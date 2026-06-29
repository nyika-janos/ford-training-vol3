from __future__ import annotations

import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.utils.state import State
from airflow.utils.trigger_rule import TriggerRule

try:
    from airflow.sdk import Variable
except ImportError:
    from airflow.models import Variable

try:
    from airflow.providers.standard.operators.python import PythonOperator
except ImportError:
    from airflow.operators.python import PythonOperator


DATAFORM_API_ROOT = "https://dataform.googleapis.com/v1beta1"
DATAFORM_TERMINAL_STATES = {"SUCCEEDED", "FAILED", "CANCELLED"}


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


def dataform_repository_path() -> str:
    project_id = airflow_var("project_id")
    location = airflow_var("dataform_location", "europe-west4")
    repository = airflow_var("dataform_repository")
    return f"projects/{project_id}/locations/{location}/repositories/{repository}"


def authorized_session():
    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return AuthorizedSession(credentials)


def validate_dataform_service_account() -> str:
    service_account = airflow_var("dataform_service_account")
    if service_account.endswith("@gcp-sa-dataform.iam.gserviceaccount.com"):
        raise AirflowException(
            "The default Dataform service agent cannot be used to run workflows "
            "in strict act-as mode. Set dataform_service_account to a custom "
            "service account, for example "
            "dataform-runner@<PROJECT_ID>.iam.gserviceaccount.com."
        )
    return service_account


def start_pipeline(**context):
    print("PIPELINE START")
    print(f"DAG run: {context['run_id']}")
    sleep_for_demo("start_pipeline")


def create_dataform_compilation_result(**context):
    session = authorized_session()
    repository_path = dataform_repository_path()
    git_commitish = airflow_var("dataform_git_commitish", "main", required=False)
    workspace = airflow_var("dataform_workspace", "", required=False)

    payload = {"gitCommitish": git_commitish}
    if workspace:
        if workspace.startswith("projects/"):
            payload = {"workspace": workspace}
        else:
            payload = {"workspace": f"{repository_path}/workspaces/{workspace}"}

    response = session.post(
        f"{DATAFORM_API_ROOT}/{repository_path}/compilationResults",
        json=payload,
        timeout=120,
    )
    if response.status_code >= 400:
        raise AirflowException(
            f"Dataform compilation result creation failed: "
            f"HTTP {response.status_code} - {response.text}"
        )

    result = response.json()
    if "name" not in result:
        raise AirflowException(f"Dataform compilation response has no name: {result}")

    sleep_for_demo("create_dataform_compilation_result")
    return result


def create_dataform_workflow_invocation(**context):
    session = authorized_session()
    repository_path = dataform_repository_path()
    compilation_result = context["ti"].xcom_pull(
        task_ids="create_dataform_compilation_result"
    )
    service_account = validate_dataform_service_account()

    payload = {
        "compilationResult": compilation_result["name"],
        "invocationConfig": {
            "serviceAccount": service_account,
        },
    }

    response = session.post(
        f"{DATAFORM_API_ROOT}/{repository_path}/workflowInvocations",
        json=payload,
        timeout=120,
    )
    if response.status_code >= 400:
        raise AirflowException(
            f"Dataform workflow invocation creation failed: "
            f"HTTP {response.status_code} - {response.text}"
        )

    result = response.json()
    if "name" not in result:
        raise AirflowException(f"Dataform workflow invocation response has no name: {result}")

    sleep_for_demo("create_dataform_workflow_invocation")
    return result


def wait_for_dataform_workflow_invocation(**context):
    session = authorized_session()
    invocation = context["ti"].xcom_pull(task_ids="create_dataform_workflow_invocation")
    invocation_name = invocation["name"]
    timeout_seconds = int(airflow_var("dataform_wait_timeout_seconds", "900", required=False))
    poll_seconds = int(airflow_var("dataform_poll_seconds", "15", required=False))
    deadline = time.monotonic() + timeout_seconds

    while True:
        response = session.get(
            f"{DATAFORM_API_ROOT}/{invocation_name}",
            timeout=120,
        )
        if response.status_code >= 400:
            raise AirflowException(
                f"Dataform workflow invocation lookup failed: "
                f"HTTP {response.status_code} - {response.text}"
            )

        result = response.json()
        state = result.get("state")
        if state in DATAFORM_TERMINAL_STATES:
            if state != "SUCCEEDED":
                raise AirflowException(
                    f"Dataform workflow invocation finished with state {state}: {result}"
                )
            return result

        if time.monotonic() > deadline:
            raise AirflowException(
                f"Timed out while waiting for Dataform workflow invocation: {invocation_name}"
            )

        time.sleep(poll_seconds)


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
        raise AirflowException(f"{table_id} is empty after Dataform run.")

    sleep_for_demo("check_sales_gold")
    return {"table_id": table_id, "row_count": row_count}


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


def trigger_cloud_run_exporter(**context):
    import requests

    exporter_url = airflow_var("cloud_run_exporter_url")
    gold_dataset = airflow_var("gold_dataset")
    gold_table = airflow_var("gold_table", "sales_gold")
    bucket_name = airflow_var("bucket_name")
    export_prefix = airflow_var("export_prefix", "export/")

    logical_date = context["logical_date"].strftime("%Y%m%dT%H%M%S")
    payload = {
        "requested_by": "airflow-notification-pipeline",
        "gold_dataset": gold_dataset,
        "gold_table": gold_table,
        "bucket_name": bucket_name,
        "export_prefix": export_prefix,
        "export_name": f"sales_gold_notification_pipeline_{logical_date}.xlsx",
    }

    sleep_for_demo("trigger_cloud_run_exporter")

    response = requests.post(
        exporter_url,
        json=payload,
        headers=exporter_headers(exporter_url),
        timeout=300,
    )
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

    sleep_for_demo("verify_export_file")
    return {"export_uri": export_uri, "size_bytes": blob.size}


def success_notification(**context):
    export_check = context["ti"].xcom_pull(task_ids="verify_export_file")
    print("PIPELINE SUCCESS")
    print(f"DAG: {context['dag'].dag_id}")
    print(f"Run ID: {context['run_id']}")
    print(f"Export URI: {export_check['export_uri']}")
    print(f"Size bytes: {export_check['size_bytes']}")


def failure_notification(**context):
    dag_run = context["dag_run"]
    failed_tasks = [
        task.task_id
        for task in dag_run.get_task_instances()
        if task.state == State.FAILED
    ]

    print("PIPELINE FAILED")
    print(f"DAG: {context['dag'].dag_id}")
    print(f"Run ID: {context['run_id']}")
    print(f"Failed tasks: {failed_tasks}")


default_args = {
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


with DAG(
    dag_id="pipeline_with_notifications_dag",
    description="Run the Dataform-to-export pipeline and emit success or failure notifications.",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["training", "gcp", "notifications"],
) as dag:

    start = PythonOperator(
        task_id="start_pipeline",
        python_callable=start_pipeline,
    )

    create_compilation = PythonOperator(
        task_id="create_dataform_compilation_result",
        python_callable=create_dataform_compilation_result,
    )

    create_invocation = PythonOperator(
        task_id="create_dataform_workflow_invocation",
        python_callable=create_dataform_workflow_invocation,
    )

    wait_for_invocation = PythonOperator(
        task_id="wait_for_dataform_workflow_invocation",
        python_callable=wait_for_dataform_workflow_invocation,
    )

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

    notify_success = PythonOperator(
        task_id="success_notification",
        python_callable=success_notification,
    )

    notify_failure = PythonOperator(
        task_id="failure_notification",
        python_callable=failure_notification,
        trigger_rule=TriggerRule.ONE_FAILED,
    )

    pipeline_tasks = [
        start,
        create_compilation,
        create_invocation,
        wait_for_invocation,
        check_gold,
        trigger_exporter,
        verify_export,
    ]

    start >> create_compilation >> create_invocation >> wait_for_invocation
    wait_for_invocation >> check_gold >> trigger_exporter >> verify_export >> notify_success
    pipeline_tasks >> notify_failure
