from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np
import pandas as pd


CONFIRMATORY_FAMILY_ID = "confirmatory_primary_family"
HOLM_ADJUSTMENT_METHOD = "holm"
PRIMARY_WALK_FORWARD_METRIC = "net_excess_nav_difference"
PRIMARY_TAX_LOSS_METRIC = "abnormal_net_return_difference"
PRIMARY_ALTERNATIVE = "greater"
WALK_FORWARD_STRATEGIES = ("trend_following", "mean_reversion", "pairs_trading")


@dataclass(frozen=True)
class PublicInferenceResult:
    primary_inference: pd.DataFrame
    tax_loss_year_effects: pd.DataFrame


def bootstrap_mean_confidence_interval(
    values: np.ndarray,
    alpha: float = 0.05,
    bootstrap_reps: int = 10000,
) -> tuple[float, float]:
    clean = np.asarray(values, dtype=float)
    clean = clean[np.isfinite(clean)]
    if clean.size == 0:
        return np.nan, np.nan
    rng = np.random.default_rng(0)
    samples = rng.choice(clean, size=(bootstrap_reps, clean.size), replace=True)
    sample_means = samples.mean(axis=1)
    return (
        float(np.quantile(sample_means, alpha / 2)),
        float(np.quantile(sample_means, 1.0 - alpha / 2)),
    )


def sign_flip_mean_p_value(
    values: np.ndarray,
    alternative: str = "greater",
    exact_max_size: int = 16,
    monte_carlo_draws: int = 20000,
) -> float:
    clean = np.asarray(values, dtype=float)
    clean = clean[np.isfinite(clean)]
    if clean.size == 0:
        return np.nan

    observed = float(clean.mean())
    if clean.size <= exact_max_size:
        sign_matrix = np.array(list(product([-1.0, 1.0], repeat=clean.size)), dtype=float)
    else:
        rng = np.random.default_rng(0)
        sign_matrix = rng.choice(
            np.array([-1.0, 1.0], dtype=float),
            size=(monte_carlo_draws, clean.size),
            replace=True,
        )
    permuted = (sign_matrix * clean).mean(axis=1)

    if alternative == "greater":
        return float(np.mean(permuted >= observed - 1e-15))
    if alternative == "less":
        return float(np.mean(permuted <= observed + 1e-15))
    if alternative == "two-sided":
        return float(np.mean(np.abs(permuted) >= abs(observed) - 1e-15))
    raise ValueError(f"Unsupported alternative: {alternative}")


def holm_adjust(p_values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(p_values, errors="coerce")
    valid = numeric.dropna()
    result = pd.Series(np.nan, index=numeric.index, dtype=float)
    if valid.empty:
        return result

    ordered = valid.sort_values(kind="mergesort")
    m = len(ordered)
    running_max = 0.0
    for position, (index, value) in enumerate(ordered.items(), start=1):
        adjusted_value = min(1.0, (m - position + 1) * float(value))
        running_max = max(running_max, adjusted_value)
        result.loc[index] = running_max
    return result


def build_public_primary_inference(
    trend_summary: pd.DataFrame,
    mean_reversion_summary: pd.DataFrame,
    pairs_summary: pd.DataFrame,
    tax_loss_event_study: pd.DataFrame,
) -> PublicInferenceResult:
    rows = [
        _walk_forward_row("trend_following", trend_summary),
        _walk_forward_row("mean_reversion", mean_reversion_summary),
        _walk_forward_row("pairs_trading", pairs_summary),
    ]

    tax_complete = _complete_tax_loss_events(tax_loss_event_study)
    tax_loss_year_effects = (
        tax_complete.groupby("year", observed=True)[PRIMARY_TAX_LOSS_METRIC]
        .agg(
            mean_abnormal_net_return_difference="mean",
            matched_observation_count="size",
        )
        .reset_index()
        .sort_values("year")
        .reset_index(drop=True)
    )
    rows.append(_tax_loss_row(tax_loss_year_effects))

    primary = pd.DataFrame(rows)
    primary["adjusted_p_value"] = holm_adjust(primary["p_value"])
    primary["reject_null_0_05"] = primary["adjusted_p_value"].le(0.05).astype("boolean")
    primary["claim_label"] = np.where(
        primary["adjusted_p_value"].isna(),
        "confirmatory_inference_incomplete",
        np.where(
            primary["adjusted_p_value"] <= 0.05,
            "confirmatory_supported_after_holm",
            "confirmatory_not_supported_after_holm",
        ),
    )
    return PublicInferenceResult(
        primary_inference=primary,
        tax_loss_year_effects=tax_loss_year_effects,
    )


def _walk_forward_row(strategy_name: str, summary: pd.DataFrame) -> dict[str, object]:
    required = {"fold_id", PRIMARY_WALK_FORWARD_METRIC}
    missing = required.difference(summary.columns)
    if missing:
        raise ValueError(
            f"{strategy_name} fold summary is missing required columns: {', '.join(sorted(missing))}"
        )

    working = summary.copy()
    if "window_label" in working.columns:
        working = working.loc[
            working["window_label"].astype("string").eq("evaluation")
        ].copy()
    values = pd.to_numeric(working[PRIMARY_WALK_FORWARD_METRIC], errors="coerce").dropna()
    return _primary_row(
        analysis_key=strategy_name,
        values=values,
        effect_unit="evaluation_fold_nav_difference",
        inference_method="walk_forward_fold_sign_flip",
        primary_metric=PRIMARY_WALK_FORWARD_METRIC,
        sample_unit="evaluation_folds",
        limitation_note=(
            "Fold-level confirmatory inference on public Yahoo out-of-sample strategy total return "
            "minus the STW.AX benchmark proxy. This is public-data transferability evidence, not a "
            "replication of the licensed publication sample and not a causal claim."
        ),
    )


def _complete_tax_loss_events(event_study: pd.DataFrame) -> pd.DataFrame:
    required = {
        "year",
        PRIMARY_TAX_LOSS_METRIC,
        "complete_event_window",
        "complete_control_window",
    }
    missing = required.difference(event_study.columns)
    if missing:
        raise ValueError(
            "Tax-loss event study is missing required columns: " + ", ".join(sorted(missing))
        )
    complete = event_study.loc[
        event_study["complete_event_window"].astype(bool)
        & event_study["complete_control_window"].astype(bool)
    ].copy()
    complete[PRIMARY_TAX_LOSS_METRIC] = pd.to_numeric(
        complete[PRIMARY_TAX_LOSS_METRIC], errors="coerce"
    )
    return complete.dropna(subset=[PRIMARY_TAX_LOSS_METRIC])


def _tax_loss_row(year_effects: pd.DataFrame) -> dict[str, object]:
    values = pd.to_numeric(
        year_effects.get("mean_abnormal_net_return_difference", pd.Series(dtype=float)),
        errors="coerce",
    ).dropna()
    return _primary_row(
        analysis_key="tax_loss_selling",
        values=values,
        effect_unit="annual_mean_abnormal_event_minus_control_return",
        inference_method="year_clustered_sign_flip",
        primary_metric=PRIMARY_TAX_LOSS_METRIC,
        sample_unit="calendar_years",
        limitation_note=(
            "Primary public Tax-Loss inference uses equal-weight calendar-year means of benchmark-adjusted "
            "net event-minus-control returns to respect within-year clustering. The public Yahoo universe "
            "is retrospective and does not reproduce point-in-time ASX 200 membership."
        ),
    )


def _primary_row(
    *,
    analysis_key: str,
    values: pd.Series,
    effect_unit: str,
    inference_method: str,
    primary_metric: str,
    sample_unit: str,
    limitation_note: str,
) -> dict[str, object]:
    clean = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(dtype=float)
    if clean.size == 0:
        effect = ci_lower = ci_upper = p_value = np.nan
    else:
        effect = float(clean.mean())
        ci_lower, ci_upper = bootstrap_mean_confidence_interval(clean)
        p_value = sign_flip_mean_p_value(clean, alternative=PRIMARY_ALTERNATIVE)

    return {
        "analysis_key": analysis_key,
        "governance": "confirmatory",
        "inference_method": inference_method,
        "effect_estimate": effect,
        "effect_unit": effect_unit,
        "null_value": 0.0,
        "alternative": PRIMARY_ALTERNATIVE,
        "ci_lower_95": ci_lower,
        "ci_upper_95": ci_upper,
        "p_value": p_value,
        "adjusted_p_value": np.nan,
        "multiple_testing_family": CONFIRMATORY_FAMILY_ID,
        "multiple_testing_method": HOLM_ADJUSTMENT_METHOD,
        "reject_null_0_05": pd.NA,
        "sample_size": int(clean.size),
        "claim_label": pd.NA,
        "primary_metric": primary_metric,
        "sample_unit": sample_unit,
        "limitation_note": limitation_note,
    }
