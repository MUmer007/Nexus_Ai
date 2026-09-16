from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'nexus-ai',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='nexus_lakehouse_pipeline',
    default_args=default_args,
    description='End-to-end lakehouse pipeline: Bronze -> Silver Iceberg -> dbt Gold',
    schedule=None,  # Manual trigger for demo
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['lakehouse', 'production', 'nexus'],
) as dag:

    # NOTE: In production, these would be KubernetesPodOperators or EMR step operators
    # to isolate heavy Spark workloads from the Airflow scheduler.
    
    bronze_ingest = BashOperator(
        task_id='bronze_ingest',
        bash_command='echo "Triggering Bronze Ingestion (PostgreSQL -> Parquet)..." && cd /opt/airflow/ingestion && python bronze_ingest.py',
    )

    silver_ingest = BashOperator(
        task_id='silver_iceberg_ingest',
        bash_command='echo "Triggering Silver Iceberg (Dedup, Standardize, Iceberg Table)..." && cd /opt/airflow/ingestion && python silver_iceberg_ingest.py',
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='echo "Building Gold Marts with dbt..." && cd /opt/airflow/dbt/nexus_gold && dbt run',
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='echo "Running Data Quality Tests..." && cd /opt/airflow/dbt/nexus_gold && dbt test',
    )

    # Define linear dependencies
    bronze_ingest >> silver_ingest >> dbt_run >> dbt_test
