from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "runtime" / "shared" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from strategies.inference import (
    PRIMARY_TAX_LOSS_METRIC,
    PRIMARY_WALK_FORWARD_METRIC,
    bootstrap_mean_confidence_interval,
    build_public_primary_inference,
    holm_adjust,
    sign_flip_mean_p_value,
)


class PublicInferenceTests(unittest.TestCase):
    def test_bootstrap_mean_confidence_interval_is_deterministic(self):
        values = np.array([0.01, 0.02, 0.03], dtype=float)
        first = bootstrap_mean_confidence_interval(values)
        second = bootstrap_mean_confidence_interval(values)
        self.assertEqual(first, second)
        self.assertLessEqual(first[0], values.mean())
        self.assertGreaterEqual(first[1], values.mean())

    def test_sign_flip_exact_positive_sample(self):
        values = np.array([0.1, 0.2], dtype=float)
        p_value = sign_flip_mean_p_value(values, alternative="greater")
        self.assertAlmostEqual(p_value, 0.25)

    def test_sign_flip_uses_monte_carlo_for_large_sample(self):
        values = np.array([0.01] * 17, dtype=float)
        p_value = sign_flip_mean_p_value(values)
        self.assertGreaterEqual(p_value, 0.0)
        self.assertLessEqual(p_value, 1.0)

    def test_holm_adjust_matches_expected_step_down_values(self):
        adjusted = holm_adjust(pd.Series([0.01, 0.04, 0.20], index=["a", "b", "c"]))
        self.assertAlmostEqual(adjusted.loc["a"], 0.03)
        self.assertAlmostEqual(adjusted.loc["b"], 0.08)
        self.assertAlmostEqual(adjusted.loc["c"], 0.20)

    def test_primary_inference_builds_four_hypotheses(self):
        result = build_public_primary_inference(
            _fold_summary("trend_following", [0.01, 0.02, -0.005]),
            _fold_summary("mean_reversion", [0.02, 0.01, 0.00]),
            _fold_summary("pairs_trading", [0.03, -0.01, 0.02]),
            _tax_loss_events(),
        )
        primary = result.primary_inference.set_index("analysis_key")

        self.assertEqual(len(primary), 4)
        self.assertEqual(
            set(primary.index),
            {"trend_following", "mean_reversion", "pairs_trading", "tax_loss_selling"},
        )
        self.assertTrue((primary["multiple_testing_method"] == "holm").all())
        self.assertEqual(primary.loc["trend_following", "sample_unit"], "evaluation_folds")
        self.assertEqual(primary.loc["tax_loss_selling", "sample_unit"], "calendar_years")

    def test_tax_loss_primary_uses_complete_benchmark_adjusted_year_means(self):
        result = build_public_primary_inference(
            _fold_summary("trend_following", [0.0]),
            _fold_summary("mean_reversion", [0.0]),
            _fold_summary("pairs_trading", [0.0]),
            _tax_loss_events(),
        )
        years = result.tax_loss_year_effects.set_index("year")
        tax = result.primary_inference.loc[
            result.primary_inference["analysis_key"] == "tax_loss_selling"
        ].iloc[0]

        self.assertEqual(len(years), 2)
        self.assertAlmostEqual(years.loc[2020, "mean_abnormal_net_return_difference"], 0.15)
        self.assertAlmostEqual(years.loc[2021, "mean_abnormal_net_return_difference"], 0.30)
        self.assertEqual(int(years.loc[2020, "matched_observation_count"]), 2)
        self.assertEqual(int(tax["sample_size"]), 2)
        self.assertAlmostEqual(float(tax["effect_estimate"]), 0.225)
        self.assertEqual(tax["primary_metric"], PRIMARY_TAX_LOSS_METRIC)


def _fold_summary(strategy: str, values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "strategy": [strategy] * len(values),
            "fold_id": [f"fold_{index:02d}" for index in range(1, len(values) + 1)],
            "window_label": ["evaluation"] * len(values),
            PRIMARY_WALK_FORWARD_METRIC: values,
        }
    )


def _tax_loss_events() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2020, 2020, 2021, 2021],
            PRIMARY_TAX_LOSS_METRIC: [0.10, 0.20, 0.30, 9.99],
            "complete_event_window": [True, True, True, False],
            "complete_control_window": [True, True, True, False],
        }
    )


if __name__ == "__main__":
    unittest.main()
