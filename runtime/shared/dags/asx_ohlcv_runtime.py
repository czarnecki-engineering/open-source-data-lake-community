from __future__ import annotations

import io
import json
import logging
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib import error, request

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


LOGGER = logging.getLogger(__name__)

MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_REGION = "local-01"

RAW_BUCKET = "raw"
CONFORMED_BUCKET = "conformed"
CURATED_BUCKET = "curated"

REQUEST_CONFIG_PATH = Path("/opt/airflow/config/asx/asx_data_request.json")
DATASET_ID = "market_ohlcv_daily_v2"
EXCHANGE = "ASX"
DEFAULT_CURRENCY = "AUD"
BASE_URL = "http://lakekeeper:8181"
CATALOG_URI = f"{BASE_URL}/catalog"
WAREHOUSE_NAME = "minio-spike"
WAREHOUSE_BUCKET = "curated"
WAREHOUSE_PREFIX = "lakekeeper-spike"
NAMESPACE_NAME = "demo"
TABLE_NAME = "asx_ohlcv_summary"
TABLE_IDENTIFIER = (NAMESPACE_NAME, TABLE_NAME)
VENDORED_PACKAGES_PATH = Path("/opt/airflow/vendor")

WAREHOUSE_CREATE_PAYLOAD = {
    "warehouse-name": WAREHOUSE_NAME,
    "storage-profile": {
        "type": "s3",
        "bucket": WAREHOUSE_BUCKET,
        "key-prefix": WAREHOUSE_PREFIX,
        "endpoint": f"{MINIO_ENDPOINT}/",
        "region": MINIO_REGION,
        "path-style-access": True,
        "sts-enabled": False,
        "flavor": "s3-compat",
        "push-s3-delete-disabled": True,
        "remote-signing-enabled": False,
    },
    "storage-credential": {
        "type": "s3",
        "credential-type": "access-key",
        "access-key-id": MINIO_ACCESS_KEY,
        "secret-access-key": MINIO_SECRET_KEY,
    },
}


def _utc_iso(dt: datetime) -> str:
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_boto3() -> Any:
    import boto3  # noqa: PLC0415

    return boto3


def get_s3_client() -> Any:
    boto3 = _load_boto3()
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name=MINIO_REGION,
    )


def _load_request_config() -> dict[str, Any]:
    candidate = Path(
        os.getenv("ASX_REQUEST_CONFIG_PATH", str(REQUEST_CONFIG_PATH))
    ).expanduser().resolve()
    if not candidate.is_file():
        return {}
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"ASX request config at {candidate} was not a JSON object.")
    return payload


def _dataset_id(config: dict[str, Any]) -> str:
    value = config.get("dataset_id", DATASET_ID)
    return str(value).strip() or DATASET_ID


def _exchange(config: dict[str, Any]) -> str:
    value = config.get("exchange", EXCHANGE)
    return str(value).strip() or EXCHANGE


def _currency(config: dict[str, Any]) -> str:
    value = config.get("currency", DEFAULT_CURRENCY)
    return str(value).strip() or DEFAULT_CURRENCY


def _raw_object_key(config: dict[str, Any], ticker: str) -> str:
    return f"tabular/{_dataset_id(config)}/exchange={_exchange(config)}/ticker={ticker}.csv"


def _raw_metadata_key(config: dict[str, Any], ticker: str) -> str:
    return f"tabular/{_dataset_id(config)}/exchange={_exchange(config)}/ticker={ticker}.metadata.json"


def _conformed_object_key(config: dict[str, Any], ticker: str) -> str:
    return f"tabular/{_dataset_id(config)}/exchange={_exchange(config)}/ticker={ticker}.parquet"


def _curated_object_key(config: dict[str, Any]) -> str:
    return (
        f"tabular/{_dataset_id(config)}/exchange={_exchange(config)}/"
        "asx_ohlcv_panel_curated.parquet"
    )


def _normalise_frame(frame: pd.DataFrame, *, ticker: str, config: dict[str, Any]) -> pd.DataFrame:
    normalised = frame.copy()
    normalised.columns = [str(column).strip().lower().replace(" ", "_") for column in normalised.columns]

    if "trade_date" not in normalised.columns:
        raise RuntimeError(f"Raw CSV for ticker {ticker} did not contain trade_date.")

    normalised["dataset_id"] = normalised.get("dataset_id", _dataset_id(config))
    normalised["exchange"] = normalised.get("exchange", _exchange(config))
    normalised["currency"] = normalised.get("currency", _currency(config))
    normalised["ticker"] = normalised.get("ticker", ticker)
    normalised["vendor_symbol"] = normalised.get("vendor_symbol", f"{ticker}.AX")
    normalised["trade_date"] = pd.to_datetime(
        normalised["trade_date"], errors="coerce", utc=False
    ).dt.strftime("%Y-%m-%d")

    for column in ("open", "high", "low", "close", "adj_close", "volume"):
        if column in normalised.columns:
            normalised[column] = pd.to_numeric(normalised[column], errors="coerce")

    columns = [
        "dataset_id",
        "exchange",
        "currency",
        "ticker",
        "vendor_symbol",
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
    ]
    return normalised[[column for column in columns if column in normalised.columns]].dropna(
        subset=["trade_date"]
    )


def _parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def _latest_available_trading_day(reference_dt: datetime | None = None) -> date:
    current = (reference_dt or datetime.now(UTC)).date()
    while current.weekday() >= 5:
        current -= timedelta(days=1)
    return current


def _resolve_horizon(config: dict[str, Any]) -> tuple[str, str]:
    end_date_value = str(config.get("end_date") or "").strip()
    if end_date_value:
        end_value = _parse_iso_date(end_date_value)
    else:
        end_value = _latest_available_trading_day()

    earliest_start_date = str(config.get("earliest_start_date") or "").strip()
    if earliest_start_date:
        start_value = _parse_iso_date(earliest_start_date)
    else:
        lookback_days = int(config.get("lookback_days") or 0)
        if lookback_days <= 0:
            raise RuntimeError("ASX request config requires earliest_start_date or positive lookback_days.")
        start_value = end_value - timedelta(days=lookback_days - 1)

    if end_value < start_value:
        raise RuntimeError("Resolved ASX request horizon has end_date before start_date.")
    return start_value.isoformat(), end_value.isoformat()


def _empty_daily_prices() -> pd.DataFrame:
    return pd.DataFrame(columns=["trade_date", "open", "high", "low", "close", "volume"])


def _vendor_symbol_for(config: dict[str, Any], ticker: str) -> str:
    vendor_symbol_map = config.get("vendor_symbol_map", {})
    return str(vendor_symbol_map.get(ticker, f"{ticker}.AX")).strip()


def _download_raw_csv_frame(
    *,
    config: dict[str, Any],
    ticker: str,
    start_date: str | None = None,
    end_date: str | None = None,
    allow_empty: bool = False,
) -> pd.DataFrame:
    import yfinance  # noqa: PLC0415

    vendor_symbol = _vendor_symbol_for(config, ticker)
    resolved_start_date, resolved_end_date = _resolve_horizon(config)
    start_date = start_date or resolved_start_date
    end_date = end_date or resolved_end_date
    frame = yfinance.download(
        tickers=vendor_symbol,
        start=start_date,
        end=(pd.Timestamp(end_date) + pd.Timedelta(days=1)).date().isoformat(),
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if frame is None or frame.empty:
        if allow_empty:
            return _empty_daily_prices()
        raise RuntimeError(f"No rows returned for {vendor_symbol} in window {start_date}..{end_date}.")

    normalized = frame.reset_index()
    normalized.columns = [
        column[0].lower() if isinstance(column, tuple) else str(column).lower()
        for column in normalized.columns
    ]
    if "date" in normalized.columns:
        normalized.rename(columns={"date": "trade_date"}, inplace=True)
    elif "datetime" in normalized.columns:
        normalized.rename(columns={"datetime": "trade_date"}, inplace=True)
    elif "index" in normalized.columns:
        normalized.rename(columns={"index": "trade_date"}, inplace=True)
    if "trade_date" not in normalized.columns:
        raise RuntimeError(f"Expected trade_date column after yFinance normalization for {ticker}.")

    normalized["trade_date"] = pd.to_datetime(normalized["trade_date"], errors="coerce").dt.date
    normalized = normalized.dropna(subset=["trade_date"]).sort_values("trade_date")
    if normalized.empty:
        raise RuntimeError(f"No valid trade_date rows remained after yFinance normalization for {ticker}.")
    normalized["trade_date"] = normalized["trade_date"].astype(str)
    normalized["ticker"] = ticker
    normalized["vendor_symbol"] = vendor_symbol
    normalized["dataset_id"] = _dataset_id(config)
    normalized["exchange"] = _exchange(config)
    normalized["currency"] = _currency(config)
    ordered_columns = [
        "dataset_id",
        "exchange",
        "currency",
        "ticker",
        "vendor_symbol",
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "adj close" if "adj close" in normalized.columns else None,
        "volume",
    ]
    return normalized[[column for column in ordered_columns if column is not None and column in normalized.columns]]


def _normalize_trade_dates(frame: pd.DataFrame) -> pd.DataFrame:
    if "trade_date" not in frame.columns:
        raise RuntimeError("Expected trade_date column in ASX raw CSV data.")
    normalized = frame.copy()
    normalized["trade_date"] = pd.to_datetime(normalized["trade_date"], errors="coerce").dt.date
    normalized = normalized.dropna(subset=["trade_date"]).sort_values("trade_date")
    if normalized.empty:
        raise RuntimeError("No valid trade_date rows remained after normalization.")
    normalized["trade_date"] = normalized["trade_date"].astype(str)
    return normalized.reset_index(drop=True)


def _read_existing_raw_frame(s3: Any, *, config: dict[str, Any], ticker: str) -> pd.DataFrame | None:
    raw_key = _raw_object_key(config, ticker)
    try:
        response = s3.get_object(Bucket=RAW_BUCKET, Key=raw_key)
    except Exception:
        return None
    return _normalize_trade_dates(pd.read_csv(io.BytesIO(response["Body"].read())))


def _previous_day(value: str) -> str:
    return (_parse_iso_date(value) - timedelta(days=1)).isoformat()


def _next_day(value: str) -> str:
    return (_parse_iso_date(value) + timedelta(days=1)).isoformat()


def _earliest_available_trading_day(reference_date: date) -> date:
    current = reference_date
    while current.weekday() >= 5:
        current += timedelta(days=1)
    return current


def _merge_frames(existing_frame: pd.DataFrame, *additional_frames: pd.DataFrame) -> pd.DataFrame:
    frames = [existing_frame, *[frame for frame in additional_frames if not frame.empty]]
    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined = _normalize_trade_dates(combined)
    return combined.drop_duplicates(subset=["trade_date"], keep="last").sort_values("trade_date").reset_index(drop=True)


def _load_raw_metadata(s3: Any, *, config: dict[str, Any], ticker: str) -> dict[str, Any]:
    metadata_key = _raw_metadata_key(config, ticker)
    try:
        response = s3.get_object(Bucket=RAW_BUCKET, Key=metadata_key)
    except Exception:
        return {}
    payload = json.loads(response["Body"].read().decode("utf-8"))
    return payload if isinstance(payload, dict) else {}


def _write_raw_metadata(s3: Any, *, config: dict[str, Any], ticker: str, payload: dict[str, Any]) -> None:
    metadata_key = _raw_metadata_key(config, ticker)
    s3.put_object(
        Bucket=RAW_BUCKET,
        Key=metadata_key,
        Body=json.dumps(payload, indent=2, sort_keys=True).encode("utf-8"),
        ContentType="application/json",
    )


def fetch_and_publish_raw_ohlcv(**_: Any) -> None:
    config = _load_request_config()
    s3 = get_s3_client()
    requested_start_date, requested_end_date = _resolve_horizon(config)
    requested_first_trade_date = _earliest_available_trading_day(_parse_iso_date(requested_start_date)).isoformat()
    requested_last_trade_date = _latest_available_trading_day(
        datetime.combine(_parse_iso_date(requested_end_date), datetime.min.time(), tzinfo=UTC)
    ).isoformat()

    published = 0
    skipped = 0
    for ticker in [str(value).strip().upper() for value in config.get("ticker_list", [])]:
        if not ticker:
            continue
        object_key = _raw_object_key(config, ticker)
        existing_frame = _read_existing_raw_frame(s3, config=config, ticker=ticker)
        metadata = _load_raw_metadata(s3, config=config, ticker=ticker)
        if existing_frame is None:
            frame = _download_raw_csv_frame(
                config=config,
                ticker=ticker,
                start_date=requested_start_date,
                end_date=requested_end_date,
            )
            status = "downloaded"
            metadata = {
                "ticker": ticker,
                "vendor_symbol": _vendor_symbol_for(config, ticker),
                "last_requested_start_date": requested_start_date,
                "last_requested_end_date": requested_end_date,
            }
        else:
            first_date = str(existing_frame["trade_date"].iloc[0])
            last_date = str(existing_frame["trade_date"].iloc[-1])
            known_earliest_trade_date = str(metadata.get("known_earliest_trade_date") or "").strip()
            missing_before = requested_first_trade_date < first_date
            if known_earliest_trade_date and requested_first_trade_date <= known_earliest_trade_date:
                missing_before = False
            missing_after = requested_last_trade_date > last_date
            if not missing_before and not missing_after:
                skipped += 1
                LOGGER.info(
                    "Skipping %s: existing raw object already covers %s..%s.",
                    ticker,
                    requested_start_date,
                    requested_end_date,
                )
                continue

            leading_frame = _empty_daily_prices()
            trailing_frame = _empty_daily_prices()
            if missing_before:
                leading_end_date = _previous_day(first_date)
                leading_frame = _download_raw_csv_frame(
                    config=config,
                    ticker=ticker,
                    start_date=requested_first_trade_date,
                    end_date=leading_end_date,
                    allow_empty=True,
                )
                if leading_frame.empty:
                    metadata["known_earliest_trade_date"] = first_date
            if missing_after:
                trailing_start_date = _next_day(last_date)
                trailing_frame = _download_raw_csv_frame(
                    config=config,
                    ticker=ticker,
                    start_date=trailing_start_date,
                    end_date=requested_last_trade_date,
                    allow_empty=True,
                )
            frame = _merge_frames(existing_frame, leading_frame, trailing_frame)
            status = "updated_existing"

        buffer = io.StringIO()
        frame.to_csv(buffer, index=False)
        s3.put_object(
            Bucket=RAW_BUCKET,
            Key=object_key,
            Body=buffer.getvalue().encode("utf-8"),
            ContentType="text/csv",
        )
        metadata["ticker"] = ticker
        metadata["vendor_symbol"] = _vendor_symbol_for(config, ticker)
        metadata["first_trade_date"] = str(frame["trade_date"].iloc[0])
        metadata["last_trade_date"] = str(frame["trade_date"].iloc[-1])
        metadata["last_requested_start_date"] = requested_start_date
        metadata["last_requested_end_date"] = requested_end_date
        metadata["updated_at"] = _utc_iso(datetime.now(UTC))
        _write_raw_metadata(s3, config=config, ticker=ticker, payload=metadata)
        published += 1
        LOGGER.info(
            "%s raw CSV object at s3://%s/%s with %d rows.",
            "Updated" if status == "updated_existing" else "Published",
            RAW_BUCKET,
            object_key,
            len(frame),
        )

    if published == 0 and skipped == 0:
        raise RuntimeError("No ASX raw CSV objects were written to MinIO raw.")

    LOGGER.info(
        "ASX raw ingestion complete. published=%d skipped=%d horizon=%s..%s.",
        published,
        skipped,
        requested_start_date,
        requested_end_date,
    )


def transform_raw_to_conformed(**_: Any) -> None:
    config = _load_request_config()
    s3 = get_s3_client()
    ingest_ts = _utc_iso(datetime.now(UTC))

    written = 0
    for ticker in [str(value).strip().upper() for value in config.get("ticker_list", [])]:
        if not ticker:
            continue
        raw_key = _raw_object_key(config, ticker)
        conformed_key = _conformed_object_key(config, ticker)
        response = s3.get_object(Bucket=RAW_BUCKET, Key=raw_key)
        frame = _normalise_frame(
            pd.read_csv(io.BytesIO(response["Body"].read())),
            ticker=ticker,
            config=config,
        )
        frame["ingest_ts"] = ingest_ts
        frame["raw_bucket"] = RAW_BUCKET
        frame["raw_key"] = raw_key
        frame["raw_uri"] = f"s3://{RAW_BUCKET}/{raw_key}"

        table = pa.Table.from_pandas(frame, preserve_index=False)
        buffer = io.BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        buffer.seek(0)
        s3.put_object(
            Bucket=CONFORMED_BUCKET,
            Key=conformed_key,
            Body=buffer.getvalue(),
            ContentType="application/octet-stream",
        )
        written += 1
        LOGGER.info(
            "Published conformed Parquet object to s3://%s/%s.", CONFORMED_BUCKET, conformed_key
        )

    if written == 0:
        raise RuntimeError("No ASX conformed Parquet objects were written.")

    LOGGER.info("Published %d ASX conformed Parquet objects to MinIO conformed.", written)


def _list_bucket_keys(s3: Any, bucket: str, prefix: str) -> list[str]:
    keys: list[str] = []
    continuation_token: str | None = None

    while True:
        kwargs: dict[str, Any] = {"Bucket": bucket, "Prefix": prefix}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token
        response = s3.list_objects_v2(**kwargs)
        keys.extend(str(item["Key"]) for item in response.get("Contents", []))
        if not response.get("IsTruncated"):
            break
        continuation_token = response.get("NextContinuationToken")

    return keys


def summarise_conformed_to_curated(**_: Any) -> None:
    config = _load_request_config()
    s3 = get_s3_client()
    prefix = f"tabular/{_dataset_id(config)}/exchange={_exchange(config)}/ticker="
    conformed_keys = [key for key in _list_bucket_keys(s3, CONFORMED_BUCKET, prefix) if key.endswith(".parquet")]

    if not conformed_keys:
        raise RuntimeError("No ASX conformed Parquet objects were found in MinIO.")

    frames: list[pd.DataFrame] = []
    for key in conformed_keys:
        response = s3.get_object(Bucket=CONFORMED_BUCKET, Key=key)
        buffer = io.BytesIO(response["Body"].read())
        frames.append(pq.read_table(buffer).to_pandas())

    curated = pd.concat(frames, ignore_index=True)
    curated["trade_date"] = pd.to_datetime(curated["trade_date"], errors="coerce")
    curated = curated.dropna(subset=["trade_date"])
    for column in ("dataset_id", "exchange", "currency", "ticker", "vendor_symbol", "raw_bucket", "raw_key", "raw_uri"):
        if column in curated.columns:
            curated[column] = curated[column].map(lambda value: None if pd.isna(value) else str(value))
    curated = curated.sort_values(["ticker", "trade_date", "ingest_ts"], ascending=[True, True, True])
    curated = curated.drop_duplicates(subset=["dataset_id", "exchange", "ticker", "trade_date"], keep="last")
    curated["trade_date"] = curated["trade_date"].dt.strftime("%Y-%m-%d")
    curated["curated_at"] = _utc_iso(datetime.now(UTC))
    curated["conformed_bucket"] = CONFORMED_BUCKET

    table = pa.Table.from_pandas(curated, preserve_index=False)
    buffer = io.BytesIO()
    pq.write_table(table, buffer, compression="snappy")
    buffer.seek(0)
    curated_key = _curated_object_key(config)
    s3.put_object(
        Bucket=CURATED_BUCKET,
        Key=curated_key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )
    LOGGER.info("Published curated ASX panel to s3://%s/%s.", CURATED_BUCKET, curated_key)


PUBLIC_CURATED_SOURCE_URL = (
    "https://raw.githubusercontent.com/Marek-Czarnecki/data-analytics-capstone-public"
    "/main/data/processed/market_ohlcv_daily_v2/exchange=ASX/asx_ohlcv_panel_clean.parquet"
)
PUBLIC_CURATED_SOURCE_LABEL = (
    "github:Marek-Czarnecki/data-analytics-capstone-public@main:"
    "data/processed/market_ohlcv_daily_v2/exchange=ASX/asx_ohlcv_panel_clean.parquet"
)


def fetch_curated_panel_from_public_source(**_: Any) -> None:
    """Community-edition replacement for the raw -> conformed -> curated chain.

    Downloads a pre-cleaned, already panel-shaped Parquet file from a public
    GitHub repo and writes it straight into the MinIO curated zone at the
    exact key asx_ohlcv_curated_to_iceberg already reads from. No yFinance
    call, no raw/conformed MinIO objects — the community edition doesn't
    populate those buckets at all for this solution, by design.
    """
    config = _load_request_config()
    s3 = get_s3_client()

    req = request.Request(
        PUBLIC_CURATED_SOURCE_URL,
        headers={"User-Agent": "open-source-data-lake-team-community-edition"},
    )
    try:
        with request.urlopen(req, timeout=120) as response:
            payload = response.read()
    except error.URLError as exc:
        raise RuntimeError(
            f"Failed to download curated panel from {PUBLIC_CURATED_SOURCE_URL}: {exc}"
        ) from exc

    if not payload:
        raise RuntimeError(f"Public curated panel at {PUBLIC_CURATED_SOURCE_URL} was empty.")

    table = pq.read_table(io.BytesIO(payload))
    columns = set(table.schema.names)
    required_columns = {"trade_date", "close", "volume"}
    missing_required = required_columns - columns
    if missing_required:
        raise RuntimeError(
            f"Public curated panel is missing required column(s) {sorted(missing_required)}. "
            f"Columns present: {sorted(columns)}."
        )
    if "ticker" not in columns and "vendor_symbol" not in columns:
        raise RuntimeError(
            "Public curated panel has neither 'ticker' nor 'vendor_symbol' column."
        )

    frame = table.to_pandas()
    ticker_column = "ticker" if "ticker" in frame.columns else "vendor_symbol"
    frame[ticker_column] = frame[ticker_column].astype(str).str.strip().str.upper()

    configured_tickers = {str(t).strip().upper() for t in config.get("ticker_list", [])}
    if configured_tickers:
        present_tickers = set(frame[ticker_column].unique())
        missing_from_source = configured_tickers - present_tickers
        if missing_from_source:
            LOGGER.warning(
                "Public curated panel is missing %d configured ticker(s): %s",
                len(missing_from_source),
                sorted(missing_from_source),
            )
        frame = frame[frame[ticker_column].isin(configured_tickers)].reset_index(drop=True)

    if frame.empty:
        raise RuntimeError(
            "Public curated panel had no rows left after filtering to the configured ticker list."
        )

    frame["curated_at"] = _utc_iso(datetime.now(UTC))
    frame["curated_source"] = PUBLIC_CURATED_SOURCE_LABEL

    out_table = pa.Table.from_pandas(frame, preserve_index=False)
    buffer = io.BytesIO()
    pq.write_table(out_table, buffer, compression="snappy")
    buffer.seek(0)

    curated_key = _curated_object_key(config)
    s3.put_object(
        Bucket=CURATED_BUCKET,
        Key=curated_key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )
    LOGGER.info(
        "Published community curated ASX panel (%d rows, %d tickers) to s3://%s/%s from %s.",
        len(frame),
        frame[ticker_column].nunique(),
        CURATED_BUCKET,
        curated_key,
        PUBLIC_CURATED_SOURCE_URL,
    )


def _request_json(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    expected_statuses: tuple[int, ...] = (200,),
) -> tuple[int, dict[str, Any] | list[Any] | None]:
    url = f"{BASE_URL}{path}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = request.Request(url=url, data=body, headers=headers, method=method)

    try:
        with request.urlopen(req, timeout=30) as response:
            raw_body = response.read().decode("utf-8")
            parsed = json.loads(raw_body) if raw_body else None
            if response.status not in expected_statuses:
                raise RuntimeError(
                    f"Unexpected Lakekeeper status for {method} {path}: {response.status}"
                )
            return response.status, parsed
    except error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8")
        parsed = None
        if raw_body:
            try:
                parsed = json.loads(raw_body)
            except json.JSONDecodeError:
                parsed = None
        exc.lakekeeper_error_payload = parsed
        raise


def _bootstrap_catalog() -> None:
    _request_json(
        "POST",
        "/management/v1/bootstrap",
        payload={"accept-terms-of-use": True},
        expected_statuses=(204,),
    )


def _is_project_not_found_error(exc: error.HTTPError) -> bool:
    payload = getattr(exc, "lakekeeper_error_payload", None) or {}
    return exc.code == 404 and payload.get("error", {}).get("type") == "ProjectNotFound"


def _find_warehouse(warehouses: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for warehouse in warehouses:
        if warehouse.get("name") == name:
            return warehouse
    return None


def _create_warehouse() -> dict[str, Any]:
    try:
        _, warehouse_payload = _request_json(
            "POST",
            "/management/v1/warehouse",
            payload=WAREHOUSE_CREATE_PAYLOAD,
            expected_statuses=(201,),
        )
    except error.HTTPError as exc:
        if not _is_project_not_found_error(exc):
            raise
        _bootstrap_catalog()
        _, warehouse_payload = _request_json(
            "POST",
            "/management/v1/warehouse",
            payload=WAREHOUSE_CREATE_PAYLOAD,
            expected_statuses=(201,),
        )

    if not isinstance(warehouse_payload, dict):
        raise RuntimeError("Lakekeeper create warehouse response was not a JSON object.")
    return warehouse_payload


def ensure_warehouse() -> str:
    _, warehouses_payload = _request_json("GET", "/management/v1/warehouse")
    warehouses = (
        warehouses_payload.get("warehouses", [])
        if isinstance(warehouses_payload, dict)
        else []
    )
    warehouse = _find_warehouse(warehouses, WAREHOUSE_NAME)
    if warehouse is None:
        warehouse = _create_warehouse()
    warehouse_id = warehouse.get("warehouse-id")
    if not warehouse_id:
        raise RuntimeError("Lakekeeper warehouse response did not include warehouse-id.")
    return warehouse_id


def ensure_namespace(warehouse_id: str) -> None:
    _, namespaces_payload = _request_json("GET", f"/catalog/v1/{warehouse_id}/namespaces")
    namespaces = (
        namespaces_payload.get("namespaces", [])
        if isinstance(namespaces_payload, dict)
        else []
    )
    namespace_names = {tuple(namespace) for namespace in namespaces}

    if (NAMESPACE_NAME,) not in namespace_names:
        _request_json(
            "POST",
            f"/catalog/v1/{warehouse_id}/namespaces",
            payload={"namespace": [NAMESPACE_NAME]},
            expected_statuses=(200,),
        )


def _load_catalog_client() -> Any:
    import sys

    vendored = str(VENDORED_PACKAGES_PATH)
    if vendored not in sys.path:
        sys.path.insert(0, vendored)

    from pyiceberg.catalog import load_catalog

    return load_catalog(
        "lakekeeper",
        **{
            "type": "rest",
            "uri": CATALOG_URI,
            "warehouse": WAREHOUSE_NAME,
            "s3.endpoint": MINIO_ENDPOINT,
            "s3.access-key-id": MINIO_ACCESS_KEY,
            "s3.secret-access-key": MINIO_SECRET_KEY,
            "s3.region": MINIO_REGION,
        },
    )


def _create_asx_summary_table(catalog: Any) -> Any:
    from pyiceberg.schema import Schema
    from pyiceberg.types import DoubleType, LongType, NestedField, StringType

    schema = Schema(
        NestedField(field_id=1, name="ticker", field_type=StringType(), required=False),
        NestedField(field_id=2, name="run_date", field_type=StringType(), required=False),
        NestedField(field_id=3, name="row_count", field_type=LongType(), required=False),
        NestedField(field_id=4, name="start_trade_date", field_type=StringType(), required=False),
        NestedField(field_id=5, name="end_trade_date", field_type=StringType(), required=False),
        NestedField(field_id=6, name="min_close", field_type=DoubleType(), required=False),
        NestedField(field_id=7, name="max_close", field_type=DoubleType(), required=False),
        NestedField(field_id=8, name="latest_close", field_type=DoubleType(), required=False),
        NestedField(field_id=9, name="average_volume", field_type=DoubleType(), required=False),
        NestedField(field_id=10, name="generated_at", field_type=StringType(), required=False),
    )
    return catalog.create_table(TABLE_IDENTIFIER, schema=schema)


def _existing_run_keys(table: Any) -> set[tuple[str, str]]:
    # NOTE: this dedup key is (ticker, run_date) only — it does not know or
    # care which ingestion DAG produced the curated panel it's summarising.
    # asx_ohlcv_raw (yFinance) and asx_ohlcv_curated_from_public_source
    # (public GitHub Parquet) both write to the same curated bucket key and
    # both feed this same DAG, so if BOTH run on the same calendar day,
    # whichever ran first "wins" for that day — the second run's
    # would-be-different summary values are silently skipped, not merged
    # or overwritten. Live-reproduced 2026-08-21: running the yFinance path
    # then the public-source path on the same day left Iceberg showing the
    # yFinance numbers (fresher, coincidentally) even after the public-
    # source curated panel had genuinely overwritten the MinIO object. In a
    # real deployment this never actually collides — the full edition only
    # ever runs the yFinance path, the community edition only ever runs the
    # public-source path — this only matters if you deliberately run both
    # in the same sandbox on the same day, as we did while proving this out.
    snapshots = table.metadata.snapshots or []
    if not snapshots:
        return set()

    try:
        existing = table.scan().to_arrow()
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("Unable to inspect existing ASX summary rows before append: %s", exc)
        return set()

    required = {"ticker", "run_date"}
    if not required.issubset(set(existing.column_names)):
        return set()

    tickers = existing["ticker"].to_pylist()
    run_dates = existing["run_date"].to_pylist()
    return {
        (str(ticker), str(run_date))
        for ticker, run_date in zip(tickers, run_dates, strict=False)
        if ticker is not None and run_date is not None
    }


def _load_curated_asx_frame(config: dict[str, Any]) -> pd.DataFrame:
    s3 = get_s3_client()
    curated_key = _curated_object_key(config)
    response = s3.get_object(Bucket=CURATED_BUCKET, Key=curated_key)
    frame = pq.read_table(io.BytesIO(response["Body"].read())).to_pandas()
    if frame.empty:
        raise RuntimeError("Curated ASX panel was empty.")
    return frame


def _build_asx_summary_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    curated = _load_curated_asx_frame(config)
    curated["trade_date"] = pd.to_datetime(curated["trade_date"], errors="coerce")
    curated["close"] = pd.to_numeric(curated.get("close"), errors="coerce")
    curated["volume"] = pd.to_numeric(curated.get("volume"), errors="coerce")
    if "ingest_ts" in curated.columns:
        curated["ingest_ts"] = pd.to_datetime(curated["ingest_ts"], errors="coerce")
    else:
        curated["ingest_ts"] = pd.NaT

    curated = curated.dropna(subset=["trade_date"])
    if curated.empty:
        raise RuntimeError("Curated ASX panel had no valid trade_date values.")

    ticker_column = "vendor_symbol" if "vendor_symbol" in curated.columns else "ticker"
    curated[ticker_column] = curated[ticker_column].map(lambda value: None if pd.isna(value) else str(value))
    curated = curated.dropna(subset=[ticker_column])
    curated = curated.sort_values([ticker_column, "trade_date", "ingest_ts"], ascending=[True, True, True])

    run_date = datetime.now(UTC).date().isoformat()
    generated_at = _utc_iso(datetime.now(UTC))
    rows: list[dict[str, Any]] = []
    for ticker, frame in curated.groupby(ticker_column, dropna=True):
        frame = frame.reset_index(drop=True)
        latest_row = frame.sort_values(["trade_date", "ingest_ts"], ascending=[True, True]).iloc[-1]
        close_series = pd.to_numeric(frame["close"], errors="coerce").dropna()
        volume_series = pd.to_numeric(frame["volume"], errors="coerce").dropna()
        rows.append(
            {
                "ticker": str(ticker),
                "run_date": run_date,
                "row_count": int(len(frame)),
                "start_trade_date": frame["trade_date"].min().date().isoformat(),
                "end_trade_date": frame["trade_date"].max().date().isoformat(),
                "min_close": float(close_series.min()) if not close_series.empty else None,
                "max_close": float(close_series.max()) if not close_series.empty else None,
                "latest_close": (
                    float(pd.to_numeric(latest_row.get("close"), errors="coerce"))
                    if pd.notna(pd.to_numeric(latest_row.get("close"), errors="coerce"))
                    else None
                ),
                "average_volume": float(volume_series.mean()) if not volume_series.empty else None,
                "generated_at": generated_at,
            }
        )

    if not rows:
        raise RuntimeError("No ASX summary rows were derived from the curated panel.")
    return rows


def materialise_curated_asx_ohlcv_to_iceberg(**_: Any) -> None:
    import sys

    vendored = str(VENDORED_PACKAGES_PATH)
    if vendored not in sys.path:
        sys.path.insert(0, vendored)

    from pyiceberg.exceptions import NoSuchTableError

    config = _load_request_config()
    rows = _build_asx_summary_rows(config)
    warehouse_id = ensure_warehouse()
    ensure_namespace(warehouse_id)
    catalog = _load_catalog_client()

    try:
        table = catalog.load_table(TABLE_IDENTIFIER)
    except NoSuchTableError:
        table = _create_asx_summary_table(catalog)

    existing_keys = _existing_run_keys(table)
    rows_to_append = [
        row for row in rows if (str(row["ticker"]), str(row["run_date"])) not in existing_keys
    ]

    if not rows_to_append:
        LOGGER.info(
            "ASX summary rows for run_date=%s are already present in %s.%s; leaving table unchanged.",
            rows[0]["run_date"],
            NAMESPACE_NAME,
            TABLE_NAME,
        )
    else:
        table.append(pa.Table.from_pylist(rows_to_append))
        LOGGER.info(
            "Appended %d ASX summary rows into %s.%s for run_date=%s.",
            len(rows_to_append),
            NAMESPACE_NAME,
            TABLE_NAME,
            rows_to_append[0]["run_date"],
        )

    table = catalog.load_table(TABLE_IDENTIFIER)
    metadata_location = table.metadata_location
    if not metadata_location:
        raise RuntimeError("ASX Iceberg table did not expose a metadata location.")

    LOGGER.info(
        "ASX Iceberg materialization succeeded for %s.%s with metadata at %s.",
        NAMESPACE_NAME,
        TABLE_NAME,
        metadata_location,
    )
