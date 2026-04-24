from __future__ import annotations

from hello_world_common import (
    conformed_local_path,
    load_job_config,
    load_json,
    maybe_download_json,
    maybe_upload_json,
    raw_local_path,
    write_json,
)


def load_raw_payload(config: dict) -> dict:
    local_path = raw_local_path()
    if local_path.is_file():
        payload = load_json(local_path)
        if not isinstance(payload, dict):
            raise ValueError(f"raw hello world payload must be a JSON object: {local_path}")
        return payload

    payload = maybe_download_json(config["raw_bucket"], config["raw_key"])
    if isinstance(payload, dict):
        return payload

    raise FileNotFoundError(
        "hello world raw payload not found in local mirror or object storage; "
        f"expected local file {local_path}"
    )


def run() -> dict:
    config = load_job_config()
    raw_payload = load_raw_payload(config)
    records = raw_payload.get("records")

    if not isinstance(records, list) or not records:
        raise ValueError("raw hello world payload must contain a non-empty records list")

    normalised = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("hello world records must be JSON objects")

        normalised.append(
            {
                "record_id": str(record["record_id"]),
                "date": str(record["date"]),
                "category": str(record["category"]).strip().lower(),
                "amount": int(record["amount"]),
            }
        )

    normalised.sort(key=lambda item: (item["date"], item["record_id"]))

    conformed_payload = {
        "job_name": config["job_name"],
        "run_date": config["run_date"],
        "record_count": len(normalised),
        "records": normalised,
    }

    output_path = conformed_local_path()
    write_json(output_path, conformed_payload)
    maybe_upload_json(config["conformed_bucket"], config["conformed_key"], conformed_payload)

    print(f"wrote conformed hello world payload to {output_path}")
    return conformed_payload


if __name__ == "__main__":
    run()
