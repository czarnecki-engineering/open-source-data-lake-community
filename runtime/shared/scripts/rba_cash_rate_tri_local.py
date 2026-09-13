from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from urllib.request import urlopen

import pandas as pd

DEFAULT_RBA_F1_CSV_URL = "https://www.rba.gov.au/statistics/tables/csv/f1-data.csv"


@dataclass(frozen=True)
class RbaCashRateTriConfig:
    source_url: str = DEFAULT_RBA_F1_CSV_URL
    start_date: str | None = None
    end_date: str | None = None


def download_rba_csv_text(source_url: str = DEFAULT_RBA_F1_CSV_URL) -> str:
    with urlopen(source_url) as response:  # nosec B310
        return response.read().decode("utf-8-sig")


def extract_tri_frame(csv_text: str) -> pd.DataFrame:
    rows = list(csv.reader(io.StringIO(csv_text)))
    if not rows:
        raise RuntimeError("RBA F1 CSV response was empty.")

    title_row = next((row for row in rows if row and row[0].strip() == "Title"), None)
    if title_row is None:
        raise RuntimeError("Could not locate the Title row in the RBA F1 CSV.")

    tri_index = next((index for index, value in enumerate(title_row) if value.strip() == "Total Return Index"), None)
    if tri_index is None:
        raise RuntimeError("Could not locate the 'Total Return Index' column in the RBA F1 CSV.")

    publication_row = next((row for row in rows if row and row[0].strip() == "Publication date"), None)
    publication_date = publication_row[tri_index].strip() if publication_row and len(publication_row) > tri_index else ""

    data_rows = []
    for row in rows:
        if not row:
            continue
        date_token = row[0].strip()
        if not _looks_like_rba_date(date_token):
            continue
        tri_value = row[tri_index].strip() if len(row) > tri_index else ""
        if not tri_value or tri_value == "N/A":
            continue
        data_rows.append({
            "trade_date": pd.to_datetime(date_token, format="%d-%b-%Y", errors="raise"),
            "rba_cash_rate_tri": float(tri_value),
            "publication_date": publication_date,
            "source": "RBA statistical table F1",
            "source_url": DEFAULT_RBA_F1_CSV_URL,
        })

    if not data_rows:
        raise RuntimeError("No TRI rows were extracted from the RBA F1 CSV.")

    frame = pd.DataFrame(data_rows).sort_values("trade_date").reset_index(drop=True)
    frame["risk_free_return"] = pd.to_numeric(frame["rba_cash_rate_tri"], errors="coerce").pct_change(fill_method=None)
    return frame[["trade_date", "rba_cash_rate_tri", "risk_free_return", "publication_date", "source", "source_url"]]


def apply_date_filter(frame: pd.DataFrame, start_date: str | None = None, end_date: str | None = None) -> pd.DataFrame:
    filtered = frame.copy()
    filtered["trade_date"] = pd.to_datetime(filtered["trade_date"], errors="coerce")
    if start_date is not None:
        filtered = filtered.loc[filtered["trade_date"] >= pd.Timestamp(start_date)].copy()
    if end_date is not None:
        filtered = filtered.loc[filtered["trade_date"] <= pd.Timestamp(end_date)].copy()
    filtered = filtered.reset_index(drop=True)
    if filtered.empty:
        raise RuntimeError("The filtered RBA TRI frame is empty.")
    return filtered


def load_rba_cash_rate_tri(config: RbaCashRateTriConfig = RbaCashRateTriConfig()) -> pd.DataFrame:
    frame = extract_tri_frame(download_rba_csv_text(config.source_url))
    return apply_date_filter(frame, config.start_date, config.end_date)


def _looks_like_rba_date(value: str) -> bool:
    if len(value) != 11:
        return False
    try:
        pd.to_datetime(value, format="%d-%b-%Y", errors="raise")
    except Exception:
        return False
    return True
