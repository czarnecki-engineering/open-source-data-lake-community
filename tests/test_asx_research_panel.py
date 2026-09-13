from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_PATH = REPO_ROOT / "runtime" / "shared" / "scripts"
if str(SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_PATH))

from asx_research_panel import (  # noqa: E402
    build_asx_research_panel,
    summarize_asx_research_panel_quality,
)


class AsxResearchPanelTests(unittest.TestCase):
    def test_builds_public_research_contract(self) -> None:
        curated = pd.DataFrame(
            [
                {"ticker": "BBB", "trade_date": "2026-01-02", "close": 20.0, "adj_close": 20.0, "volume": 200},
                {"ticker": "AAA", "trade_date": "2026-01-03", "close": 12.0, "adj_close": 11.0, "volume": 110},
                {"ticker": "AAA", "trade_date": "2026-01-02", "close": 10.0, "adj_close": 10.0, "volume": 100},
                {"ticker": "BBB", "trade_date": "2026-01-03", "close": 19.0, "adj_close": 18.0, "volume": 180},
            ]
        )

        panel = build_asx_research_panel(curated, min_history=2)

        self.assertEqual(panel["ticker"].tolist(), ["AAA", "AAA", "BBB", "BBB"])
        self.assertEqual(panel["history_observation_count"].tolist(), [1, 2, 1, 2])
        self.assertEqual(panel["eligible_to_trade"].tolist(), [False, True, False, True])
        self.assertAlmostEqual(panel.loc[1, "daily_return"], 0.10)
        self.assertAlmostEqual(panel.loc[3, "daily_return"], -0.10)
        self.assertEqual(panel.loc[0, "dollar_volume"], 1000.0)
        self.assertEqual(panel.loc[2, "dollar_volume"], 4000.0)
        self.assertNotIn("member_of_universe", panel.columns)
        self.assertEqual(panel.attrs["universe_treatment"], "public_yahoo_retrospective")
        self.assertIn("adj_close", panel.attrs["return_price_rule"])
        self.assertEqual(panel.attrs["liquidity_proxy"], "close_x_volume")

    def test_uses_close_for_liquidity_and_returns_when_adjusted_close_is_negative(self) -> None:
        curated = pd.DataFrame(
            [
                {
                    "ticker": "AAA",
                    "trade_date": "2026-01-02",
                    "close": 2.0,
                    "adj_close": -0.5,
                    "volume": 100,
                },
                {
                    "ticker": "AAA",
                    "trade_date": "2026-01-03",
                    "close": 2.5,
                    "adj_close": -0.4,
                    "volume": 120,
                },
            ]
        )

        panel = build_asx_research_panel(curated)

        self.assertEqual(panel["dollar_volume"].tolist(), [200.0, 300.0])
        self.assertGreaterEqual(panel["dollar_volume"].min(), 0.0)
        self.assertAlmostEqual(panel.loc[1, "daily_return"], 0.25)

    def test_falls_back_to_close_across_negative_to_positive_adjusted_transition(self) -> None:
        curated = pd.DataFrame(
            [
                {"ticker": "AAA", "trade_date": "2026-01-02", "close": 5.40, "adj_close": -0.00000063, "volume": 100},
                {"ticker": "AAA", "trade_date": "2026-01-03", "close": 5.20, "adj_close": -0.00000065, "volume": 100},
                {"ticker": "AAA", "trade_date": "2026-01-04", "close": 5.10, "adj_close": 5.10, "volume": 100},
                {"ticker": "AAA", "trade_date": "2026-01-05", "close": 5.20, "adj_close": 5.40, "volume": 100},
            ]
        )

        panel = build_asx_research_panel(curated)

        self.assertAlmostEqual(panel.loc[1, "daily_return"], 5.20 / 5.40 - 1)
        self.assertAlmostEqual(panel.loc[2, "daily_return"], 5.10 / 5.20 - 1)
        self.assertAlmostEqual(panel.loc[3, "daily_return"], 5.40 / 5.10 - 1)

    def test_quality_summary_reports_anomalies_without_mutating_panel(self) -> None:
        curated = pd.DataFrame(
            [
                {"ticker": "AAA", "trade_date": "2026-01-02", "close": 2.0, "adj_close": -0.5, "volume": 100},
                {"ticker": "AAA", "trade_date": "2026-01-03", "close": 2.5, "adj_close": -0.4, "volume": 120},
                {"ticker": "BBB", "trade_date": "2026-01-02", "close": 1.0, "adj_close": 1.0, "volume": 10},
                {"ticker": "BBB", "trade_date": "2026-01-03", "close": 12.5, "adj_close": 12.5, "volume": 10},
            ]
        )
        panel = build_asx_research_panel(curated)
        original = panel.copy(deep=True)

        summary = summarize_asx_research_panel_quality(panel)

        self.assertEqual(summary["rows"], 4)
        self.assertEqual(summary["tickers"], 2)
        self.assertEqual(summary["non_positive_adjusted_price_rows"], 2)
        self.assertEqual(summary["adjusted_price_fallback_rows"], 2)
        self.assertEqual(summary["invalid_or_negative_dollar_volume_rows"], 0)
        self.assertEqual(summary["extreme_return_rows"], 1)
        self.assertEqual(summary["date_min"], pd.Timestamp("2026-01-02"))
        self.assertEqual(summary["date_max"], pd.Timestamp("2026-01-03"))
        pd.testing.assert_frame_equal(panel, original)

    def test_quality_summary_rejects_invalid_thresholds(self) -> None:
        curated = pd.DataFrame(
            [{"ticker": "AAA", "trade_date": "2026-01-02", "close": 1.0, "adj_close": 1.0, "volume": 1}]
        )
        panel = build_asx_research_panel(curated)
        with self.assertRaisesRegex(ValueError, "extreme_return_floor"):
            summarize_asx_research_panel_quality(panel, extreme_return_floor=2.0, extreme_return_ceiling=1.0)

    def test_rejects_duplicate_ticker_dates(self) -> None:
        curated = pd.DataFrame(
            [
                {"ticker": "AAA", "trade_date": "2026-01-02", "close": 10.0, "adj_close": 10.0, "volume": 100},
                {"ticker": "AAA", "trade_date": "2026-01-02", "close": 11.0, "adj_close": 11.0, "volume": 110},
            ]
        )
        with self.assertRaisesRegex(ValueError, "duplicate ticker/trade_date"):
            build_asx_research_panel(curated)

    def test_rejects_missing_required_columns(self) -> None:
        curated = pd.DataFrame([{"ticker": "AAA", "trade_date": "2026-01-02"}])
        with self.assertRaisesRegex(ValueError, "adj_close"):
            build_asx_research_panel(curated)


if __name__ == "__main__":
    unittest.main()
