from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .public_costs import DEFAULT_MIN_LIQUIDITY_OBSERVATIONS, build_public_fold_liquidity_tiers
from .walk_forward import WalkForwardFold


@dataclass(frozen=True)
class PublicFoldCostContext:
    fold_id: str
    liquidity_tier_map: pd.Series
    liquidity_diagnostics: pd.DataFrame


def build_public_fold_cost_context(
    prices: pd.DataFrame,
    fold: WalkForwardFold,
    evaluation_prices: pd.DataFrame | None = None,
    identity_col: str = "ticker",
    min_liquidity_observations: int = DEFAULT_MIN_LIQUIDITY_OBSERVATIONS,
) -> PublicFoldCostContext:
    source = evaluation_prices if evaluation_prices is not None else prices
    if identity_col not in source.columns:
        raise ValueError(f"Evaluation prices are missing identity column: {identity_col}")
    evaluation_identities = pd.Index(source[identity_col].dropna().unique())
    result = build_public_fold_liquidity_tiers(
        prices=prices,
        formation_start=fold.formation_start,
        formation_end=fold.formation_end,
        evaluation_identities=evaluation_identities,
        identity_col=identity_col,
        min_liquidity_observations=min_liquidity_observations,
    )
    diagnostics = result.diagnostics.copy()
    diagnostics.insert(0, "fold_id", fold.fold_id)
    return PublicFoldCostContext(fold.fold_id, result.tier_map, diagnostics)
