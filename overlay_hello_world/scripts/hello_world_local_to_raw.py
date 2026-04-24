from __future__ import annotations

from hello_world_common import (
    load_job_config,
    load_json,
    maybe_upload_json,
    raw_local_path,
    require_sample_input_path,
    write_json,
)


def run() -> dict:
    config = load_job_config()
    sample_path = require_sample_input_path()
    payload = load_json(sample_path)
    records = payload.get("records")

    if not isinstance(records, list) or not records:
        raise ValueError(f"hello world sample input must contain a non-empty records list: {sample_path}")

    raw_payload = {
        "job_name": config["job_name"],
        "run_date": config["run_date"],
        "source_file": str(sample_path),
        "record_count": len(records),
        "records": records,
    }

    output_path = raw_local_path()
    write_json(output_path, raw_payload)
    maybe_upload_json(config["raw_bucket"], config["raw_key"], raw_payload)

    print(f"wrote raw hello world payload to {output_path}")
    return raw_payload


if __name__ == "__main__":
    run()
