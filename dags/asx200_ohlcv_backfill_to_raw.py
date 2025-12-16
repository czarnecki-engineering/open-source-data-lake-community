from __future__ import annotations

# NOTE: This DAG is intentionally written as a near-copy of raw_market_ohlcv_daily_asx.py.
# Only required changes:
#   1) ticker source: fixed CSV config in raw bucket (ASX200 list)
#   2) window: 5 years (instead of ~45 days / last 30 trading days)
#   3) resumability: state + audit artifacts in raw bucket

from datetime import datetime, timedelta, timezone
import io
import json
import os
import time

import boto3
import pandas as pd
import pendulum
import yfinance as yf

from airflow import DAG
from airflow.operators.python import PythonOperator


DATASET_ID = "market_ohlcv_daily"
EXCHANGE = "ASX"
CURRENCY = "AUD"

RAW_BUCKET = "raw"
MINIO_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")


# --- Fixed bucket-driven config (no options) ---
# Upload this file:
#   s3://raw/tabular/market_ohlcv_daily/control/asx200_backfill/asx200_tickers.csv
# Format:
#   ticker
#   BHP
#   CBA
#   ...
ASX200_TICKERS_KEY = f"tabular/{DATASET_ID}/control/asx200_backfill/asx200_tickers.csv"
ASX200_TICKERS_PATH = os.getenv(
    "ASX200_TICKERS_PATH",
    "/opt/airflow/config/asx200_tickers.csv",
) 

# Resumability + audit (fixed locations)
STATE_KEY = f"tabular/{DATASET_ID}/control/asx200_backfill/state.json"
AUDIT_PREFIX = f"tabular/{DATASET_ID}/audit/asx200_backfill"


def _s3_client():
    # Match the daily DAG pattern (including defaults that work with your compose stack)
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def _raw_key(trade_date: str, ticker: str) -> str:
    # Must be IDENTICAL to daily DAG
    return (
        f"tabular/{DATASET_ID}/exchange={EXCHANGE}/trade_date={trade_date}/"
        f"ticker={ticker}.csv"
    )


def _vendor_symbol(ticker: str) -> str:
    # Must be IDENTICAL to daily DAG
    return f"{ticker}.AX"


def _read_asx200_tickers_from_config() -> list[str]:
    if not os.path.exists(ASX200_TICKERS_PATH):
        raise RuntimeError(
            f"Missing ASX200 tickers config at {ASX200_TICKERS_PATH}. "
            f"Ensure ./config/asx200_tickers.csv exists and is mounted into the Airflow container."
        )

    df = pd.read_csv(ASX200_TICKERS_PATH)
    cols = [c.strip().lower() for c in df.columns.astype(str).tolist()]
    if "ticker" not in cols:
        df = pd.read_csv(ASX200_TICKERS_PATH, header=None, names=["ticker"])

    tickers = (
        df["ticker"]
        .astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"[^A-Z0-9]", "", regex=True)
        .tolist()
    )
    tickers = [t for t in tickers if t]

    # de-dupe preserve order
    seen = set()
    out: list[str] = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            out.append(t)

    if not out:
        raise RuntimeError(f"ASX200 tickers config empty/invalid at {ASX200_TICKERS_PATH}")

    return out


def _read_asx200_tickers_from_bucket(s3) -> list[str]:
    try:
        obj = s3.get_object(Bucket=RAW_BUCKET, Key=ASX200_TICKERS_KEY)
        text = obj["Body"].read().decode("utf-8")
    except Exception as e:
        raise RuntimeError(
            f"Missing ASX200 tickers config. Upload to s3://{RAW_BUCKET}/{ASX200_TICKERS_KEY}. Error: {e}"
        )

    df = pd.read_csv(io.StringIO(text))
    cols = [c.strip().lower() for c in df.columns.astype(str).tolist()]
    if "ticker" not in cols:
        df = pd.read_csv(io.StringIO(text), header=None, names=["ticker"])

    tickers = (
        df["ticker"]
        .astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"[^A-Z0-9]", "", regex=True)
        .tolist()
    )
    tickers = [t for t in tickers if t]

    # de-dupe preserve order
    seen = set()
    out: list[str] = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            out.append(t)

    if not out:
        raise RuntimeError(f"ASX200 tickers config empty/invalid at s3://{RAW_BUCKET}/{ASX200_TICKERS_KEY}")

    return out


def _load_state(s3) -> dict:
    try:
        obj = s3.get_object(Bucket=RAW_BUCKET, Key=STATE_KEY)
        return json.loads(obj["Body"].read().decode("utf-8"))
    except Exception:
        return {"version": 1, "tickers": {}}


def _save_state(s3, state: dict) -> None:
    state["last_updated"] = pendulum.now("UTC").to_iso8601_string()
    s3.put_object(
        Bucket=RAW_BUCKET,
        Key=STATE_KEY,
        Body=json.dumps(state, indent=2).encode("utf-8"),
        ContentType="application/json",
    )


def _append_audit_error(s3, run_date: str, payload: dict) -> None:
    key = f"{AUDIT_PREFIX}/run_date={run_date}/errors.json"
    try:
        obj = s3.get_object(Bucket=RAW_BUCKET, Key=key)
        existing = json.loads(obj["Body"].read().decode("utf-8"))
    except Exception:
        existing = {"run_date": run_date, "errors": []}

    existing["errors"].append(payload)
    s3.put_object(
        Bucket=RAW_BUCKET,
        Key=key,
        Body=json.dumps(existing, indent=2).encode("utf-8"),
        ContentType="application/json",
    )


def fetch_and_write_raw_csvs() -> None:
    """
    Backfill variant of the daily DAG:
      - reads ASX200 tickers from a fixed bucket config file
      - downloads daily OHLCV for 5 years
      - writes one CSV object per (ticker, trade_date) into raw/
      - uses a state file in raw/ to resume (skip completed tickers)
      - records per-ticker failures to audit/errors.json
    """
    s3 = _s3_client()

    end = datetime.now(timezone.utc).date()
    start = (end - timedelta(days=365 * 5))

    run_date = end.isoformat()

    tickers = _read_asx200_tickers_from_config()

    state = _load_state(s3)
    state["window"] = {"start": str(start), "end": str(end)}
    state.setdefault("tickers", {})

    # Explicit throttle (conservative; matches backfill requirement)
    throttle_seconds = 2.0
    max_retries = 3
    backoff_seconds = 5.0

    for ticker in tickers:
        if state["tickers"].get(ticker, {}).get("status") == "complete":
            continue

        symbol = _vendor_symbol(ticker)

        try:
            df = None
            last_err = None

            for i in range(max_retries):
                try:
                    time.sleep(throttle_seconds)
                    df = yf.download(
                        tickers=symbol,
                        start=str(start),
                        end=str(end + timedelta(days=1)),
                        interval="1d",
                        auto_adjust=False,
                        progress=False,
                        threads=False,
                    )
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
                    time.sleep(backoff_seconds * (2 ** i))

            if last_err is not None:
                raise last_err

            if df is None or df.empty:
                raise RuntimeError("No data returned")

            # --- Normalisation pattern: mirror the daily DAG approach ---
            # Use reset_index so 'trade_date' is a column (Series), then .dt works reliably.
            #df = df.reset_index()
            #df.columns = [str(c).lower() for c in df.columns]
            #df.rename(columns={"date": "trade_date"}, inplace=True)
            #df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date.astype(str)
            # -----------------------------------------------------------
            df = df.reset_index()

            # MATCH DAILY DAG: handle tuple columns from yfinance/pandas
            df.columns = [
                c[0].lower() if isinstance(c, tuple) else str(c).lower()
                for c in df.columns
            ]

            # Robust rename: yfinance index column is usually Date, but keep it defensive
            if "date" in df.columns:
                df.rename(columns={"date": "trade_date"}, inplace=True)
            elif "datetime" in df.columns:
                df.rename(columns={"datetime": "trade_date"}, inplace=True)
            elif "index" in df.columns:
                df.rename(columns={"index": "trade_date"}, inplace=True)

            if "trade_date" not in df.columns:
                raise RuntimeError(f"Expected trade_date after reset_index(); got columns={df.columns.tolist()}")

            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date.astype(str)

            rows_written = 0

            for _, row in df.iterrows():
                trade_date = row["trade_date"]

                out = pd.DataFrame(
                    [
                        {
                            "dataset_id": DATASET_ID,
                            "exchange": EXCHANGE,
                            "ticker": ticker,
                            "vendor_symbol": symbol,
                            "currency": CURRENCY,
                            "trade_date": trade_date,
                            "open": float(row["open"]) if pd.notna(row["open"]) else None,
                            "high": float(row["high"]) if pd.notna(row["high"]) else None,
                            "low": float(row["low"]) if pd.notna(row["low"]) else None,
                            "close": float(row["close"]) if pd.notna(row["close"]) else None,
                            "volume": int(row["volume"]) if pd.notna(row["volume"]) else None,
                            "adj_close": float(row["adj close"]) if pd.notna(row.get("adj close")) else None,
                        }
                    ]
                )

                csv_buf = io.StringIO()
                out.to_csv(csv_buf, index=False)

                key = _raw_key(trade_date=trade_date, ticker=ticker)
                s3.put_object(
                    Bucket=RAW_BUCKET,
                    Key=key,
                    Body=csv_buf.getvalue().encode("utf-8"),
                    ContentType="text/csv",
                )
                rows_written += 1

            state["tickers"][ticker] = {
                "status": "complete",
                "rows_written": rows_written,
                "completed_at": pendulum.now("UTC").to_iso8601_string(),
            }
            _save_state(s3, state)

        except Exception as e:
            _append_audit_error(
                s3,
                run_date,
                {
                    "ticker": ticker,
                    "vendor_symbol": symbol,
                    "window_start": str(start),
                    "window_end": str(end),
                    "error": str(e),
                    "ts": pendulum.now("UTC").to_iso8601_string(),
                },
            )
            state["tickers"][ticker] = {
                "status": "error",
                "error": str(e),
                "failed_at": pendulum.now("UTC").to_iso8601_string(),
            }
            _save_state(s3, state)
            # continue-on-error


with DAG(
    dag_id="asx200_ohlcv_backfill_to_raw",
    start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),
    schedule="@daily",  # temporarily scheduled; disable once complete
    catchup=False,
    max_active_runs=1,
    tags=["minio", "raw", "ohlcv", "asx", "backfill", "yfinance"],
) as dag:
    PythonOperator(
        task_id="fetch_and_write_raw_csvs",
        python_callable=fetch_and_write_raw_csvs,
    )
