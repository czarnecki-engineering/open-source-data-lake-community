from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_PATH = REPO_ROOT / "runtime" / "shared" / "scripts"
if str(SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_PATH))

from asx200_ohlcv_local import (  # noqa: E402
    CsvPriceStore,
    IngestionConfig,
    MinioPriceStore,
    PriceIngestionService,
    TickerIngestionResult,
)


DEFAULT_CONFIG_PATH = REPO_ROOT / "runtime" / "shared" / "config" / "asx" / "asx_data_request.json"


def make_config(
    *,
    start_date: str = "2026-03-29",
    end_date: str = "2026-04-27",
    request_id: str = "req-001",
) -> IngestionConfig:
    return IngestionConfig.from_dict(
        {
            "request_id": request_id,
            "dataset_id": "market_ohlcv_daily_v2",
            "exchange": "ASX",
            "currency": "AUD",
            "ticker_list": ["BHP"],
            "vendor_symbol_map": {"BHP": "BHP.AX"},
            "earliest_start_date": start_date,
            "lookback_days": None,
            "end_date": end_date,
        }
    )


def make_price_frame(*dates: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": trade_date,
                "open": 1.0 + index / 10,
                "high": 2.0 + index / 10,
                "low": 0.5 + index / 10,
                "close": 1.5 + index / 10,
                "volume": 100 + index * 10,
            }
            for index, trade_date in enumerate(dates)
        ]
    )


class IngestionConfigTests(unittest.TestCase):
    def test_load_main_config(self) -> None:
        config_path = Path(os.environ.get("TEST_INGESTION_CONFIG_PATH", str(DEFAULT_CONFIG_PATH)))
        config = IngestionConfig.from_file(config_path)

        self.assertEqual(config.exchange, "ASX")
        self.assertEqual(config.currency, "AUD")
        self.assertGreater(len(config.ticker_list), 0)
        first_ticker = config.ticker_list[0]
        self.assertEqual(config.vendor_symbol_for(first_ticker), config.vendor_symbol_map[first_ticker])

    def test_resolve_horizon_from_explicit_dates(self) -> None:
        config = make_config()

        start_date, end_date = config.resolve_horizon()

        self.assertEqual(start_date, "2026-03-29")
        self.assertEqual(end_date, "2026-04-27")


class CsvPriceStoreTests(unittest.TestCase):
    def test_save_prices_writes_expected_csv(self) -> None:
        config = make_config()
        frame = make_price_frame("2026-03-30")

        with tempfile.TemporaryDirectory() as tmp_dir:
            store = CsvPriceStore(Path(tmp_dir))
            output_path = store.save_prices(
                config=config,
                ticker_code="BHP",
                vendor_symbol="BHP.AX",
                frame=frame,
            )

            self.assertTrue(output_path.exists())
            saved = pd.read_csv(output_path)
            self.assertEqual(saved.loc[0, "ticker"], "BHP")
            self.assertEqual(saved.loc[0, "vendor_symbol"], "BHP.AX")
            self.assertEqual(saved.loc[0, "trade_date"], "2026-03-30")

    def test_inspect_existing_csv_returns_expected_metadata(self) -> None:
        config = make_config()
        frame = make_price_frame("2026-03-30", "2026-03-31")

        with tempfile.TemporaryDirectory() as tmp_dir:
            store = CsvPriceStore(Path(tmp_dir))
            store.save_prices(config=config, ticker_code="BHP", vendor_symbol="BHP.AX", frame=frame)

            metadata = store.inspect_existing_csv(config=config, ticker_code="BHP")

            self.assertEqual(metadata.ticker_code, "BHP")
            self.assertEqual(metadata.row_count, 2)
            self.assertEqual(metadata.first_date, "2026-03-30")
            self.assertEqual(metadata.last_date, "2026-03-31")


class FakeClient:
    def __init__(self, responses: dict[tuple[str, str, str], pd.DataFrame]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, str]] = []

    def download_daily_prices(
        self,
        *,
        vendor_symbol: str,
        start_date: str,
        end_date: str,
        allow_empty: bool = False,
    ) -> pd.DataFrame:
        self.calls.append((vendor_symbol, start_date, end_date))
        frame = self.responses.get((vendor_symbol, start_date, end_date))
        if frame is None:
            if allow_empty:
                return pd.DataFrame(columns=["trade_date", "open", "high", "low", "close", "volume"])
            raise AssertionError(f"Unexpected download request: {(vendor_symbol, start_date, end_date)}")
        return frame.copy()


class PriceIngestionServiceTests(unittest.TestCase):
    def assert_result_status(self, result: TickerIngestionResult, *, status: str, row_count: int) -> None:
        self.assertEqual(result.status, status)
        self.assertEqual(result.row_count, row_count)

    def test_ingest_skips_existing_ticker_csv(self) -> None:
        config = make_config()
        existing_frame = make_price_frame("2026-03-29", "2026-04-27")

        with tempfile.TemporaryDirectory() as tmp_dir:
            store = CsvPriceStore(Path(tmp_dir))
            store.save_prices(config=config, ticker_code="BHP", vendor_symbol="BHP.AX", frame=existing_frame)
            client = FakeClient({})

            result = PriceIngestionService(client=client, store=store).ingest(config)

            self.assertEqual(client.calls, [])
            self.assertEqual(result.ticker_count, 1)
            self.assert_result_status(result.outputs[0], status="skipped_existing", row_count=2)

    def test_ingest_downloads_and_writes_missing_ticker_csv(self) -> None:
        config = make_config()
        downloaded = make_price_frame("2026-03-30")

        with tempfile.TemporaryDirectory() as tmp_dir:
            store = CsvPriceStore(Path(tmp_dir))
            client = FakeClient({("BHP.AX", "2026-03-29", "2026-04-27"): downloaded})

            result = PriceIngestionService(client=client, store=store).ingest(config)

            self.assertEqual(client.calls, [("BHP.AX", "2026-03-29", "2026-04-27")])
            self.assert_result_status(result.outputs[0], status="downloaded", row_count=1)
            self.assertTrue(Path(result.outputs[0].output_path).exists())

    def test_ingest_skips_existing_csv_when_calendar_start_is_weekend(self) -> None:
        config = make_config(start_date="2026-06-21", end_date="2026-07-20", request_id="req-002")
        existing_frame = make_price_frame("2026-06-22", "2026-07-20")

        with tempfile.TemporaryDirectory() as tmp_dir:
            store = CsvPriceStore(Path(tmp_dir))
            store.save_prices(config=config, ticker_code="BHP", vendor_symbol="BHP.AX", frame=existing_frame)
            client = FakeClient({})

            result = PriceIngestionService(client=client, store=store).ingest(config)

            self.assertEqual(client.calls, [])
            self.assert_result_status(result.outputs[0], status="skipped_existing", row_count=2)

    def test_ingest_extends_existing_csv_with_missing_leading_range(self) -> None:
        config = make_config(start_date="2026-03-27")
        existing_frame = make_price_frame("2026-03-30", "2026-04-27")
        leading_frame = make_price_frame("2026-03-27")

        with tempfile.TemporaryDirectory() as tmp_dir:
            store = CsvPriceStore(Path(tmp_dir))
            store.save_prices(config=config, ticker_code="BHP", vendor_symbol="BHP.AX", frame=existing_frame)
            client = FakeClient({("BHP.AX", "2026-03-27", "2026-03-29"): leading_frame})

            result = PriceIngestionService(client=client, store=store).ingest(config)

            self.assertEqual(client.calls, [("BHP.AX", "2026-03-27", "2026-03-29")])
            self.assert_result_status(result.outputs[0], status="updated_existing", row_count=3)
            self.assertEqual(result.outputs[0].first_date, "2026-03-27")
            self.assertEqual(result.outputs[0].last_date, "2026-04-27")

    def test_ingest_extends_existing_csv_with_missing_trailing_range(self) -> None:
        config = make_config()
        existing_frame = make_price_frame("2026-03-29")
        trailing_frame = make_price_frame("2026-03-30")

        with tempfile.TemporaryDirectory() as tmp_dir:
            store = CsvPriceStore(Path(tmp_dir))
            store.save_prices(config=config, ticker_code="BHP", vendor_symbol="BHP.AX", frame=existing_frame)
            client = FakeClient({("BHP.AX", "2026-03-30", "2026-04-27"): trailing_frame})

            result = PriceIngestionService(client=client, store=store).ingest(config)

            self.assertEqual(client.calls, [("BHP.AX", "2026-03-30", "2026-04-27")])
            self.assert_result_status(result.outputs[0], status="updated_existing", row_count=2)

    def test_ingest_extends_existing_csv_on_both_edges_and_deduplicates(self) -> None:
        config = make_config(start_date="2026-03-27")
        existing_frame = make_price_frame("2026-03-30")
        leading_frame = make_price_frame("2026-03-27", "2026-03-30")
        trailing_frame = make_price_frame("2026-04-27")

        with tempfile.TemporaryDirectory() as tmp_dir:
            store = CsvPriceStore(Path(tmp_dir))
            store.save_prices(config=config, ticker_code="BHP", vendor_symbol="BHP.AX", frame=existing_frame)
            client = FakeClient(
                {
                    ("BHP.AX", "2026-03-27", "2026-03-29"): leading_frame,
                    ("BHP.AX", "2026-03-31", "2026-04-27"): trailing_frame,
                }
            )

            result = PriceIngestionService(client=client, store=store).ingest(config)

            self.assertEqual(
                client.calls,
                [("BHP.AX", "2026-03-27", "2026-03-29"), ("BHP.AX", "2026-03-31", "2026-04-27")],
            )
            self.assert_result_status(result.outputs[0], status="updated_existing", row_count=3)
            self.assertEqual(result.outputs[0].first_date, "2026-03-27")
            self.assertEqual(result.outputs[0].last_date, "2026-04-27")

    def test_ingest_remembers_unavailable_leading_history(self) -> None:
        config = make_config(start_date="2026-03-27")
        existing_frame = make_price_frame("2026-03-30", "2026-04-27")

        with tempfile.TemporaryDirectory() as tmp_dir:
            store = CsvPriceStore(Path(tmp_dir))
            store.save_prices(config=config, ticker_code="BHP", vendor_symbol="BHP.AX", frame=existing_frame)
            first_client = FakeClient({})

            first_result = PriceIngestionService(client=first_client, store=store).ingest(config)

            self.assertEqual(first_client.calls, [("BHP.AX", "2026-03-27", "2026-03-29")])
            self.assert_result_status(first_result.outputs[0], status="updated_existing", row_count=2)
            metadata = store.load_ingestion_metadata(config=config, ticker_code="BHP")
            self.assertEqual(metadata["known_earliest_trade_date"], "2026-03-30")

            second_client = FakeClient({})
            second_result = PriceIngestionService(client=second_client, store=store).ingest(config)

            self.assertEqual(second_client.calls, [])
            self.assert_result_status(second_result.outputs[0], status="skipped_existing", row_count=2)


class FakeNotFoundError(Exception):
    def __init__(self) -> None:
        self.response = {
            "Error": {"Code": "NoSuchKey"},
            "ResponseMetadata": {"HTTPStatusCode": 404},
        }


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
        if (Bucket, Key) not in self.objects:
            raise FakeNotFoundError()
        return {}

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, io.BytesIO]:
        try:
            payload = self.objects[(Bucket, Key)]
        except KeyError as exc:
            raise FakeNotFoundError() from exc
        return {"Body": io.BytesIO(payload)}

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str,
    ) -> dict[str, object]:
        self.objects[(Bucket, Key)] = Body
        return {}


class MinioPriceStoreTests(unittest.TestCase):
    def test_minio_store_round_trips_prices_and_metadata(self) -> None:
        config = make_config()
        s3 = FakeS3()
        store = MinioPriceStore(s3, bucket="raw")
        frame = make_price_frame("2026-03-30", "2026-03-31")

        output_path = store.save_prices(
            config=config,
            ticker_code="BHP",
            vendor_symbol="BHP.AX",
            frame=frame,
        )
        store.save_ingestion_metadata(
            config=config,
            ticker_code="BHP",
            metadata={"known_earliest_trade_date": "2026-03-30"},
        )

        self.assertEqual(
            output_path,
            "s3://raw/tabular/market_ohlcv_daily_v2/exchange=ASX/ticker=BHP.csv",
        )
        self.assertTrue(store.has_prices(config=config, ticker_code="BHP"))
        saved = store.read_existing_prices(config=config, ticker_code="BHP")
        self.assertEqual(saved["trade_date"].tolist(), ["2026-03-30", "2026-03-31"])
        metadata = store.load_ingestion_metadata(config=config, ticker_code="BHP")
        self.assertEqual(metadata["known_earliest_trade_date"], "2026-03-30")

    def test_minio_store_reports_missing_objects_without_swallowing_other_errors(self) -> None:
        config = make_config()
        store = MinioPriceStore(FakeS3(), bucket="raw")

        self.assertFalse(store.has_prices(config=config, ticker_code="BHP"))
        self.assertEqual(store.load_ingestion_metadata(config=config, ticker_code="BHP"), {})

        class BrokenS3(FakeS3):
            def head_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
                raise RuntimeError("MinIO unavailable")

        with self.assertRaisesRegex(RuntimeError, "MinIO unavailable"):
            MinioPriceStore(BrokenS3(), bucket="raw").has_prices(config=config, ticker_code="BHP")

    def test_canonical_service_runs_against_minio_store(self) -> None:
        config = make_config()
        s3 = FakeS3()
        store = MinioPriceStore(s3, bucket="raw")
        downloaded = make_price_frame("2026-03-30")
        client = FakeClient({("BHP.AX", "2026-03-29", "2026-04-27"): downloaded})

        result = PriceIngestionService(client=client, store=store).ingest(config)

        self.assert_result(result.outputs[0], status="downloaded", row_count=1)
        self.assertTrue(store.has_prices(config=config, ticker_code="BHP"))
        metadata = store.load_ingestion_metadata(config=config, ticker_code="BHP")
        self.assertEqual(metadata["ticker"], "BHP")
        self.assertEqual(metadata["vendor_symbol"], "BHP.AX")

    def assert_result(self, result: TickerIngestionResult, *, status: str, row_count: int) -> None:
        self.assertEqual(result.status, status)
        self.assertEqual(result.row_count, row_count)


if __name__ == "__main__":
    unittest.main()
