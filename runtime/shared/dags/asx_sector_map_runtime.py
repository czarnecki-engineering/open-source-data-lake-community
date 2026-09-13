from __future__ import annotations

import io
import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


LOGGER = logging.getLogger(__name__)

MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_REGION = "local-01"
CURATED_BUCKET = "curated"
REQUEST_CONFIG_PATH = Path("/opt/airflow/config/asx/asx_data_request.json")
SECTOR_MAP_DATASET_ID = "asx_ticker_sector_map_v1"
EXCHANGE = "ASX"

YAHOO_TO_GICS = {
    "Basic Materials": "Materials",
    "Communication Services": "Communication Services",
    "Consumer Cyclical": "Consumer Discretionary",
    "Consumer Defensive": "Consumer Staples",
    "Energy": "Energy",
    "Financial Services": "Financials",
    "Healthcare": "Health Care",
    "Industrials": "Industrials",
    "Real Estate": "Real Estate",
    "Technology": "Information Technology",
    "Utilities": "Utilities",
}

MANUAL_OVERRIDES = {
    "SGH": {
        "company_name": "SGH Limited",
        "sector": "Industrials",
        "industry": "Capital Goods",
        "source": "Manual verification",
        "status": "resolved",
    }
}

OUTPUT_COLUMNS = [
    "dataset_id",
    "exchange",
    "ticker",
    "vendor_symbol",
    "company_name",
    "sector",
    "industry",
    "source",
    "classification_date",
    "status",
]


def _load_boto3() -> Any:
    import boto3  # noqa: PLC0415

    return boto3


def _load_yfinance() -> Any:
    import yfinance as yf  # noqa: PLC0415

    return yf


def get_s3_client() -> Any:
    boto3 = _load_boto3()
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name=MINIO_REGION,
    )


def _request_config_path() -> Path:
    candidate = Path(
        os.getenv("ASX_REQUEST_CONFIG_PATH", str(REQUEST_CONFIG_PATH))
    ).expanduser().resolve()
    if not candidate.is_file():
        raise RuntimeError(f"ASX request config was not found at {candidate}.")
    return candidate


def load_request_config(path: Path | None = None) -> dict[str, Any]:
    candidate = path or _request_config_path()
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"ASX request config at {candidate} was not a JSON object.")
    return payload


def sector_map_object_key() -> str:
    return (
        f"tabular/{SECTOR_MAP_DATASET_ID}/exchange={EXCHANGE}/"
        "asx_ticker_sector_map.parquet"
    )


def _clean_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def normalize_yahoo_sector(yahoo_sector: str) -> str:
    cleaned = _clean_text(yahoo_sector)
    return YAHOO_TO_GICS.get(cleaned, cleaned)


def classify_ticker(
    ticker: str,
    vendor_symbol: str,
    info_loader: Callable[[str], dict[str, Any]],
    classification_date: str,
) -> dict[str, str]:
    try:
        info = info_loader(vendor_symbol) or {}
        yahoo_sector = _clean_text(info.get("sector"))
        sector = normalize_yahoo_sector(yahoo_sector)
        company_name = (
            _clean_text(info.get("longName"))
            or _clean_text(info.get("shortName"))
            or _clean_text(info.get("displayName"))
        )
        industry = _clean_text(info.get("industry"))
        status = "resolved" if sector else ("unmapped_sector" if yahoo_sector else "unresolved")
        row = {
            "ticker": ticker,
            "vendor_symbol": vendor_symbol,
            "company_name": company_name,
            "sector": sector,
            "industry": industry,
            "source": "Yahoo Finance via yfinance",
            "classification_date": classification_date,
            "status": status,
        }
    except Exception as exc:
        row = {
            "ticker": ticker,
            "vendor_symbol": vendor_symbol,
            "company_name": "",
            "sector": "",
            "industry": "",
            "source": "Yahoo Finance via yfinance",
            "classification_date": classification_date,
            "status": f"error: {type(exc).__name__}: {exc}",
        }

    if ticker in MANUAL_OVERRIDES:
        row.update(MANUAL_OVERRIDES[ticker])
    return row


def build_sector_map(
    config: dict[str, Any],
    info_loader: Callable[[str], dict[str, Any]],
    *,
    classification_date: str | None = None,
) -> pd.DataFrame:
    tickers = config.get("ticker_list")
    symbol_map = config.get("vendor_symbol_map")
    if not isinstance(tickers, list) or not all(isinstance(value, str) for value in tickers):
        raise ValueError("'ticker_list' must be a list of strings.")
    if not isinstance(symbol_map, dict):
        raise ValueError("'vendor_symbol_map' must be an object.")

    normalized_tickers = [value.strip().upper() for value in tickers if value.strip()]
    duplicates = sorted({ticker for ticker in normalized_tickers if normalized_tickers.count(ticker) > 1})
    if duplicates:
        raise ValueError(f"Duplicate ticker codes in ticker_list: {', '.join(duplicates)}")

    missing_symbols = [ticker for ticker in normalized_tickers if not symbol_map.get(ticker)]
    if missing_symbols:
        raise ValueError("Missing vendor symbols for: " + ", ".join(sorted(missing_symbols)))

    as_of = classification_date or date.today().isoformat()
    rows = []
    for ticker in normalized_tickers:
        row = classify_ticker(ticker, str(symbol_map[ticker]), info_loader, as_of)
        row["dataset_id"] = SECTOR_MAP_DATASET_ID
        row["exchange"] = EXCHANGE
        rows.append(row)

    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def publish_curated_sector_map(**_: Any) -> None:
    config = load_request_config()
    yf = _load_yfinance()
    sector_map = build_sector_map(
        config,
        lambda symbol: yf.Ticker(symbol).get_info() or {},
    )
    if sector_map.empty:
        raise RuntimeError("No ASX sector-map rows were produced.")

    table = pa.Table.from_pandas(sector_map, preserve_index=False)
    buffer = io.BytesIO()
    pq.write_table(table, buffer, compression="snappy")
    key = sector_map_object_key()
    get_s3_client().put_object(
        Bucket=CURATED_BUCKET,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )

    unresolved = int((sector_map["status"] != "resolved").sum())
    LOGGER.info(
        "Published ASX sector map to s3://%s/%s. rows=%d unresolved=%d.",
        CURATED_BUCKET,
        key,
        len(sector_map),
        unresolved,
    )
