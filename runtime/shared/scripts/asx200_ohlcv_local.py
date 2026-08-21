from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol

import pandas as pd


UTC = timezone.utc
DEFAULT_CONFIG_PATH = Path("/opt/airflow/config/asx/asx_data_request.json")
DEFAULT_OUTPUT_ROOT = Path("/opt/airflow/data/raw")


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def latest_available_trading_day(reference_date: date | None = None) -> date:
    current = reference_date or datetime.now(UTC).date()
    while current.weekday() >= 5:
        current -= timedelta(days=1)
    return current


def earliest_available_trading_day(reference_date: date) -> date:
    current = reference_date
    while current.weekday() >= 5:
        current += timedelta(days=1)
    return current


class DownloadClient(Protocol):
    def __call__(
        self,
        *,
        tickers: str,
        start: str,
        end: str,
        interval: str,
        auto_adjust: bool,
        progress: bool,
        threads: bool,
    ) -> pd.DataFrame: ...


@dataclass(frozen=True)
class IngestionConfig:
    request_id: str
    dataset_id: str
    exchange: str
    currency: str
    ticker_list: list[str]
    vendor_symbol_map: dict[str, str]
    earliest_start_date: str | None
    lookback_days: int | None
    end_date: str | None

    @classmethod
    def from_file(cls, path: Path) -> "IngestionConfig":
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return cls.from_dict(payload)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "IngestionConfig":
        for field_name in ("request_id", "dataset_id", "exchange", "currency"):
            value = payload.get(field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Config field '{field_name}' must be a non-empty string.")

        ticker_list = payload.get("ticker_list")
        if not isinstance(ticker_list, list) or not ticker_list:
            raise ValueError("Config field 'ticker_list' must be a non-empty list.")
        normalized_tickers = [str(ticker).strip().upper() for ticker in ticker_list if str(ticker).strip()]
        if len(normalized_tickers) != len(ticker_list) or len(set(normalized_tickers)) != len(normalized_tickers):
            raise ValueError("Config field 'ticker_list' must contain unique non-empty ticker codes.")

        vendor_symbol_map = payload.get("vendor_symbol_map")
        if not isinstance(vendor_symbol_map, dict):
            raise ValueError("Config field 'vendor_symbol_map' must be a JSON object.")
        normalized_map = {str(key).strip().upper(): str(value).strip().upper() for key, value in vendor_symbol_map.items()}
        for ticker_code in normalized_tickers:
            if ticker_code not in normalized_map or not normalized_map[ticker_code]:
                raise ValueError(f"Config field 'vendor_symbol_map' is missing ticker '{ticker_code}'.")

        earliest_start_date = payload.get("earliest_start_date")
        lookback_days = payload.get("lookback_days")
        end_date_value = payload.get("end_date")

        if earliest_start_date is not None:
            parse_iso_date(str(earliest_start_date))
        if lookback_days is not None and (not isinstance(lookback_days, int) or lookback_days <= 0):
            raise ValueError("Config field 'lookback_days' must be a positive integer or null.")
        if earliest_start_date is None and lookback_days is None:
            raise ValueError("Config requires either 'earliest_start_date' or 'lookback_days'.")
        if end_date_value is not None:
            parse_iso_date(str(end_date_value))

        return cls(
            request_id=str(payload["request_id"]).strip(),
            dataset_id=str(payload["dataset_id"]).strip(),
            exchange=str(payload["exchange"]).strip(),
            currency=str(payload["currency"]).strip(),
            ticker_list=normalized_tickers,
            vendor_symbol_map=normalized_map,
            earliest_start_date=str(earliest_start_date) if earliest_start_date is not None else None,
            lookback_days=lookback_days,
            end_date=str(end_date_value) if end_date_value is not None else None,
        )

    def vendor_symbol_for(self, ticker_code: str) -> str:
        return self.vendor_symbol_map[ticker_code.strip().upper()]

    def resolve_horizon(self, current_date: date | None = None) -> tuple[str, str]:
        end_value = parse_iso_date(self.end_date) if self.end_date else latest_available_trading_day(current_date)
        if self.earliest_start_date:
            start_value = parse_iso_date(self.earliest_start_date)
        else:
            assert self.lookback_days is not None
            start_value = end_value - timedelta(days=self.lookback_days - 1)
        if end_value < start_value:
            raise ValueError("Resolved date horizon has end_date before start_date.")
        return start_value.isoformat(), end_value.isoformat()


class YahooFinanceClient:
    def __init__(self, downloader: DownloadClient | None = None) -> None:
        if downloader is None:
            try:
                import yfinance
            except ModuleNotFoundError as exc:  # pragma: no cover
                raise ModuleNotFoundError(
                    "Missing dependency 'yfinance'. The Team Airflow runtime now expects "
                    "ingestion libraries to be present in the prebuilt Airflow image. "
                    "Rebuild the Compose/K8s Airflow image before running this script."
                ) from exc
            downloader = yfinance.download
        self._downloader = downloader

    @staticmethod
    def _empty_daily_prices() -> pd.DataFrame:
        return pd.DataFrame(columns=["trade_date", "open", "high", "low", "close", "volume"])

    def download_daily_prices(
        self,
        *,
        vendor_symbol: str,
        start_date: str,
        end_date: str,
        allow_empty: bool = False,
    ) -> pd.DataFrame:
        frame = self._downloader(
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
                return self._empty_daily_prices()
            raise RuntimeError(f"No rows returned for {vendor_symbol} in window {start_date}..{end_date}.")
        return self._normalize(frame)

    @staticmethod
    def _normalize(downloaded: pd.DataFrame) -> pd.DataFrame:
        frame = downloaded.reset_index()
        frame.columns = [column[0].lower() if isinstance(column, tuple) else str(column).lower() for column in frame.columns]
        if "date" in frame.columns:
            frame.rename(columns={"date": "trade_date"}, inplace=True)
        elif "datetime" in frame.columns:
            frame.rename(columns={"datetime": "trade_date"}, inplace=True)
        elif "index" in frame.columns:
            frame.rename(columns={"index": "trade_date"}, inplace=True)
        if "trade_date" not in frame.columns:
            raise RuntimeError(f"Expected trade_date column after reset_index(); got {frame.columns.tolist()}.")
        frame["trade_date"] = pd.to_datetime(frame["trade_date"], errors="coerce").dt.date
        frame = frame.dropna(subset=["trade_date"]).sort_values("trade_date")
        if frame.empty:
            raise RuntimeError("No valid trade_date rows remained after normalization.")
        frame["trade_date"] = frame["trade_date"].astype(str)
        return frame


class CsvPriceStore:
    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root

    def ensure_structure(self) -> None:
        self.output_root.mkdir(parents=True, exist_ok=True)

    def output_path(self, config: IngestionConfig, ticker_code: str) -> Path:
        return (
            self.output_root
            / config.dataset_id
            / f"exchange={config.exchange}"
            / f"ticker={ticker_code}.csv"
        )

    @staticmethod
    def _normalize_trade_dates(frame: pd.DataFrame) -> pd.DataFrame:
        if "trade_date" not in frame.columns:
            raise RuntimeError("Expected trade_date column in ticker price data.")
        normalized = frame.copy()
        normalized["trade_date"] = pd.to_datetime(normalized["trade_date"], errors="coerce").dt.date
        normalized = normalized.dropna(subset=["trade_date"]).sort_values("trade_date")
        if normalized.empty:
            raise RuntimeError("No valid trade_date rows remained after normalization.")
        normalized["trade_date"] = normalized["trade_date"].astype(str)
        return normalized

    @staticmethod
    def _metadata_from_frame(*, ticker_code: str, output_path: Path, frame: pd.DataFrame) -> "ExistingTickerCsvMetadata":
        return ExistingTickerCsvMetadata(
            ticker_code=ticker_code,
            output_path=str(output_path),
            row_count=len(frame),
            first_date=str(frame["trade_date"].iloc[0]),
            last_date=str(frame["trade_date"].iloc[-1]),
        )

    def read_existing_prices(self, *, config: IngestionConfig, ticker_code: str) -> pd.DataFrame:
        output_path = self.output_path(config, ticker_code)
        frame = pd.read_csv(output_path)
        if frame.empty:
            raise RuntimeError(f"Existing CSV for {ticker_code} at {output_path} is empty.")
        return self._normalize_trade_dates(frame)

    def inspect_existing_csv(self, *, config: IngestionConfig, ticker_code: str) -> "ExistingTickerCsvMetadata":
        output_path = self.output_path(config, ticker_code)
        frame = self.read_existing_prices(config=config, ticker_code=ticker_code)
        return self._metadata_from_frame(ticker_code=ticker_code, output_path=output_path, frame=frame)

    def merge_frames(self, existing_frame: pd.DataFrame, *additional_frames: pd.DataFrame) -> pd.DataFrame:
        frames = [existing_frame, *[frame for frame in additional_frames if not frame.empty]]
        combined = pd.concat(frames, ignore_index=True, sort=False)
        combined = self._normalize_trade_dates(combined)
        return combined.drop_duplicates(subset=["trade_date"], keep="last").sort_values("trade_date").reset_index(drop=True)

    def save_prices(self, *, config: IngestionConfig, ticker_code: str, vendor_symbol: str, frame: pd.DataFrame) -> Path:
        output_path = self.output_path(config, ticker_code)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._normalize_trade_dates(frame)
        payload["ticker"] = ticker_code
        payload["vendor_symbol"] = vendor_symbol
        payload["dataset_id"] = config.dataset_id
        payload["exchange"] = config.exchange
        payload["currency"] = config.currency
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
            "adj close" if "adj close" in payload.columns else None,
            "volume",
        ]
        payload = payload[[column for column in ordered_columns if column is not None and column in payload.columns]]
        payload.to_csv(output_path, index=False)
        return output_path


@dataclass(frozen=True)
class ExistingTickerCsvMetadata:
    ticker_code: str
    output_path: str
    row_count: int
    first_date: str
    last_date: str


@dataclass(frozen=True)
class TickerIngestionResult:
    ticker_code: str
    vendor_symbol: str
    status: str
    row_count: int
    output_path: str
    first_date: str | None = None
    last_date: str | None = None


@dataclass(frozen=True)
class IngestionRunResult:
    request_id: str
    start_date: str
    end_date: str
    ticker_count: int
    outputs: list[TickerIngestionResult]


class PriceIngestionService:
    def __init__(self, client: YahooFinanceClient, store: CsvPriceStore) -> None:
        self.client = client
        self.store = store

    @staticmethod
    def _previous_day(value: str) -> str:
        return (parse_iso_date(value) - timedelta(days=1)).isoformat()

    @staticmethod
    def _next_day(value: str) -> str:
        return (parse_iso_date(value) + timedelta(days=1)).isoformat()

    def ingest(self, config: IngestionConfig, *, current_date: date | None = None) -> IngestionRunResult:
        self.store.ensure_structure()
        start_date, end_date = config.resolve_horizon(current_date)
        requested_first_trade_date = earliest_available_trading_day(parse_iso_date(start_date)).isoformat()
        requested_last_trade_date = latest_available_trading_day(parse_iso_date(end_date)).isoformat()
        outputs: list[TickerIngestionResult] = []

        for ticker_code in config.ticker_list:
            vendor_symbol = config.vendor_symbol_for(ticker_code)
            output_path = self.store.output_path(config, ticker_code)
            if output_path.exists():
                existing_frame = self.store.read_existing_prices(config=config, ticker_code=ticker_code)
                metadata = self.store.inspect_existing_csv(config=config, ticker_code=ticker_code)
                missing_before = requested_first_trade_date < metadata.first_date
                missing_after = requested_last_trade_date > metadata.last_date
                if not missing_before and not missing_after:
                    print(f"Skipping {ticker_code}: existing CSV already covers {start_date}..{end_date}")
                    outputs.append(
                        TickerIngestionResult(
                            ticker_code=ticker_code,
                            vendor_symbol=vendor_symbol,
                            status="skipped_existing",
                            row_count=metadata.row_count,
                            output_path=metadata.output_path,
                            first_date=metadata.first_date,
                            last_date=metadata.last_date,
                        )
                    )
                    continue

                leading_frame = YahooFinanceClient._empty_daily_prices()
                trailing_frame = YahooFinanceClient._empty_daily_prices()
                if missing_before:
                    leading_end_date = self._previous_day(metadata.first_date)
                    print(
                        f"Updating {ticker_code}: downloading missing leading range "
                        f"{requested_first_trade_date}..{leading_end_date}"
                    )
                    leading_frame = self.client.download_daily_prices(
                        vendor_symbol=vendor_symbol,
                        start_date=requested_first_trade_date,
                        end_date=leading_end_date,
                        allow_empty=True,
                    )
                if missing_after:
                    trailing_start_date = self._next_day(metadata.last_date)
                    print(
                        f"Updating {ticker_code}: downloading missing trailing range "
                        f"{trailing_start_date}..{requested_last_trade_date}"
                    )
                    trailing_frame = self.client.download_daily_prices(
                        vendor_symbol=vendor_symbol,
                        start_date=trailing_start_date,
                        end_date=requested_last_trade_date,
                        allow_empty=True,
                    )

                merged_frame = self.store.merge_frames(existing_frame, leading_frame, trailing_frame)
                output_path = self.store.save_prices(
                    config=config,
                    ticker_code=ticker_code,
                    vendor_symbol=vendor_symbol,
                    frame=merged_frame,
                )
                merged_metadata = self.store._metadata_from_frame(
                    ticker_code=ticker_code,
                    output_path=output_path,
                    frame=merged_frame,
                )
                print(f"Updated {ticker_code}: wrote merged CSV to {output_path}")
                outputs.append(
                    TickerIngestionResult(
                        ticker_code=ticker_code,
                        vendor_symbol=vendor_symbol,
                        status="updated_existing",
                        row_count=merged_metadata.row_count,
                        output_path=merged_metadata.output_path,
                        first_date=merged_metadata.first_date,
                        last_date=merged_metadata.last_date,
                    )
                )
                continue

            frame = self.client.download_daily_prices(
                vendor_symbol=vendor_symbol,
                start_date=start_date,
                end_date=end_date,
            )
            output_path = self.store.save_prices(
                config=config,
                ticker_code=ticker_code,
                vendor_symbol=vendor_symbol,
                frame=frame,
            )
            print(f"Downloaded {ticker_code}: wrote CSV to {output_path}")
            outputs.append(
                TickerIngestionResult(
                    ticker_code=ticker_code,
                    vendor_symbol=vendor_symbol,
                    status="downloaded",
                    row_count=len(frame),
                    output_path=str(output_path),
                    first_date=str(frame["trade_date"].iloc[0]),
                    last_date=str(frame["trade_date"].iloc[-1]),
                )
            )

        return IngestionRunResult(
            request_id=config.request_id,
            start_date=start_date,
            end_date=end_date,
            ticker_count=len(outputs),
            outputs=outputs,
        )


def run_ingestion(
    *,
    config_path: Path | str | None = None,
    output_root: Path | str | None = None,
    current_date: date | None = None,
) -> IngestionRunResult:
    resolved_config_path = Path(config_path or DEFAULT_CONFIG_PATH).expanduser().resolve()
    resolved_output_root = Path(output_root or DEFAULT_OUTPUT_ROOT).expanduser().resolve()
    config = IngestionConfig.from_file(resolved_config_path)
    service = PriceIngestionService(
        client=YahooFinanceClient(),
        store=CsvPriceStore(resolved_output_root),
    )
    return service.ingest(config, current_date=current_date)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download ASX200 daily prices from yFinance to local CSV files.")
    parser.add_argument("--config", default="config/asx_data_request.json", help="Path to the ingestion config JSON file.")
    parser.add_argument("--output-root", default="data/raw", help="Folder where ticker CSV files will be written.")
    parser.add_argument("--current-date", default=None, help="Optional ISO date used to resolve rolling horizons.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current_date = parse_iso_date(args.current_date) if args.current_date else None
    result = run_ingestion(
        config_path=args.config,
        output_root=args.output_root,
        current_date=current_date,
    )
    print(json.dumps(asdict(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
