from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "runtime" / "shared" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from strategies.public_tax_loss import (
    TAX_LOSS_SELECTION_OFFSET_DAYS,
    TAX_LOSS_UNIVERSE_TREATMENT,
    _strict_window_return,
    run_public_tax_loss_event_study,
)


class PublicTaxLossTests(unittest.TestCase):
    def test_strict_window_return_rejects_missing_observation(self):
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        series = pd.Series([0.01, np.nan, 0.02], index=dates)
        self.assertTrue(np.isnan(_strict_window_return(series, dates)))

    def test_bottom_decile_selection_uses_public_ticker_history(self):
        dates = pd.bdate_range("2019-01-01", periods=1000)
        rows = []
        for i in range(10):
            start = 100.0
            end = 40.0 if i == 0 else 100.0 + i * 5.0
            close = np.linspace(start, end, len(dates))
            rows.append(_ticker_frame(f"T{i:02d}", dates, close, 1_000_000.0 + i))
        prices = pd.concat(rows, ignore_index=True)
        benchmark = pd.DataFrame({"trade_date": dates, "benchmark_return": 0.0})

        result = run_public_tax_loss_event_study(prices, benchmark)

        self.assertFalse(result.event_study.empty)
        self.assertTrue(result.event_study["ticker"].eq("T00").any())
        self.assertEqual(result.summary.loc[0, "universe_treatment"], TAX_LOSS_UNIVERSE_TREATMENT)
        self.assertEqual(result.summary.loc[0, "selection_offset_days"], TAX_LOSS_SELECTION_OFFSET_DAYS)
        self.assertEqual(TAX_LOSS_SELECTION_OFFSET_DAYS, 11)

    def test_symmetric_cost_leaves_event_control_difference_unchanged(self):
        dates = pd.bdate_range("2019-01-01", periods=1000)
        prices = pd.concat(
            [
                _ticker_frame("AAA", dates, np.linspace(200.0, 80.0, len(dates)), 5_000_000.0),
                _ticker_frame("BBB", dates, np.linspace(100.0, 130.0, len(dates)), 1_000_000.0),
            ],
            ignore_index=True,
        )
        benchmark = pd.DataFrame({"trade_date": dates, "benchmark_return": 0.0})

        result = run_public_tax_loss_event_study(prices, benchmark)
        complete = result.event_study.loc[
            result.event_study["complete_event_window"]
            & result.event_study["complete_control_window"]
        ]

        self.assertFalse(complete.empty)
        np.testing.assert_allclose(
            complete["return_difference"].to_numpy(dtype=float),
            complete["net_return_difference"].to_numpy(dtype=float),
            atol=1e-12,
        )

    def test_benchmark_adjustment_is_applied(self):
        dates = pd.bdate_range("2019-01-01", periods=1000)
        prices = pd.concat(
            [
                _ticker_frame("AAA", dates, np.linspace(200.0, 80.0, len(dates)), 5_000_000.0),
                _ticker_frame("BBB", dates, np.linspace(100.0, 130.0, len(dates)), 1_000_000.0),
            ],
            ignore_index=True,
        )
        benchmark = pd.DataFrame({"trade_date": dates, "benchmark_return": 0.001})

        result = run_public_tax_loss_event_study(prices, benchmark)
        complete = result.event_study.dropna(subset=["abnormal_net_event_window_return"])

        self.assertFalse(complete.empty)
        np.testing.assert_allclose(
            complete["abnormal_net_event_window_return"].to_numpy(dtype=float),
            complete["net_event_window_return"].to_numpy(dtype=float)
            - complete["benchmark_event_window_return"].to_numpy(dtype=float),
            atol=1e-12,
        )

    def test_summary_requires_complete_security_and_benchmark_windows(self):
        dates = pd.bdate_range("2019-01-01", periods=1000)
        prices = pd.concat(
            [
                _ticker_frame("AAA", dates, np.linspace(200.0, 80.0, len(dates)), 5_000_000.0),
                _ticker_frame("BBB", dates, np.linspace(100.0, 130.0, len(dates)), 1_000_000.0),
            ],
            ignore_index=True,
        )
        benchmark = pd.DataFrame({"trade_date": dates, "benchmark_return": 0.0})
        benchmark.loc[benchmark.index[500], "benchmark_return"] = np.nan

        result = run_public_tax_loss_event_study(prices, benchmark)
        expected = result.event_study.loc[
            result.event_study["complete_event_window"]
            & result.event_study["complete_control_window"]
        ]

        self.assertEqual(
            int(result.summary.loc[0, "complete_matched_observation_count"]),
            len(expected),
        )
        self.assertEqual(
            int(result.summary.loc[0, "year_count"]),
            expected["year"].nunique(),
        )

    def test_public_method_does_not_require_membership_column(self):
        dates = pd.bdate_range("2019-01-01", periods=1000)
        prices = pd.concat(
            [
                _ticker_frame("AAA", dates, np.linspace(200.0, 80.0, len(dates)), 5_000_000.0),
                _ticker_frame("BBB", dates, np.linspace(100.0, 130.0, len(dates)), 1_000_000.0),
            ],
            ignore_index=True,
        )
        self.assertNotIn("member_of_universe", prices.columns)
        benchmark = pd.DataFrame({"trade_date": dates, "benchmark_return": 0.0})

        result = run_public_tax_loss_event_study(prices, benchmark, max_years=1)

        self.assertIsNotNone(result.summary)


def _ticker_frame(
    ticker: str,
    dates: pd.DatetimeIndex,
    close: np.ndarray,
    dollar_volume: float,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ticker": ticker,
            "trade_date": dates,
            "adj_close": close,
            "daily_return": pd.Series(close).pct_change(fill_method=None).to_numpy(),
            "dollar_volume": dollar_volume,
        }
    )


if __name__ == "__main__":
    unittest.main()
