from __future__ import annotations

from datetime import datetime, timedelta, timezone
import io
import os

import boto3
import pandas as pd
import pendulum
import yfinance as yf

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable


DATASET_ID = "market_ohlcv_daily"
EXCHANGE = "ASX"
CURRENCY = "AUD"

RAW_BUCKET = "raw"
MINIO_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")

ASX200_TICKERS_PATH = os.getenv(
    "ASX200_TICKERS_PATH",
    "/opt/airflow/config/asx200_tickers.csv",
)


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


#def _asx_tickers() -> list[str]:
#    # Set Airflow Variable ASX_TICKERS = "BHP,CBA,RIO,CSL" etc.
#    raw = Variable.get("ASX_TICKERS", default_var="BHP,CBA")
#    return [t.strip().upper() for t in raw.split(",") if t.strip()]



def _asx_tickers() -> list[str]:
    # Read tickers from mounted config/asx200_tickers.csv
    if not os.path.exists(ASX200_TICKERS_PATH):
        raise RuntimeError(
            f"Missing ASX200 tickers config at {ASX200_TICKERS_PATH}. "
            f"Ensure ./config/asx200_tickers.csv exists and is mounted into the Airflow container."
        )

    df = pd.read_csv(ASX200_TICKERS_PATH)

    # Support either a headered CSV with a 'ticker' column, or a single-column/no-header file.
    cols = [str(c).strip().lower() for c in df.columns.tolist()]
    if "ticker" in cols:
        series = df[df.columns[cols.index("ticker")]]
    else:
        # Treat first column as tickers if there's no 'ticker' header
        series = df.iloc[:, 0]

    tickers = (
        series.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"[^A-Z0-9]", "", regex=True)
        .tolist()
    )
    tickers = [t for t in tickers if t]

    # de-dupe, preserve order
    seen = set()
    out: list[str] = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            out.append(t)

    if not out:
        raise RuntimeError(f"ASX200 tickers config empty/invalid at {ASX200_TICKERS_PATH}")

    return out


def _vendor_symbol(ticker: str) -> str:
    # Yahoo Finance convention for ASX listings: <TICKER>.AX
    return f"{ticker}.AX"


def _raw_key(trade_date: str, ticker: str) -> str:
    return (
        f"tabular/{DATASET_ID}/exchange={EXCHANGE}/trade_date={trade_date}/"
        f"ticker={ticker}.csv"
    )


def fetch_and_write_raw_csvs(rolling_trading_days: int = 30) -> None:
    """
    For each ASX ticker:
      - download daily OHLCV for ~45 calendar days
      - take last N rows (N=rolling_trading_days)
      - write one CSV object per (ticker, trade_date) into raw/
    """
    s3 = _s3_client()

    # Fetch enough calendar days to usually cover 30 trading days
    end = datetime.now(timezone.utc).date()
    start = (end - timedelta(days=45))

    for ticker in _asx_tickers():
        symbol = _vendor_symbol(ticker)

        df = yf.download(
            tickers=symbol,
            start=str(start),
            end=str(end + timedelta(days=1)),
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if df is None or df.empty:
            continue

        # Standardise columns
        df = df.reset_index()
        df.columns = [c[0].lower() if isinstance(c, tuple) else str(c).lower() for c in df.columns]
        df.rename(columns={"date": "trade_date"}, inplace=True)

        # Ensure date string format
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date.astype(str)

        # Take last N trading days
        df = df.tail(rolling_trading_days)

        # Emit one CSV per day
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


with DAG(
    dag_id="asx200_ohlcv_daily_to_raw",
    start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),
    schedule="*/5 * * * *",  # adjust as desired; 5-min is safer than 1-min for Yahoo
    catchup=False,
    max_active_runs=1,
    tags=["minio", "raw", "ohlcv", "asx"],
) as dag:
    PythonOperator(
        task_id="fetch_and_write_raw_csvs",
        python_callable=fetch_and_write_raw_csvs,
        op_kwargs={"rolling_trading_days": 30},
    )
