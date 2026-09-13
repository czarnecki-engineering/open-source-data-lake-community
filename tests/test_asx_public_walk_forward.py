from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from runtime.shared.scripts.strategies.public_costs import build_public_fold_liquidity_tiers
from runtime.shared.scripts.strategies.public_walk_forward import (
    PUBLIC_STRATEGY_DEFINITIONS,
    PublicStrategyDefinition,
    _slice_strategy_history,
    run_public_walk_forward,
)
from runtime.shared.scripts.strategies.walk_forward import generate_walk_forward_folds


class PublicWalkForwardTests(unittest.TestCase):
    @staticmethod
    def _prices() -> pd.DataFrame:
        dates = pd.bdate_range("2000-03-31", "2004-06-30")
        frames = []
        for ticker, slope, dollar_volume in (("AAA", 0.0005, 10_000_000.0), ("BBB", 0.0002, 4_000_000.0), ("CCC", -0.0001, 1_000_000.0)):
            steps = np.arange(len(dates), dtype=float)
            frame = pd.DataFrame({"ticker": ticker, "trade_date": dates, "adj_close": 100.0 * np.exp(slope * steps),
                                  "dollar_volume": dollar_volume, "eligible_to_trade": True})
            frame["daily_return"] = frame["adj_close"].pct_change(fill_method=None)
            frames.append(frame)
        return pd.concat(frames, ignore_index=True)

    @staticmethod
    def _benchmark(prices: pd.DataFrame) -> pd.DataFrame:
        dates = pd.Index(sorted(prices["trade_date"].unique()))
        returns = pd.Series(0.0001, index=dates, dtype=float); returns.iloc[0] = np.nan
        return pd.DataFrame({"trade_date": dates, "benchmark_return": returns.to_numpy()})

    def test_generates_three_year_one_year_fold(self):
        folds = generate_walk_forward_folds(self._prices())
        self.assertGreaterEqual(len(folds), 1)
        self.assertEqual(folds[0].fold_id, "fold_01")
        self.assertLess(folds[0].formation_end, folds[0].evaluation_start)

    def test_public_liquidity_ranking_has_no_membership_dependency(self):
        prices = self._prices()
        result = build_public_fold_liquidity_tiers(prices, pd.Timestamp("2000-03-31"), pd.Timestamp("2003-03-31"))
        self.assertEqual(set(result.tier_map.index), {"AAA", "BBB", "CCC"})
        self.assertNotIn("member_of_universe", result.diagnostics.columns)

    def test_public_liquidity_ignores_rows_outside_formation_window(self):
        prices = self._prices()
        formation_start = pd.Timestamp("2001-01-02")
        formation_end = pd.Timestamp("2002-12-31")
        baseline = build_public_fold_liquidity_tiers(prices, formation_start, formation_end)

        modified = prices.copy()
        outside = (modified["trade_date"] < formation_start) | (modified["trade_date"] > formation_end)
        modified.loc[outside, "dollar_volume"] = 999_999_999_999.0
        result = build_public_fold_liquidity_tiers(modified, formation_start, formation_end)

        pd.testing.assert_series_equal(result.tier_map.sort_index(), baseline.tier_map.sort_index())
        pd.testing.assert_frame_equal(
            result.diagnostics.sort_values("ticker").reset_index(drop=True),
            baseline.diagnostics.sort_values("ticker").reset_index(drop=True),
        )

    def test_one_fold_trend_smoke_uses_public_contract(self):
        prices = self._prices(); benchmark = self._benchmark(prices)
        result = run_public_walk_forward("trend_following", prices, benchmark, max_folds=1)
        self.assertEqual(len(result.fold_table), 1)
        fold = result.fold_table.iloc[0]
        self.assertEqual(fold["identity_col"], "ticker")
        self.assertEqual(fold["eligibility_col"], "eligible_to_trade")
        self.assertFalse(result.fold_daily_results.empty)
        self.assertFalse(result.fold_summary.empty)
        self.assertFalse(result.liquidity_diagnostics.empty)

    def test_walk_forward_starts_at_benchmark_and_preserves_price_warmup(self):
        prices = self._prices()
        benchmark = self._benchmark(prices)
        benchmark.loc[benchmark["trade_date"] < pd.Timestamp("2000-07-03"), "benchmark_return"] = np.nan
        first_valid_benchmark_date = benchmark.loc[benchmark["benchmark_return"].notna(), "trade_date"].iloc[0]

        original = PUBLIC_STRATEGY_DEFINITIONS["trend_following"]
        runner_min_dates = []

        def recording_runner(strategy_prices: pd.DataFrame, **kwargs):
            runner_min_dates.append(strategy_prices["trade_date"].min())
            return original.runner(strategy_prices, **kwargs)

        PUBLIC_STRATEGY_DEFINITIONS["trend_following"] = PublicStrategyDefinition(
            recording_runner,
            original.min_history,
            original.parameter_grid,
        )
        try:
            result = run_public_walk_forward("trend_following", prices, benchmark, max_folds=1)
        finally:
            PUBLIC_STRATEGY_DEFINITIONS["trend_following"] = original

        self.assertEqual(result.fold_table.iloc[0]["formation_start"], first_valid_benchmark_date)
        self.assertTrue(runner_min_dates)
        self.assertTrue(all(date == prices["trade_date"].min() for date in runner_min_dates))

    def test_strategy_history_keeps_only_required_pre_window_warmup(self):
        dates = pd.bdate_range("1998-01-01", "2002-12-31")
        prices = pd.DataFrame({
            "ticker": np.repeat(["AAA", "BBB"], len(dates)),
            "trade_date": list(dates) * 2,
        })
        window_start = pd.Timestamp("2001-01-02")
        window_end = pd.Timestamp("2001-12-31")

        bounded = _slice_strategy_history(
            prices,
            window_start=window_start,
            window_end=window_end,
            warmup_observations=5,
        )

        expected_window_rows = prices.loc[
            (prices["trade_date"] >= window_start) & (prices["trade_date"] <= window_end)
        ]
        self.assertEqual(len(bounded), len(expected_window_rows) + 10)

        for ticker in ("AAA", "BBB"):
            ticker_full = prices.loc[prices["ticker"] == ticker].sort_values("trade_date")
            ticker_bounded = bounded.loc[bounded["ticker"] == ticker].sort_values("trade_date")
            expected_warmup = ticker_full.loc[ticker_full["trade_date"] < window_start].tail(5)["trade_date"].tolist()
            actual_warmup = ticker_bounded.loc[ticker_bounded["trade_date"] < window_start, "trade_date"].tolist()
            actual_window = ticker_bounded.loc[
                (ticker_bounded["trade_date"] >= window_start) & (ticker_bounded["trade_date"] <= window_end),
                "trade_date",
            ].tolist()
            expected_window = ticker_full.loc[
                (ticker_full["trade_date"] >= window_start) & (ticker_full["trade_date"] <= window_end),
                "trade_date",
            ].tolist()
            self.assertEqual(actual_warmup, expected_warmup)
            self.assertEqual(actual_window, expected_window)
            self.assertGreater(ticker_bounded["trade_date"].min(), ticker_full["trade_date"].min())
            self.assertLessEqual(ticker_bounded["trade_date"].max(), window_end)

    def test_one_fold_mean_reversion_smoke_uses_locked_grid(self):
        prices = self._prices(); benchmark = self._benchmark(prices)
        result = run_public_walk_forward("mean_reversion", prices, benchmark, max_folds=1)
        chosen = str(result.fold_table.iloc[0]["chosen_parameters"])
        self.assertIn("min_history=60", chosen)
        self.assertIn("cost_scenario=base", chosen)
        self.assertFalse(result.fold_daily_results.empty)


if __name__ == "__main__":
    unittest.main()
