from __future__ import annotations

import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

from airflow import DAG
from airflow.exceptions import AirflowException

try:
    from airflow.sdk import Param, Variable
except ImportError:
    from airflow.models import Variable
    from airflow.models.param import Param

try:
    from airflow.providers.standard.operators.python import BranchPythonOperator, PythonOperator
except ImportError:
    from airflow.operators.python import BranchPythonOperator, PythonOperator


DATAFORM_API_ROOT = "https://dataform.googleapis.com/v1beta1"
DATAFORM_TERMINAL_STATES = {"SUCCEEDED", "FAILED", "CANCELLED"}
VALID_PIPELINE_MODES = {"quick", "full"}


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


def selected_pipeline_mode(**context) -> str:
    mode = context["params"].get("pipeline_mode")
    if isinstance(mode, str):
        mode = mode.strip().lower()

    if mode not in VALID_PIPELINE_MODES:
        raise AirflowException(
            "Missing or invalid required trigger parameter: pipeline_mode. "
            "Use one of: quick, full."
        )

    return mode


def choose_pipeline_mode(**context):
    mode = selected_pipeline_mode(**context)
    sleep_for_demo("choose_pipeline_mode")

    if mode == "full":
        print("pipeline_mode=full: running Dataform before export.")
        return "create_dataform_compilation_result"

    print("pipeline_mode=quick: exporting the existing GOLD table.")
    return "quick_check_sales_gold"


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
        raise AirflowException(f"{table_id} is empty.")

    sleep_for_demo(context["task"].task_id)
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


def trigger_cloud_run_exporter(export_suffix: str, **context):
    import requests

    exporter_url = airflow_var("cloud_run_exporter_url")
    gold_dataset = airflow_var("gold_dataset")
    gold_table = airflow_var("gold_table", "sales_gold")
    bucket_name = airflow_var("bucket_name")
    export_prefix = airflow_var("export_prefix", "export/")

    logical_date = context["logical_date"].strftime("%Y%m%dT%H%M%S")
    payload = {
        "requested_by": "airflow-branching-pipeline-mode",
        "gold_dataset": gold_dataset,
        "gold_table": gold_table,
        "bucket_name": bucket_name,
        "export_prefix": export_prefix,
        "export_name": f"sales_gold_{export_suffix}_{logical_date}.xlsx",
    }

    sleep_for_demo(context["task"].task_id)

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


def verify_export_file(export_task_id: str, **context):
    from google.cloud import storage

    exporter_result = context["ti"].xcom_pull(task_ids=export_task_id)
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

    sleep_for_demo(context["task"].task_id)
    return {"export_uri": export_uri, "size_bytes": blob.size}


def branch_done(label: str, export_check_task_id: str, **context):
    export_check = context["ti"].xcom_pull(task_ids=export_check_task_id)
    print(f"{label.upper()} PIPELINE MODE DONE")
    print(f"DAG run: {context['run_id']}")
    print(f"Export URI: {export_check['export_uri']}")
    print(f"Size bytes: {export_check['size_bytes']}")


default_args = {
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


with DAG(
    dag_id="branching_pipeline_mode_dag",
    description="Choose quick export or full Dataform-to-export path from a required trigger parameter.",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    params={
        "pipeline_mode": Param(
            "quick",
            enum=["quick", "full"],
            description="Required at trigger time. quick = export existing GOLD table, full = run Dataform first.",
        ),
    },
    tags=["training", "gcp", "branching", "params"],
) as dag:

    choose_mode = BranchPythonOperator(
        task_id="choose_pipeline_mode",
        python_callable=choose_pipeline_mode,
    )

    quick_check_gold = PythonOperator(
        task_id="quick_check_sales_gold",
        python_callable=check_sales_gold,
    )

    quick_export = PythonOperator(
        task_id="quick_export_all_markets",
        python_callable=trigger_cloud_run_exporter,
        op_kwargs={"export_suffix": "quick"},
    )

    quick_verify = PythonOperator(
        task_id="quick_verify_export_file",
        python_callable=verify_export_file,
        op_kwargs={"export_task_id": "quick_export_all_markets"},
    )

    quick_done = PythonOperator(
        task_id="quick_pipeline_done",
        python_callable=branch_done,
        op_kwargs={
            "label": "quick",
            "export_check_task_id": "quick_verify_export_file",
        },
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

    full_check_gold = PythonOperator(
        task_id="full_check_sales_gold",
        python_callable=check_sales_gold,
    )

    full_export = PythonOperator(
        task_id="full_export_all_markets",
        python_callable=trigger_cloud_run_exporter,
        op_kwargs={"export_suffix": "full"},
    )

    full_verify = PythonOperator(
        task_id="full_verify_export_file",
        python_callable=verify_export_file,
        op_kwargs={"export_task_id": "full_export_all_markets"},
    )

    full_done = PythonOperator(
        task_id="full_pipeline_done",
        python_callable=branch_done,
        op_kwargs={
            "label": "full",
            "export_check_task_id": "full_verify_export_file",
        },
    )

    choose_mode >> quick_check_gold >> quick_export >> quick_verify >> quick_done
    (
        choose_mode
        >> create_compilation
        >> create_invocation
        >> wait_for_invocation
        >> full_check_gold
        >> full_export
        >> full_verify
        >> full_done
    )
