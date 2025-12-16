from datetime import datetime
import os

import boto3
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator


def write_time_to_raw() -> None:
    s3 = boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://minio:9000"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )

    now = datetime.now(pendulum.timezone("Australia/Melbourne"))
    body = now.strftime("%Y-%m-%d %H:%M:%S %Z\n").encode()

    key = f"heartbeat/airflow_time_{now.strftime('%Y%m%d_%H%M%S')}.txt"
    s3.put_object(Bucket="raw", Key=key, Body=body)


with DAG(
    dag_id="heartbeat_1m_to_raw",
    start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),
    schedule="* * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["raw", "minio"],
) as dag:
    PythonOperator(
        task_id="write_time_to_raw",
        python_callable=write_time_to_raw,
    )
