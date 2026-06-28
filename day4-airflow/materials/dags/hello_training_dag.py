from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="hello_training_dag",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["training"],
) as dag:

    hello = BashOperator(
        task_id="hello",
        bash_command="echo 'Szia Airflow, itt a negyedik tréningnap!'",
    )

    show_date = BashOperator(
        task_id="show_date",
        bash_command="date",
    )

    hello >> show_date