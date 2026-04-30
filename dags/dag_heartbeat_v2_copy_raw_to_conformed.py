from datetime import datetime

import boto3
from botocore.client import Config

from airflow import DAG
from airflow.operators.python import PythonOperator


RAW_BUCKET = "raw"
CONFORMED_BUCKET = "conformed"
PREFIX = "heartbeat_v2/"
MINIO_ENDPOINT = "http://minio:9000"


def copy_new_objects() -> None:
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        config=Config(signature_version="s3v4"),
    )

    raw_objects = s3.list_objects_v2(Bucket=RAW_BUCKET, Prefix=PREFIX).get("Contents", [])
    conformed_objects = s3.list_objects_v2(Bucket=CONFORMED_BUCKET, Prefix=PREFIX).get("Contents", [])
    conformed_keys = {obj["Key"] for obj in conformed_objects}

    for obj in raw_objects:
        key = obj["Key"]
        if key not in conformed_keys:
            s3.copy_object(
                Bucket=CONFORMED_BUCKET,
                Key=key,
                CopySource={"Bucket": RAW_BUCKET, "Key": key},
            )


default_args = {
    "owner": "airflow",
    "retries": 0,
}


with DAG(
    dag_id="heartbeat_v2_copy_raw_to_conformed",
    start_date=datetime(2024, 1, 1),
    schedule_interval="*/1 * * * *",
    catchup=False,
    default_args=default_args,
    tags=["overlay", "heartbeat-v2", "minio", "raw", "conformed"],
) as dag:
    PythonOperator(
        task_id="copy_new_raw_objects",
        python_callable=copy_new_objects,
    )
