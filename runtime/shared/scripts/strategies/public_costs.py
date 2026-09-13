from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from .costs import DEFAULT_HIGH_LIQUIDITY_CUTOFF, DEFAULT_MEDIUM_LIQUIDITY_CUTOFF

DEFAULT_MIN_LIQUIDITY_OBSERVATIONS = 60
CONSERVATIVE_FALLBACK_TIER = "lower"


@dataclass(frozen=True)
class PublicLiquidityTierResult:
    tier_map: pd.Series
    diagnostics: pd.DataFrame


def build_public_fold_liquidity_tiers(
    prices: pd.DataFrame,
    formation_start: pd.Timestamp,
    formation_end: pd.Timestamp,
    evaluation_identities: Iterable[object] | None = None,
    identity_col: str = "ticker",
    date_col: str = "trade_date",
    dollar_volume_col: str = "dollar_volume",
    min_liquidity_observations: int = DEFAULT_MIN_LIQUIDITY_OBSERVATIONS,
    high_liquidity_cutoff: float = DEFAULT_HIGH_LIQUIDITY_CUTOFF,
    medium_liquidity_cutoff: float = DEFAULT_MEDIUM_LIQUIDITY_CUTOFF,
) -> PublicLiquidityTierResult:
    """Build ex-ante liquidity tiers for the public Yahoo universe.

    Unlike the publication/Norgate implementation, no point-in-time index
    membership filter is applied. Securities observed in the formation window
    with sufficient public dollar-volume history are ranked; other evaluation
    securities receive the conservative lower tier.
    """
    required = {identity_col, date_col, dollar_volume_col}
    missing = required.difference(prices.columns)
    if missing:
        raise ValueError(f"Public liquidity panel is missing required columns: {', '.join(sorted(missing))}")
    if min_liquidity_observations <= 0:
        raise ValueError("min_liquidity_observations must be positive.")

    formation_start = pd.Timestamp(formation_start)
    formation_end = pd.Timestamp(formation_end)
    trade_dates = pd.to_datetime(prices[date_col])
    formation_mask = (trade_dates >= formation_start) & (trade_dates <= formation_end)
    formation = prices.loc[formation_mask, [identity_col, date_col, dollar_volume_col]].copy()
    formation[date_col] = trade_dates.loc[formation_mask].to_numpy()
    if formation.empty:
        raise ValueError("No observations are available in the formation window.")

    formation[dollar_volume_col] = pd.to_numeric(formation[dollar_volume_col], errors="coerce")
    if (formation[dollar_volume_col].dropna() < 0).any():
        raise ValueError("dollar_volume must be non-negative where observed.")

    liquidity = formation.loc[formation[dollar_volume_col].notna()].groupby(identity_col, observed=True)[dollar_volume_col].agg(
        liquidity_observation_count="size", median_dollar_volume="median"
    )
    liquidity["sufficient_liquidity_history"] = liquidity["liquidity_observation_count"] >= min_liquidity_observations
    ranked = liquidity.loc[liquidity["sufficient_liquidity_history"]].sort_values("median_dollar_volume", ascending=False, kind="mergesort").copy()
    if not ranked.empty:
        ranked["liquidity_rank"] = np.arange(1, len(ranked) + 1)
        ranked["liquidity_percentile"] = ranked["liquidity_rank"] / len(ranked)
        ranked["liquidity_tier"] = np.select(
            [ranked["liquidity_percentile"] <= high_liquidity_cutoff, ranked["liquidity_percentile"] <= medium_liquidity_cutoff],
            ["high", "medium"], default=CONSERVATIVE_FALLBACK_TIER,
        )
    diagnostics = liquidity.join(ranked[["liquidity_rank", "liquidity_percentile", "liquidity_tier"]], how="left")
    diagnostics["liquidity_tier"] = diagnostics["liquidity_tier"].fillna(CONSERVATIVE_FALLBACK_TIER)
    diagnostics["tier_assignment_reason"] = np.where(
        diagnostics["sufficient_liquidity_history"], "formation_window_rank", "insufficient_history_conservative_lower"
    )

    evaluation_index = pd.Index(
        prices[identity_col].dropna().unique() if evaluation_identities is None else list(evaluation_identities)
    ).dropna().unique()
    tier_map = pd.Series(CONSERVATIVE_FALLBACK_TIER, index=evaluation_index, dtype="string", name="liquidity_tier")
    common = tier_map.index.intersection(diagnostics.index)
    tier_map.loc[common] = diagnostics.loc[common, "liquidity_tier"].astype("string")

    diagnostics.index.name = identity_col
    diagnostics = diagnostics.reset_index()
    diagnostics["formation_start"] = formation_start
    diagnostics["formation_end"] = formation_end
    diagnostics["min_liquidity_observations"] = min_liquidity_observations
    return PublicLiquidityTierResult(tier_map=tier_map, diagnostics=diagnostics)
