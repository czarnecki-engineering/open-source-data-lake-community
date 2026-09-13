from __future__ import annotations

import sys
import unittest
from pathlib import Path

DAGS_DIR = Path(__file__).resolve().parents[1] / "runtime" / "shared" / "dags"
if str(DAGS_DIR) not in sys.path:
    sys.path.insert(0, str(DAGS_DIR))

from asx_sector_map_runtime import (
    SECTOR_MAP_DATASET_ID,
    build_sector_map,
    normalize_yahoo_sector,
    sector_map_object_key,
)


class AsxSectorMapTests(unittest.TestCase):
    def test_normalizes_yahoo_sector_labels_to_gics_names(self):
        self.assertEqual(normalize_yahoo_sector("Basic Materials"), "Materials")
        self.assertEqual(normalize_yahoo_sector("Consumer Cyclical"), "Consumer Discretionary")
        self.assertEqual(normalize_yahoo_sector("Technology"), "Information Technology")
        self.assertEqual(normalize_yahoo_sector("Utilities"), "Utilities")

    def test_build_sector_map_preserves_every_configured_ticker_and_status(self):
        config = {
            "ticker_list": ["AAA", "BBB"],
            "vendor_symbol_map": {"AAA": "AAA.AX", "BBB": "BBB.AX"},
        }

        def info_loader(symbol: str):
            if symbol == "AAA.AX":
                return {
                    "longName": "AAA Limited",
                    "sector": "Financial Services",
                    "industry": "Banks - Regional",
                }
            return {"longName": "BBB Limited"}

        result = build_sector_map(
            config,
            info_loader,
            classification_date="2026-09-12",
        )

        self.assertEqual(result["ticker"].tolist(), ["AAA", "BBB"])
        self.assertEqual(result.loc[0, "sector"], "Financials")
        self.assertEqual(result.loc[0, "status"], "resolved")
        self.assertEqual(result.loc[1, "sector"], "")
        self.assertEqual(result.loc[1, "status"], "unresolved")
        self.assertTrue((result["dataset_id"] == SECTOR_MAP_DATASET_ID).all())
        self.assertTrue((result["exchange"] == "ASX").all())

    def test_sector_map_object_uses_curated_reference_dataset_convention(self):
        self.assertEqual(
            sector_map_object_key(),
            "tabular/asx_ticker_sector_map_v1/exchange=ASX/asx_ticker_sector_map.parquet",
        )

    def test_build_sector_map_rejects_missing_vendor_symbol(self):
        config = {
            "ticker_list": ["AAA", "BBB"],
            "vendor_symbol_map": {"AAA": "AAA.AX"},
        }
        with self.assertRaisesRegex(ValueError, "Missing vendor symbols for: BBB"):
            build_sector_map(config, lambda _: {}, classification_date="2026-09-12")


if __name__ == "__main__":
    unittest.main()
