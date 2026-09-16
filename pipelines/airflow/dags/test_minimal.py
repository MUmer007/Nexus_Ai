from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG('test_minimal', start_date=datetime(2026, 1, 1), schedule_interval='@daily') as dag:
    BashOperator(task_id='hello', bash_command='echo hello')
