from __future__ import annotations

from collections import Counter

from hello_world_common import (
    conformed_local_path,
    curated_local_path,
    load_job_config,
    load_json,
    maybe_download_json,
    maybe_upload_json,
    write_json,
)


def load_conformed_payload(config: dict) -> dict:
    local_path = conformed_local_path()
    if local_path.is_file():
        payload = load_json(local_path)
        if not isinstance(payload, dict):
            raise ValueError(f"conformed hello world payload must be a JSON object: {local_path}")
        return payload

    payload = maybe_download_json(config["conformed_bucket"], config["conformed_key"])
    if isinstance(payload, dict):
        return payload

    raise FileNotFoundError(
        "hello world conformed payload not found in local mirror or object storage; "
        f"expected local file {local_path}"
    )


def run() -> dict:
    config = load_job_config()
    conformed_payload = load_conformed_payload(config)
    records = conformed_payload.get("records")

    if not isinstance(records, list) or not records:
        raise ValueError("conformed hello world payload must contain a non-empty records list")

    dates = [str(record["date"]) for record in records]
    amounts = [int(record["amount"]) for record in records]
    category_counts = Counter(str(record["category"]) for record in records)

    summary = {
        "job_name": config["job_name"],
        "run_date": config["run_date"],
        "record_count": len(records),
        "total_amount": sum(amounts),
        "category_counts": dict(sorted(category_counts.items())),
        "minimum_date": min(dates),
        "maximum_date": max(dates),
        "raw_object": {
            "bucket": config["raw_bucket"],
            "key": config["raw_key"],
        },
        "conformed_object": {
            "bucket": config["conformed_bucket"],
            "key": config["conformed_key"],
        },
        "curated_object": {
            "bucket": config["curated_bucket"],
            "key": config["curated_key"],
        },
    }

    output_path = curated_local_path()
    write_json(output_path, summary)
    maybe_upload_json(config["curated_bucket"], config["curated_key"], summary)

    print(f"wrote curated hello world summary to {output_path}")
    return summary


if __name__ == "__main__":
    run()
