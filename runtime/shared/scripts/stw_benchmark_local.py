from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

MISSING_YFINANCE_MESSAGE = (
    "Missing dependency 'yfinance'. Install it before running STW benchmark ingestion."
)


@dataclass(frozen=True)
class STWIngestionConfig:
    vendor_symbol: str = "STW.AX"
    start_date: str | None = None
    end_date: str | None = None


def _load_yfinance():
    try:
        import yfinance as yf
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise ModuleNotFoundError(MISSING_YFINANCE_MESSAGE) from exc
    return yf


def resolve_date_window(panel: pd.DataFrame, start_date: str | None = None, end_date: str | None = None) -> tuple[str, str]:
    if "trade_date" not in panel.columns:
        raise ValueError("Panel must include trade_date.")
    trade_dates = pd.to_datetime(panel["trade_date"], errors="coerce").dropna()
    if trade_dates.empty:
        raise ValueError("Panel contains no valid trade_date values.")
    resolved_start = start_date or str(trade_dates.min().date())
    resolved_end = end_date or str(trade_dates.max().date())
    if pd.Timestamp(resolved_end) < pd.Timestamp(resolved_start):
        raise ValueError("Resolved STW date window has end_date before start_date.")
    return resolved_start, resolved_end


def download_stw_history(config: STWIngestionConfig) -> pd.DataFrame:
    if not config.start_date or not config.end_date:
        raise ValueError("STWIngestionConfig requires start_date and end_date for download.")
    yf = _load_yfinance()
    downloaded = yf.download(
        tickers=config.vendor_symbol,
        start=config.start_date,
        end=(pd.Timestamp(config.end_date) + pd.Timedelta(days=1)).date().isoformat(),
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if downloaded is None or downloaded.empty:
        raise RuntimeError(
            f"No rows returned for {config.vendor_symbol} in window {config.start_date}..{config.end_date}."
        )
    return normalize_downloaded_history(downloaded, config.vendor_symbol)


def normalize_downloaded_history(downloaded: pd.DataFrame, vendor_symbol: str = "STW.AX") -> pd.DataFrame:
    frame = downloaded.reset_index()
    frame.columns = [column[0].lower() if isinstance(column, tuple) else str(column).lower() for column in frame.columns]
    if "date" in frame.columns:
        frame.rename(columns={"date": "trade_date"}, inplace=True)
    elif "datetime" in frame.columns:
        frame.rename(columns={"datetime": "trade_date"}, inplace=True)
    elif "index" in frame.columns:
        frame.rename(columns={"index": "trade_date"}, inplace=True)
    required = {"trade_date", "open", "high", "low", "close", "adj close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise RuntimeError("Downloaded STW history is missing expected Yahoo Finance columns: " + ", ".join(sorted(missing)))

    normalized = frame[["trade_date", "open", "high", "low", "close", "adj close", "volume"]].copy()
    normalized.rename(columns={"adj close": "adj_close"}, inplace=True)
    normalized["trade_date"] = pd.to_datetime(normalized["trade_date"], errors="coerce")
    normalized = normalized.dropna(subset=["trade_date"]).sort_values("trade_date").reset_index(drop=True)
    if normalized.empty:
        raise RuntimeError("No valid trade_date rows remained after normalization.")
    normalized["vendor_symbol"] = str(vendor_symbol).strip().upper()
    normalized["stw_return"] = pd.to_numeric(normalized["adj_close"], errors="coerce").pct_change(fill_method=None)
    normalized["benchmark_return"] = normalized["stw_return"]
    normalized["source"] = "Yahoo Finance via yfinance"
    return normalized[[
        "trade_date", "vendor_symbol", "open", "high", "low", "close", "adj_close", "volume", "stw_return", "benchmark_return", "source"
    ]]
