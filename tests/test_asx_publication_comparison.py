from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "runtime" / "shared" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from strategies.publication_comparison import (
    build_publication_comparison,
    public_vs_publication_data_design,
    publication_primary_results,
    publication_trend_mechanism_summary,
)


class PublicationComparisonTests(unittest.TestCase):
    def test_publication_primary_results_are_frozen_four_strategy_evidence(self):
        publication = publication_primary_results().set_index("analysis_key")

        self.assertEqual(len(publication), 4)
        self.assertAlmostEqual(
            float(publication.loc["trend_following", "publication_effect_estimate"]),
            0.0008204009098994,
        )
        self.assertAlmostEqual(
            float(publication.loc["tax_loss_selling", "publication_adjusted_p_value"]),
            0.6932,
        )
        self.assertFalse(publication["publication_supported_after_holm"].any())

    def test_comparison_identifies_support_changes_without_pooling_results(self):
        comparison = build_publication_comparison(_public_inference()).set_index("analysis_key")

        self.assertTrue(bool(comparison.loc["trend_following", "support_changed"]))
        self.assertTrue(bool(comparison.loc["tax_loss_selling", "support_changed"]))
        self.assertFalse(bool(comparison.loc["mean_reversion", "support_changed"]))
        self.assertFalse(bool(comparison.loc["pairs_trading", "support_changed"]))
        self.assertTrue((comparison["comparison_role"] == "data_environment_sensitivity").all())

    def test_comparison_reports_effect_direction_changes(self):
        comparison = build_publication_comparison(_public_inference()).set_index("analysis_key")

        self.assertEqual(comparison.loc["trend_following", "public_effect_direction"], "positive")
        self.assertEqual(comparison.loc["trend_following", "publication_effect_direction"], "positive")
        self.assertFalse(bool(comparison.loc["trend_following", "effect_direction_changed"]))
        self.assertEqual(comparison.loc["mean_reversion", "public_effect_direction"], "positive")
        self.assertEqual(comparison.loc["mean_reversion", "publication_effect_direction"], "negative")
        self.assertTrue(bool(comparison.loc["mean_reversion", "effect_direction_changed"]))

    def test_trend_mechanism_summary_preserves_bounded_publication_claim(self):
        mechanism = publication_trend_mechanism_summary().iloc[0]

        self.assertEqual(int(mechanism["matched_fold_count"]), 7)
        self.assertAlmostEqual(
            float(mechanism["mean_total_universe_treatment_effect_nav_difference"]),
            0.153051485153,
        )
        self.assertAlmostEqual(
            float(mechanism["mean_universe_composition_component_nav_difference"]),
            0.151701286408,
        )
        self.assertEqual(int(mechanism["positive_universe_component_fold_count"]), 7)
        self.assertIn("does not fully explain", mechanism["interpretation_boundary"])

    def test_data_design_table_marks_publication_non_equivalence(self):
        design = public_vs_publication_data_design().set_index("dimension")

        self.assertEqual(
            design.loc["historical_universe", "comparison_status"],
            "material_non_equivalence",
        )
        self.assertIn("point-in-time", design.loc["historical_universe", "publication_norgate"])
        self.assertEqual(design.loc["benchmark", "comparison_status"], "proxy_difference")

    def test_comparison_rejects_missing_strategy_keys(self):
        with self.assertRaisesRegex(ValueError, "strategy keys do not match"):
            build_publication_comparison(
                _public_inference().loc[lambda frame: frame["analysis_key"] != "pairs_trading"]
            )


def _public_inference() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "analysis_key": [
                "trend_following",
                "mean_reversion",
                "pairs_trading",
                "tax_loss_selling",
            ],
            "effect_estimate": [0.131658, 0.251020, -0.089582, 0.089720],
            "adjusted_p_value": [0.004333, 0.128662, 0.991409, 0.038086],
            "reject_null_0_05": [True, False, False, True],
            "sample_size": [16, 16, 16, 10],
            "sample_unit": [
                "evaluation_folds",
                "evaluation_folds",
                "evaluation_folds",
                "calendar_years",
            ],
            "primary_metric": [
                "net_excess_nav_difference",
                "net_excess_nav_difference",
                "net_excess_nav_difference",
                "abnormal_net_return_difference",
            ],
            "claim_label": [
                "confirmatory_supported_after_holm",
                "confirmatory_not_supported_after_holm",
                "confirmatory_not_supported_after_holm",
                "confirmatory_supported_after_holm",
            ],
        }
    )


if __name__ == "__main__":
    unittest.main()
