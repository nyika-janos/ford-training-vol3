from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.exceptions import AirflowException

try:
    from airflow.sdk import Variable
except ImportError:
    from airflow.models import Variable

try:
    from airflow.providers.standard.operators.bash import BashOperator
    from airflow.providers.standard.operators.empty import EmptyOperator
    from airflow.providers.standard.operators.python import PythonOperator
except ImportError:
    from airflow.operators.bash import BashOperator
    from airflow.operators.empty import EmptyOperator
    from airflow.operators.python import PythonOperator

try:
    from airflow.providers.google.cloud.operators.bigquery import BigQueryCheckOperator
except ImportError as exc:
    raise ImportError(
        "bigquery_operator_showcase_dag requires apache-airflow-providers-google. "
        "Add it to _PIP_ADDITIONAL_REQUIREMENTS before copying this DAG."
    ) from exc


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


def print_operator_summary(**context):
    project_id = airflow_var("project_id")
    gold_dataset = airflow_var("gold_dataset")
    gold_table = airflow_var("gold_table", "sales_gold")
    print("BIGQUERY OPERATOR SHOWCASE SUCCESS")
    print(f"Checked table: {project_id}.{gold_dataset}.{gold_table}")
    print("The BigQueryCheckOperator handled the BigQuery query execution.")
    print("PythonOperator is only used here for a final human-readable summary.")


default_args = {
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

PROJECT_ID = airflow_var("project_id")
GOLD_DATASET = airflow_var("gold_dataset")
GOLD_TABLE = airflow_var("gold_table", "sales_gold")
GCP_CONN_ID = airflow_var("gcp_conn_id", "google_cloud_default")
BIGQUERY_LOCATION = airflow_var("bigquery_location", "europe-west4")
DEMO_TASK_DELAY_SECONDS = airflow_var("demo_task_delay_seconds", "3")


with DAG(
    dag_id="bigquery_operator_showcase_dag",
    description="Show a native BigQuery Airflow operator next to standard operators.",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["training", "gcp", "bigquery", "operators"],
) as dag:

    start = EmptyOperator(task_id="start")

    check_sales_gold_with_bigquery_operator = BigQueryCheckOperator(
        task_id="check_sales_gold_with_bigquery_operator",
        gcp_conn_id=GCP_CONN_ID,
        location=BIGQUERY_LOCATION,
        use_legacy_sql=False,
        sql=f"""
            SELECT COUNT(*) > 0
            FROM `{PROJECT_ID}.{GOLD_DATASET}.{GOLD_TABLE}`
        """,
    )

    visual_pause = BashOperator(
        task_id="visual_pause",
        bash_command=f"echo 'BigQuery operator finished; waiting for the demo graph...' && sleep {DEMO_TASK_DELAY_SECONDS}",
    )

    operator_summary = PythonOperator(
        task_id="operator_summary",
        python_callable=print_operator_summary,
    )

    start >> check_sales_gold_with_bigquery_operator >> visual_pause >> operator_summary
