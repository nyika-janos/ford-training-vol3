from __future__ import annotations

import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.utils.trigger_rule import TriggerRule

try:
    from airflow.sdk import Variable
except ImportError:
    from airflow.models import Variable

try:
    from airflow.providers.standard.operators.empty import EmptyOperator
    from airflow.providers.standard.operators.python import BranchPythonOperator, PythonOperator
except ImportError:
    from airflow.operators.empty import EmptyOperator
    from airflow.operators.python import BranchPythonOperator, PythonOperator


MARKET_EXPORTS = [
    {"task_id": "export_market_hu", "market": "HU", "export_suffix": "hu"},
    {"task_id": "export_market_cz", "market": "CZ", "export_suffix": "cz"},
    {"task_id": "export_market_sk", "market": "SK", "export_suffix": "sk"},
]


def airflow_var(name: str, default: str | None = None, required: bool = True) -> str:
    try:
        value = Variable.get(name, default=default)
    except TypeError:
        value = Variable.get(name, default_var=default)

    if isinstance(value, str):
        value = value.strip()

    if required and not value:
        raise AirflowException(f"Missing required Airflow Variable: {name}")
    return value


def sleep_for_demo(label: str):
    delay_seconds = int(airflow_var("demo_task_delay_seconds", "3", required=False))
    if delay_seconds > 0:
        print(f"{label}: sleeping for {delay_seconds} seconds so the branch is visible.")
        time.sleep(delay_seconds)


def check_sales_gold(**context):
    from google.cloud import bigquery

    project_id = airflow_var("project_id")
    gold_dataset = airflow_var("gold_dataset")
    gold_table = airflow_var("gold_table", "sales_gold")

    table_id = f"{project_id}.{gold_dataset}.{gold_table}"
    client = bigquery.Client(project=project_id)
    query = f"SELECT COUNT(*) AS row_count FROM `{table_id}`"
    row = next(iter(client.query(query).result()))
    row_count = row["row_count"]

    if row_count == 0:
        raise AirflowException(f"{table_id} is empty.")

    print(f"{table_id} row count: {row_count}")
    return {"table_id": table_id, "row_count": row_count}


def choose_export_strategy(**context):
    gold_check = context["ti"].xcom_pull(task_ids="check_sales_gold")
    row_count = int(gold_check["row_count"])
    threshold = int(airflow_var("branching_export_row_threshold", "100", required=False))

    sleep_for_demo("choose_export_strategy")

    if row_count > threshold:
        print(
            f"Row count is {row_count}, threshold is {threshold}. "
            "Using market-level sequential exports."
        )
        return "export_market_hu"

    print(
        f"Row count is {row_count}, threshold is {threshold}. "
        "Using one all-markets export."
    )
    return "export_all_markets"


def exporter_headers(exporter_url: str):
    headers = {"Content-Type": "application/json"}
    authenticated = airflow_var("cloud_run_exporter_authenticated", "false", required=False)

    if authenticated.lower() == "true":
        import google.auth.transport.requests
        from google.oauth2 import id_token

        auth_request = google.auth.transport.requests.Request()
        token = id_token.fetch_id_token(auth_request, exporter_url)
        headers["Authorization"] = f"Bearer {token}"

    return headers


def trigger_export(export_suffix: str, market: str | None = None, **context):
    import requests

    exporter_url = airflow_var("cloud_run_exporter_url")
    gold_dataset = airflow_var("gold_dataset")
    gold_table = airflow_var("gold_table", "sales_gold")
    bucket_name = airflow_var("bucket_name")
    export_prefix = airflow_var("export_prefix", "export/")

    logical_date = context["logical_date"].strftime("%Y%m%dT%H%M%S")
    payload = {
        "requested_by": "airflow-branching-market-export",
        "gold_dataset": gold_dataset,
        "gold_table": gold_table,
        "bucket_name": bucket_name,
        "export_prefix": export_prefix,
        "export_name": f"sales_gold_branching_{export_suffix}_{logical_date}.xlsx",
    }
    if market:
        payload["market"] = market

    sleep_for_demo(f"export_{export_suffix}")

    response = requests.post(
        exporter_url,
        json=payload,
        headers=exporter_headers(exporter_url),
        timeout=300,
    )
    if response.status_code >= 400:
        raise AirflowException(
            f"Cloud Run exporter failed for {export_suffix}: "
            f"HTTP {response.status_code} - {response.text}"
        )

    result = response.json()
    if result.get("status") != "success":
        raise AirflowException(
            f"Cloud Run exporter returned non-success for {export_suffix}: {result}"
        )

    return result


def verify_selected_exports(**context):
    from google.cloud import storage

    task_ids = ["export_all_markets"] + [export["task_id"] for export in MARKET_EXPORTS]
    client = storage.Client(project=airflow_var("project_id"))
    verified = {}

    for task_id in task_ids:
        result = context["ti"].xcom_pull(task_ids=task_id)
        if not result:
            print(f"{task_id}: skipped by branch decision.")
            continue

        export_uri = result.get("export_uri")
        if not export_uri or not export_uri.startswith("gs://"):
            raise AirflowException(f"Invalid export_uri from {task_id}: {export_uri}")

        parsed = urlparse(export_uri)
        bucket_name = parsed.netloc
        object_name = parsed.path.lstrip("/")
        blob = client.bucket(bucket_name).get_blob(object_name)

        if blob is None:
            raise AirflowException(f"Export file was not found for {task_id}: {export_uri}")
        if not blob.size:
            raise AirflowException(f"Export file is empty for {task_id}: {export_uri}")

        verified[task_id] = {
            "export_uri": export_uri,
            "size_bytes": blob.size,
            "row_count": result.get("row_count"),
        }

    if not verified:
        raise AirflowException("No export result was produced by the selected branch.")

    sleep_for_demo("verify_selected_exports")
    return verified


def final_branching_notification(**context):
    verified = context["ti"].xcom_pull(task_ids="verify_selected_exports")
    print("BRANCHING MARKET EXPORT SUCCESS")
    print(f"DAG run: {context['run_id']}")
    for task_id, info in verified.items():
        print(
            f"{task_id}: {info['export_uri']} "
            f"({info['size_bytes']} bytes, rows={info.get('row_count')})"
        )


default_args = {
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


with DAG(
    dag_id="branching_market_export_dag",
    description="Choose all-markets or market-by-market export path based on GOLD row count.",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["training", "gcp", "cloud-run", "branching"],
) as dag:

    check_gold = PythonOperator(
        task_id="check_sales_gold",
        python_callable=check_sales_gold,
    )

    choose_strategy = BranchPythonOperator(
        task_id="choose_export_strategy",
        python_callable=choose_export_strategy,
    )

    export_all_markets = PythonOperator(
        task_id="export_all_markets",
        python_callable=trigger_export,
        op_kwargs={"export_suffix": "all", "market": None},
    )

    export_market_hu = PythonOperator(
        task_id="export_market_hu",
        python_callable=trigger_export,
        op_kwargs={"export_suffix": "hu", "market": "HU"},
    )

    export_market_cz = PythonOperator(
        task_id="export_market_cz",
        python_callable=trigger_export,
        op_kwargs={"export_suffix": "cz", "market": "CZ"},
    )

    export_market_sk = PythonOperator(
        task_id="export_market_sk",
        python_callable=trigger_export,
        op_kwargs={"export_suffix": "sk", "market": "SK"},
    )

    join_selected_branch = EmptyOperator(
        task_id="join_selected_branch",
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    verify_exports = PythonOperator(
        task_id="verify_selected_exports",
        python_callable=verify_selected_exports,
    )

    notify_success = PythonOperator(
        task_id="final_branching_notification",
        python_callable=final_branching_notification,
    )

    check_gold >> choose_strategy
    choose_strategy >> export_all_markets >> join_selected_branch
    choose_strategy >> export_market_hu >> export_market_cz >> export_market_sk >> join_selected_branch
    join_selected_branch >> verify_exports >> notify_success
