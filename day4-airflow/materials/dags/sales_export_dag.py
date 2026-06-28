from __future__ import annotations

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


def trigger_cloud_run_exporter(**context):
    import requests

    exporter_url = airflow_var("cloud_run_exporter_url")
    gold_dataset = airflow_var("gold_dataset")
    gold_table = airflow_var("gold_table", "sales_gold")
    bucket_name = airflow_var("bucket_name")
    export_prefix = airflow_var("export_prefix", "export/")
    authenticated = airflow_var("cloud_run_exporter_authenticated", "false", required=False)

    logical_date = context["logical_date"].strftime("%Y%m%dT%H%M%S")
    payload = {
        "requested_by": "airflow-local",
        "gold_dataset": gold_dataset,
        "gold_table": gold_table,
        "bucket_name": bucket_name,
        "export_prefix": export_prefix,
        "export_name": f"sales_gold_airflow_{logical_date}.xlsx",
    }

    headers = {"Content-Type": "application/json"}
    if authenticated.lower() == "true":
        import google.auth.transport.requests
        from google.oauth2 import id_token

        auth_request = google.auth.transport.requests.Request()
        token = id_token.fetch_id_token(auth_request, exporter_url)
        headers["Authorization"] = f"Bearer {token}"

    response = requests.post(exporter_url, json=payload, headers=headers, timeout=300)
    if response.status_code >= 400:
        raise AirflowException(
            f"Cloud Run exporter failed: HTTP {response.status_code} - {response.text}"
        )

    result = response.json()
    if result.get("status") != "success":
        raise AirflowException(f"Cloud Run exporter returned non-success response: {result}")

    return result


def verify_export_file(**context):
    from google.cloud import storage

    exporter_result = context["ti"].xcom_pull(task_ids="trigger_cloud_run_exporter")
    export_uri = exporter_result.get("export_uri")
    if not export_uri or not export_uri.startswith("gs://"):
        raise AirflowException(f"Invalid export_uri returned by exporter: {export_uri}")

    parsed = urlparse(export_uri)
    bucket_name = parsed.netloc
    object_name = parsed.path.lstrip("/")

    client = storage.Client(project=airflow_var("project_id"))
    blob = client.bucket(bucket_name).get_blob(object_name)
    if blob is None:
        raise AirflowException(f"Export file was not found: {export_uri}")

    if not blob.size:
        raise AirflowException(f"Export file is empty: {export_uri}")

    return {"export_uri": export_uri, "size_bytes": blob.size}


default_args = {
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


with DAG(
    dag_id="sales_export_dag",
    description="Validate BigQuery GOLD data, call the Cloud Run exporter, and verify the exported file.",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["training", "gcp", "cloud-run", "export"],
) as dag:

    check_gold = PythonOperator(
        task_id="check_sales_gold",
        python_callable=check_sales_gold,
    )

    trigger_exporter = PythonOperator(
        task_id="trigger_cloud_run_exporter",
        python_callable=trigger_cloud_run_exporter,
    )

    verify_export = PythonOperator(
        task_id="verify_export_file",
        python_callable=verify_export_file,
    )

    check_gold >> trigger_exporter >> verify_export
