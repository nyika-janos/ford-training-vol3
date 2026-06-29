from __future__ import annotations

import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

from airflow import DAG
from airflow.exceptions import AirflowException

try:
    from airflow.sdk import Variable
except ImportError:
    from airflow.models import Variable

try:
    from airflow.providers.standard.operators.python import PythonOperator
except ImportError:
    from airflow.operators.python import PythonOperator


MARKET_EXPORTS = [
    {"task_id": "export_market_hu", "market": "HU", "export_suffix": "hu"},
    {"task_id": "export_market_cz", "market": "CZ", "export_suffix": "cz"},
    {"task_id": "export_market_sk", "market": "SK", "export_suffix": "sk"},
    {"task_id": "export_all_markets", "market": None, "export_suffix": "all"},
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
        print(f"{label}: sleeping for {delay_seconds} seconds so the graph is visible.")
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

    return {"table_id": table_id, "row_count": row_count}


def prepare_export_requests(**context):
    logical_date = context["logical_date"].strftime("%Y%m%dT%H%M%S")
    requests = {}

    for export in MARKET_EXPORTS:
        export_name = f"sales_gold_{export['export_suffix']}_{logical_date}.xlsx"
        payload = {
            "requested_by": "airflow-parallel-market-exports",
            "export_name": export_name,
        }
        if export["market"]:
            payload["market"] = export["market"]
        requests[export["task_id"]] = payload

    sleep_for_demo("prepare_export_requests")
    return requests


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


def trigger_market_export(export_task_id: str, **context):
    import requests

    exporter_url = airflow_var("cloud_run_exporter_url")
    gold_dataset = airflow_var("gold_dataset")
    gold_table = airflow_var("gold_table", "sales_gold")
    bucket_name = airflow_var("bucket_name")
    export_prefix = airflow_var("export_prefix", "export/")

    prepared_requests = context["ti"].xcom_pull(task_ids="prepare_export_requests")
    payload = dict(prepared_requests[export_task_id])
    payload.update(
        {
            "gold_dataset": gold_dataset,
            "gold_table": gold_table,
            "bucket_name": bucket_name,
            "export_prefix": export_prefix,
        }
    )

    sleep_for_demo(export_task_id)

    response = requests.post(
        exporter_url,
        json=payload,
        headers=exporter_headers(exporter_url),
        timeout=300,
    )
    if response.status_code >= 400:
        raise AirflowException(
            f"Cloud Run exporter failed for {export_task_id}: "
            f"HTTP {response.status_code} - {response.text}"
        )

    result = response.json()
    if result.get("status") != "success":
        raise AirflowException(
            f"Cloud Run exporter returned non-success for {export_task_id}: {result}"
        )

    return result


def collect_export_results(**context):
    results = {}
    for export in MARKET_EXPORTS:
        task_id = export["task_id"]
        result = context["ti"].xcom_pull(task_ids=task_id)
        if not result:
            raise AirflowException(f"No XCom result found for {task_id}.")
        if result.get("status") != "success":
            raise AirflowException(f"Export task {task_id} did not return success: {result}")
        results[task_id] = result

    return results


def verify_all_export_files(**context):
    from google.cloud import storage

    results = context["ti"].xcom_pull(task_ids="collect_export_results")
    client = storage.Client(project=airflow_var("project_id"))
    verified = {}

    for task_id, result in results.items():
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

    sleep_for_demo("verify_all_export_files")
    return verified


def final_success_notification(**context):
    verified = context["ti"].xcom_pull(task_ids="verify_all_export_files")
    print("PARALLEL MARKET EXPORTS SUCCESS")
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
    dag_id="parallel_market_exports_dag",
    description="Run multiple Cloud Run exporter requests in parallel and join them before verification.",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["training", "gcp", "cloud-run", "parallel"],
) as dag:

    check_gold = PythonOperator(
        task_id="check_sales_gold",
        python_callable=check_sales_gold,
    )

    prepare_requests = PythonOperator(
        task_id="prepare_export_requests",
        python_callable=prepare_export_requests,
    )

    export_tasks = []
    for export in MARKET_EXPORTS:
        export_tasks.append(
            PythonOperator(
                task_id=export["task_id"],
                python_callable=trigger_market_export,
                op_kwargs={"export_task_id": export["task_id"]},
            )
        )

    collect_results = PythonOperator(
        task_id="collect_export_results",
        python_callable=collect_export_results,
    )

    verify_exports = PythonOperator(
        task_id="verify_all_export_files",
        python_callable=verify_all_export_files,
    )

    notify_success = PythonOperator(
        task_id="final_success_notification",
        python_callable=final_success_notification,
    )

    check_gold >> prepare_requests >> export_tasks >> collect_results >> verify_exports >> notify_success
