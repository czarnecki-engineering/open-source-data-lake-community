Skip to content
Chat history




You said:
hi. 

1. we have set up a working minio object store.

2. we have a working Airflow.

3. there is a scheduled DAG which is creating a heartbeat file every minute in the raw/ bucket

i would like to extend this to 

4. run a second DAG that opens new files in the raw/ bucket and copies them to the conformed/ bucket

is this possible?

is there an existin property of a new file in raw that can be used to trigger a DAG to copy the file to conformed/ ?

just the investigation and answers please.
ChatGPT said:
Yes—this is entirely possible. The key distinction is what Airflow can natively “sense” versus what requires polling or event integration.

Below is a concise investigation and direct answers.

1. Can a second DAG copy new objects from raw/ to conformed/?
Yes.
A second DAG can:

List objects in raw/

Identify objects not yet present in conformed/ (or not yet processed)

Copy them to conformed/

This is a standard Airflow pattern.

2. Can a “new file in MinIO” directly trigger a DAG?
No, not natively.

Airflow does not support event-driven triggers from S3-compatible object stores (including MinIO) out of the box.

Airflow DAGs are:

Time-based

Externally triggered via API

Polling-based via Sensors

There is no built-in “object created” event hook for MinIO.

3. Does a MinIO object have a property that indicates “newness”?
Yes—but Airflow cannot subscribe to it automatically.

Relevant object metadata:

LastModified

ETag

Object key (path)

Size

These can be queried, not pushed.

4. Practical patterns to detect “new files”
Pattern A — Polling with a Sensor (most common)
Use a sensor to:

List objects in raw/

Compare against a stored state (e.g. processed keys)

Typical approaches:

Compare raw/ vs conformed/

Maintain a manifest (DynamoDB / Postgres / Airflow Variable)

Track LastModified > last_run_time

This is the recommended Airflow-native approach.

Pattern B — Time-based DAG with idempotent logic
Schedule the second DAG every minute (or 5 minutes):

List all objects in raw/

For each object:

If not present in conformed/, copy it

Otherwise skip

This avoids sensors entirely and is very robust.

Pattern C — External event → Airflow REST trigger (advanced)
MinIO does support:

Bucket notifications (Webhook, NATS, Kafka, etc.)

You could:

Configure MinIO to send a webhook on ObjectCreated

That webhook calls:

POST /api/v1/dags/{dag_id}/dagRuns
Airflow triggers the DAG immediately

This works—but adds infrastructure complexity and is usually unnecessary unless near-real-time is required.

5. Direct answers to your questions
Q: Is this possible?
Yes. This is a standard Airflow design.

Q: Is there an existing property of a new file that can trigger a DAG?
No—not directly. MinIO object metadata exists, but Airflow cannot subscribe to it without polling or external events.

Q: What is the simplest, cleanest approach?
A time-scheduled DAG that:

Lists raw/

Copies only objects not yet present in conformed/

Is idempotent

This aligns perfectly with Airflow’s execution model.

If you want, the next step would be:

A one-task DAG using the MinIO (S3) client that performs this copy safely and minimally.

You said:
is the approach you suggest - A time-scheduled DAG - based on your '4(B)' or 4(A)
ChatGPT said:
The approach I am recommending is 4(B).

To be explicit:

4(B) — Time-based DAG with idempotent logic is the primary recommendation.

4(A) — Polling with a Sensor is optional and usually unnecessary for this use case.

Why 4(B) is preferred
Airflow is fundamentally schedule-driven, not event-driven.

A simple scheduled DAG:

Lists objects in raw/

Copies only those not already present in conformed/

Is naturally idempotent

No Sensors, no state management complexity, no long-running tasks.

Easier to reason about, debug, and operate.

When 4(A) would make sense instead
Only if:

You want the DAG run to block until at least one new object appears, and

You are comfortable with polling semantics and sensor timeouts.

In your case (continuous ingestion, minute-level cadence), 4(B) is the cleanest and most correct Airflow pattern.

If you want to proceed next, the implementation is typically a single PythonOperator with a small loop—no sensors required.

You said:
please let me have the code as pe your recommendation, so i can install into my dags/ folder
ChatGPT said:
Below is a minimal, production-safe DAG implementing 4(B): time-scheduled, idempotent copy.

Assumptions (aligned with your setup):

MinIO is S3-compatible

Airflow already has credentials configured (env vars or connection)

Buckets exist: raw, conformed

Copy is key-preserving (raw/foo.txt → conformed/foo.txt)

raw_to_conformed_copy.py
Place this file directly into your dags/ folder.

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

import boto3
from botocore.client import Config


RAW_BUCKET = "raw"
CONFORMED_BUCKET = "conformed"
MINIO_ENDPOINT = "http://minio:9000"  # adjust if required


def copy_new_objects():
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        config=Config(signature_version="s3v4"),
    )

    raw_objects = s3.list_objects_v2(Bucket=RAW_BUCKET).get("Contents", [])
    conformed_objects = s3.list_objects_v2(Bucket=CONFORMED_BUCKET).get("Contents", [])

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
    dag_id="raw_to_conformed_copy",
    start_date=datetime(2024, 1, 1),
    schedule_interval="*/1 * * * *",  # every minute
    catchup=False,
    default_args=default_args,
    tags=["minio", "raw", "conformed"],
) as dag:

    copy_task = PythonOperator(
        task_id="copy_new_raw_objects",
        python_callable=copy_new_objects,
    )
Key properties (by design)
No sensors

Idempotent (safe to rerun)

Stateless (derives truth from buckets)

Short-running

Aligned with Airflow execution model

Operational notes (important but brief)
Scheduling is fully automatic once the file is in dags/

No manual triggers required

If a file already exists in conformed/, it is skipped

Works cleanly with your existing heartbeat DAG

If you want next:

Prefix filtering (raw/heartbeat/, etc.)

Atomic “move” semantics

Object versioning awareness

Per-run logging of copied keys

Say the word and keep it minimal.

You said:
please could you write the code for a similar dag to copy from conformed/ to curated/
ChatGPT said:
Below is the direct analogue of the previous DAG, with only the minimum necessary changes.

You can drop this straight into your dags/ folder.

conformed_to_curated_copy.py
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

import boto3
from botocore.client import Config


CONFORMED_BUCKET = "conformed"
CURATED_BUCKET = "curated"
MINIO_ENDPOINT = "http://minio:9000"  # adjust if required


def copy_new_objects():
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        config=Config(signature_version="s3v4"),
    )

    conformed_objects = s3.list_objects_v2(Bucket=CONFORMED_BUCKET).get("Contents", [])
    curated_objects = s3.list_objects_v2(Bucket=CURATED_BUCKET).get("Contents", [])

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
    dag_id="conformed_to_curated_copy",
    start_date=datetime(2024, 1, 1),
    schedule_interval="*/1 * * * *",  # every minute
    catchup=False,
    tags=["minio", "conformed", "curated"],
) as dag:

    copy_task = PythonOperator(
        task_id="copy_new_conformed_objects",
        python_callable=copy_new_objects,
    )
What this gives you
Same time-based, idempotent pattern as before

No sensors

No shared state

Safe to run every minute

Clean separation of pipeline stages:

raw → conformed → curated
This composes cleanly with your existing heartbeat and raw→conformed DAGs.

If you later want:

Prefix-based promotion

Schema/version checks

“Only promote files older than N minutes”

Promotion manifests

Those can be layered on without changing the core structure.

You said:
excellent progress. thank you. done in this tab.
ChatGPT said:
Understood. Glad this is now in a good state.

You have a clean, correct pattern in place:

MinIO as the object store

Airflow as the scheduler

Time-based, idempotent DAGs for stage promotion (raw → conformed → curated)

No sensors, no hidden state, no unnecessary complexity

This is a solid foundation and scales well as you add transformation logic later.

Close this tab with confidence.




No file chosenNo file chosen
ChatGPT can make mistakes. Check important info.
