from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "runtime" / "shared" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from strategies.pairs_trading import build_pair_return_panel, select_pairs_in_window
from strategies.public_pairs import (
    PAIR_BORROW_FINANCING,
    PAIR_CAPITAL_NORMALIZATION,
    PAIR_CANDIDATE_SOURCE,
    PAIR_COST_APPLICATION,
    PAIR_UNIVERSE_TREATMENT,
    run_public_pairs_walk_forward,
)


class PublicPairsTests(unittest.TestCase):
    def test_pair_return_uses_one_day_lag_normalization_and_weighted_cost(self):
        dates = pd.date_range("2024-01-01", periods=6, freq="D")
        prices = pd.concat(
            [
                pd.DataFrame({
                    "ticker": "LEFT",
                    "trade_date": dates,
                    "adj_close": [100.0, 100.0, 100.0, 80.0, 88.0, 88.0],
                    "eligible_to_trade": True,
                }),
                pd.DataFrame({
                    "ticker": "RIGHT",
                    "trade_date": dates,
                    "adj_close": [100.0] * 6,
                    "eligible_to_trade": True,
                }),
            ],
            ignore_index=True,
        )
        selected = pd.DataFrame([{
            "pair_id": "LEFT_RIGHT",
            "left_identity": "LEFT",
            "right_identity": "RIGHT",
            "left_ticker": "LEFT",
            "right_ticker": "RIGHT",
            "hedge_ratio": 1.0,
            "intercept": 0.0,
            "left_liquidity_tier": "high",
            "right_liquidity_tier": "lower",
        }])

        panel = build_pair_return_panel(
            prices,
            selected,
            spread_window=2,
            entry_z=0.5,
            exit_z=0.1,
            cost_scenario="base",
        ).set_index("trade_date")

        self.assertEqual(float(panel.loc[dates[4], "gross_exposure_denominator"]), 2.0)
        self.assertAlmostEqual(float(panel.loc[dates[4], "pair_gross_return"]), 0.05, places=10)
        self.assertAlmostEqual(float(panel.loc[dates[4], "pair_turnover_cost_bps"]), 22.5, places=10)

    def test_pair_selection_prefers_same_sector_candidates(self):
        dates = pd.bdate_range("2020-01-01", periods=120)
        x = np.arange(len(dates), dtype=float)
        base = 100.0 * np.exp(0.001 * x)
        prices = pd.concat([
            pd.DataFrame({
                "ticker": "AAA.AX", "trade_date": dates, "adj_close": base,
                "dollar_volume": 5_000_000.0, "eligible_to_trade": True,
            }),
            pd.DataFrame({
                "ticker": "BBB.AX", "trade_date": dates, "adj_close": base * 1.02,
                "dollar_volume": 4_000_000.0, "eligible_to_trade": True,
            }),
            pd.DataFrame({
                "ticker": "CCC.AX", "trade_date": dates, "adj_close": base * 0.98,
                "dollar_volume": 3_000_000.0, "eligible_to_trade": True,
            }),
        ], ignore_index=True)
        tiers = pd.Series({"AAA.AX": "high", "BBB.AX": "medium", "CCC.AX": "lower"}, dtype="string")
        sectors = pd.DataFrame({
            "ticker": ["AAA.AX", "BBB.AX", "CCC.AX"],
            "sector": ["Financials", "Financials", "Materials"],
        })

        pair_table, selected = select_pairs_in_window(
            prices,
            top_liquid_tickers=3,
            top_pair_count=1,
            liquidity_tier_map=tiers,
            sector_map=sectors,
        )

        self.assertEqual(len(pair_table), 1)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected.iloc[0]["candidate_source"], "same_sector")
        self.assertEqual(selected.iloc[0]["left_sector"], "Financials")
        self.assertEqual(selected.iloc[0]["right_sector"], "Financials")
        self.assertTrue(bool(selected.iloc[0]["passed_cointegration"]))

    def test_pair_selection_uses_sector_fallback_when_same_sector_pool_is_insufficient(self):
        dates = pd.bdate_range("2020-01-01", periods=120)
        x = np.arange(len(dates), dtype=float)
        base = 100.0 * np.exp(0.001 * x)
        prices = pd.concat([
            pd.DataFrame({
                "ticker": "AAA.AX", "trade_date": dates, "adj_close": base,
                "dollar_volume": 5_000_000.0, "eligible_to_trade": True,
            }),
            pd.DataFrame({
                "ticker": "BBB.AX", "trade_date": dates, "adj_close": base * 1.02,
                "dollar_volume": 4_000_000.0, "eligible_to_trade": True,
            }),
        ], ignore_index=True)
        sectors = pd.DataFrame({
            "ticker": ["AAA.AX", "BBB.AX"],
            "sector": ["Financials", "Materials"],
        })

        pair_table, selected = select_pairs_in_window(
            prices,
            top_liquid_tickers=2,
            top_pair_count=1,
            sector_map=sectors,
        )

        self.assertEqual(len(pair_table), 1)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected.iloc[0]["candidate_source"], "sector_fallback")

    def test_one_fold_public_pairs_records_method_boundaries(self):
        dates = pd.bdate_range("2008-01-02", "2012-06-29")
        steps = np.arange(len(dates), dtype=float)
        base = 100.0 * np.exp(0.0003 * steps)
        prices = pd.concat([
            pd.DataFrame({
                "ticker": "AAA.AX", "trade_date": dates, "adj_close": base,
                "daily_return": pd.Series(base).pct_change(fill_method=None).to_numpy(),
                "dollar_volume": 5_000_000.0, "eligible_to_trade": True,
            }),
            pd.DataFrame({
                "ticker": "BBB.AX", "trade_date": dates, "adj_close": base * 1.02,
                "daily_return": pd.Series(base * 1.02).pct_change(fill_method=None).to_numpy(),
                "dollar_volume": 4_000_000.0, "eligible_to_trade": True,
            }),
        ], ignore_index=True)
        sector_map = pd.DataFrame({
            "ticker": ["AAA.AX", "BBB.AX"],
            "sector": ["Financials", "Financials"],
        })
        benchmark = pd.DataFrame({
            "trade_date": dates,
            "benchmark_return": np.r_[np.nan, np.repeat(0.0001, len(dates) - 1)],
        })
        risk_free = pd.DataFrame({
            "trade_date": dates,
            "risk_free_return": np.r_[np.nan, np.repeat(0.00005, len(dates) - 1)],
        })

        result = run_public_pairs_walk_forward(
            prices,
            benchmark,
            sector_map,
            risk_free,
            max_folds=1,
            top_liquid_tickers=2,
            top_pair_count=1,
        )

        self.assertEqual(len(result.fold_table), 1)
        fold = result.fold_table.iloc[0]
        self.assertEqual(fold["capital_normalization"], PAIR_CAPITAL_NORMALIZATION)
        self.assertEqual(fold["pair_cost_application"], PAIR_COST_APPLICATION)
        self.assertEqual(fold["borrow_financing"], PAIR_BORROW_FINANCING)
        self.assertEqual(fold["universe_treatment"], PAIR_UNIVERSE_TREATMENT)
        self.assertEqual(fold["candidate_source"], PAIR_CANDIDATE_SOURCE)
        self.assertEqual(int(fold["selected_pair_count"]), 1)
        self.assertFalse(result.fold_daily_results.empty)
        self.assertFalse(result.fold_summary.empty)
        self.assertFalse(result.pair_diagnostics.empty)
        self.assertEqual(result.pair_diagnostics.iloc[0]["candidate_source"], "same_sector")


if __name__ == "__main__":
    unittest.main()
