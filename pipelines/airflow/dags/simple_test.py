from datetime import UTC, datetime

from airflow.operators.bash import BashOperator

from airflow import DAG

with DAG(
    dag_id="simple_test",
    start_date=datetime(2026, 1, 1, tzinfo=UTC),
    schedule_interval="@daily",
    catchup=False,
) as dag:
    BashOperator(task_id="hello", bash_command='echo "Airflow is working!"')
