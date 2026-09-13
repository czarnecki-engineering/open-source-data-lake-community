from __future__ import annotations

import numpy as np
import pandas as pd


PUBLICATION_EVIDENCE_REPOSITORY = "Marek-Czarnecki/return-predictability-australia"
PUBLICATION_EVIDENCE_BRANCH = "main"
PUBLICATION_CONFIRMATORY_SOURCE = "data/evidence/publication_final_primary_results.csv"
PUBLICATION_MECHANISM_SOURCE = "data/evidence/publication_trend_2x2_decomposition.csv"
PUBLICATION_EVIDENCE_COMMIT = "7b4bec52bcdf94691b2206c2049cfa6d69ba526e"


_PUBLICATION_PRIMARY_ROWS = (
    {
        "analysis_key": "trend_following",
        "publication_primary_metric": "net_excess_nav_difference",
        "publication_effect_estimate": 0.0008204009098994,
        "publication_adjusted_p_value": 1.0,
        "publication_supported_after_holm": False,
        "publication_sample_size": 24,
        "publication_sample_unit": "evaluation_folds",
        "publication_claim_label": "confirmatory_not_supported_after_holm",
    },
    {
        "analysis_key": "mean_reversion",
        "publication_primary_metric": "net_excess_nav_difference",
        "publication_effect_estimate": -0.5555920906637198,
        "publication_adjusted_p_value": 1.0,
        "publication_supported_after_holm": False,
        "publication_sample_size": 24,
        "publication_sample_unit": "evaluation_folds",
        "publication_claim_label": "confirmatory_not_supported_after_holm",
    },
    {
        "analysis_key": "pairs_trading",
        "publication_primary_metric": "net_excess_nav_difference",
        "publication_effect_estimate": -0.1068399483401674,
        "publication_adjusted_p_value": 1.0,
        "publication_supported_after_holm": False,
        "publication_sample_size": 24,
        "publication_sample_unit": "evaluation_folds",
        "publication_claim_label": "confirmatory_not_supported_after_holm",
    },
    {
        "analysis_key": "tax_loss_selling",
        "publication_primary_metric": "abnormal_net_return_difference",
        "publication_effect_estimate": 0.0249188080451322,
        "publication_adjusted_p_value": 0.6932,
        "publication_supported_after_holm": False,
        "publication_sample_size": 26,
        "publication_sample_unit": "calendar_years",
        "publication_claim_label": "confirmatory_not_supported_after_holm",
    },
)


def publication_primary_results() -> pd.DataFrame:
    """Return frozen aggregate publication results used for public-data comparison.

    Values are copied from the publication-facing reproducibility repository. They are
    aggregate evidence only; no licensed Norgate security-level data are embedded here.
    """
    frame = pd.DataFrame(_PUBLICATION_PRIMARY_ROWS)
    frame["publication_evidence_repository"] = PUBLICATION_EVIDENCE_REPOSITORY
    frame["publication_evidence_source"] = PUBLICATION_CONFIRMATORY_SOURCE
    return frame


def build_publication_comparison(public_inference: pd.DataFrame) -> pd.DataFrame:
    """Compare public Yahoo/STW inference with frozen publication aggregate evidence.

    This is a descriptive sensitivity comparison. It is not a pooled statistical test,
    an attempt to reproduce the licensed Norgate sample, or evidence that one dataset is
    a substitute for the other.
    """
    required = {
        "analysis_key",
        "effect_estimate",
        "adjusted_p_value",
        "reject_null_0_05",
        "sample_size",
        "sample_unit",
        "primary_metric",
        "claim_label",
    }
    missing = required.difference(public_inference.columns)
    if missing:
        raise ValueError(
            "Public inference is missing required columns: " + ", ".join(sorted(missing))
        )

    public = public_inference.loc[:, sorted(required)].copy()
    public = public.rename(
        columns={
            "effect_estimate": "public_effect_estimate",
            "adjusted_p_value": "public_adjusted_p_value",
            "reject_null_0_05": "public_supported_after_holm",
            "sample_size": "public_sample_size",
            "sample_unit": "public_sample_unit",
            "primary_metric": "public_primary_metric",
            "claim_label": "public_claim_label",
        }
    )
    public["public_supported_after_holm"] = public["public_supported_after_holm"].astype(bool)

    comparison = public.merge(
        publication_primary_results(),
        on="analysis_key",
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    if not comparison["_merge"].eq("both").all():
        missing_keys = comparison.loc[
            comparison["_merge"] != "both", ["analysis_key", "_merge"]
        ].to_dict("records")
        raise ValueError(f"Public/publication strategy keys do not match: {missing_keys}")
    comparison = comparison.drop(columns="_merge")

    comparison["public_effect_direction"] = comparison["public_effect_estimate"].map(_effect_direction)
    comparison["publication_effect_direction"] = comparison["publication_effect_estimate"].map(
        _effect_direction
    )
    comparison["effect_direction_changed"] = (
        comparison["public_effect_direction"] != comparison["publication_effect_direction"]
    )
    comparison["support_changed"] = (
        comparison["public_supported_after_holm"]
        != comparison["publication_supported_after_holm"]
    )
    comparison["comparison_role"] = "data_environment_sensitivity"
    comparison["interpretation_boundary"] = (
        "Different empirical conclusions are evidence of sensitivity to the data/design environment; "
        "the public Yahoo/STW analysis is not an attempted reproduction of the licensed Norgate sample."
    )
    return comparison.sort_values("analysis_key").reset_index(drop=True)


def publication_trend_mechanism_summary() -> pd.DataFrame:
    """Return the frozen seven-fold Norgate universe-treatment mechanism evidence."""
    return pd.DataFrame(
        [
            {
                "analysis": "trend_universe_2x2_decomposition",
                "matched_fold_count": 7,
                "mean_total_universe_treatment_effect_nav_difference": 0.153051485153,
                "mean_universe_composition_component_nav_difference": 0.151701286408,
                "mean_parameter_selection_component_nav_difference": 0.001350198745,
                "positive_universe_component_fold_count": 7,
                "parameter_selection_changed_fold_count": 5,
                "evidence_repository": PUBLICATION_EVIDENCE_REPOSITORY,
                "evidence_source": PUBLICATION_MECHANISM_SOURCE,
                "evidence_commit": PUBLICATION_EVIDENCE_COMMIT,
                "interpretation_boundary": (
                    "Controlled same-vendor Norgate evidence isolates historical universe treatment within "
                    "common Norgate security coverage; it does not fully explain Yahoo-versus-Norgate differences."
                ),
            }
        ]
    )


def public_vs_publication_data_design() -> pd.DataFrame:
    """Document material data/design differences that bound the comparison."""
    rows = (
        (
            "historical_universe",
            "Configured retrospective Yahoo/yFinance universe",
            "Historical point-in-time ASX 200 membership",
            "material_non_equivalence",
        ),
        (
            "security_identity",
            "Ticker-based public identity",
            "Permanent Norgate asset identity",
            "material_non_equivalence",
        ),
        (
            "delisting_and_history_coverage",
            "Public Yahoo coverage is incomplete and vendor-dependent",
            "Licensed Norgate security history including delisted coverage",
            "material_non_equivalence",
        ),
        (
            "benchmark",
            "STW.AX public ETF proxy",
            "Publication benchmark series",
            "proxy_difference",
        ),
        (
            "adjusted_price_convention",
            "Yahoo adjusted-price convention with documented fallback handling",
            "Norgate Total Return / publication price convention",
            "vendor_difference",
        ),
        (
            "sector_classification",
            "Current Yahoo-derived sector reference map",
            "Publication/Norgate research environment",
            "not_point_in_time_equivalent",
        ),
    )
    return pd.DataFrame(
        rows,
        columns=["dimension", "public_yahoo_stw", "publication_norgate", "comparison_status"],
    )


def _effect_direction(value: object) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return "missing"
    if np.isclose(float(numeric), 0.0):
        return "zero"
    return "positive" if float(numeric) > 0.0 else "negative"
