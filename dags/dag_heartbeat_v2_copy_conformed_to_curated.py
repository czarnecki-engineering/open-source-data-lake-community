from datetime import datetime

import boto3
from botocore.client import Config

from airflow import DAG
from airflow.operators.python import PythonOperator


CONFORMED_BUCKET = "conformed"
CURATED_BUCKET = "curated"
PREFIX = "heartbeat_v2/"
MINIO_ENDPOINT = "http://minio:9000"


def copy_new_objects() -> None:
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        config=Config(signature_version="s3v4"),
    )

    conformed_objects = s3.list_objects_v2(Bucket=CONFORMED_BUCKET, Prefix=PREFIX).get("Contents", [])
    curated_objects = s3.list_objects_v2(Bucket=CURATED_BUCKET, Prefix=PREFIX).get("Contents", [])
    curated_keys = {obj["Key"] for obj in curated_objects}

    for obj in conformed_objects:
        key = obj["Key"]
        if key not in curated_keys:
            s3.copy_object(
                Bucket=CURATED_BUCKET,
                Key=key,
                CopySource={"Bucket": CONFORMED_BUCKET, "Key": key},
            )


with DAG(
    dag_id="heartbeat_v2_copy_conformed_to_curated",
    start_date=datetime(2024, 1, 1),
    schedule_interval="*/1 * * * *",
    catchup=False,
    tags=["overlay", "heartbeat-v2", "minio", "conformed", "curated"],
) as dag:
    PythonOperator(
        task_id="copy_new_conformed_objects",
        python_callable=copy_new_objects,
    )
