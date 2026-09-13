from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class WalkForwardFold:
    fold_id: str
    formation_start: pd.Timestamp
    formation_end: pd.Timestamp
    evaluation_start: pd.Timestamp
    evaluation_end: pd.Timestamp


def generate_walk_forward_folds(
    prices: pd.DataFrame,
    formation_years: int = 3,
    evaluation_years: int = 1,
    step_years: int = 1,
) -> list[WalkForwardFold]:
    trade_dates = pd.Index(pd.to_datetime(prices["trade_date"])).sort_values().unique()
    if trade_dates.empty:
        return []

    folds: list[WalkForwardFold] = []
    fold_start = pd.Timestamp(trade_dates[0])
    final_trade_date = pd.Timestamp(trade_dates[-1])
    fold_number = 1

    while True:
        formation_end_exclusive = fold_start + pd.DateOffset(years=formation_years)
        evaluation_end_exclusive = formation_end_exclusive + pd.DateOffset(years=evaluation_years)
        formation_dates = trade_dates[(trade_dates >= fold_start) & (trade_dates < formation_end_exclusive)]
        evaluation_dates = trade_dates[(trade_dates >= formation_end_exclusive) & (trade_dates < evaluation_end_exclusive)]
        if len(formation_dates) == 0 or len(evaluation_dates) == 0:
            break
        folds.append(WalkForwardFold(
            fold_id=f"fold_{fold_number:02d}",
            formation_start=pd.Timestamp(formation_dates[0]),
            formation_end=pd.Timestamp(formation_dates[-1]),
            evaluation_start=pd.Timestamp(evaluation_dates[0]),
            evaluation_end=pd.Timestamp(evaluation_dates[-1]),
        ))
        fold_number += 1
        fold_start = fold_start + pd.DateOffset(years=step_years)
        if fold_start > final_trade_date:
            break
    return folds
