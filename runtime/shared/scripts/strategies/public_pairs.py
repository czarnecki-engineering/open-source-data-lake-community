from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import pandas as pd

from .metrics import compute_nav, summarize_return_stream
from .pairs_trading import build_pair_return_panel, build_strategy_daily, select_pairs_in_window
from .public_walk_forward import (
    _build_daily_results,
    _coerce_return_series,
    _format_parameters,
    _score_candidate,
)
from .public_walk_forward_costs import build_public_fold_cost_context
from .walk_forward import generate_walk_forward_folds


PAIR_PARAMETER_GRID = {
    "spread_window": [10, 20],
    "entry_z": [1.5, 2.0],
    "exit_z": [0.25, 0.5],
    "cost_scenario": ["base"],
}
PAIR_CAPITAL_NORMALIZATION = "gross_exposure_normalized_by_1_plus_abs_hedge_ratio"
PAIR_COST_APPLICATION = "normalized_two_leg_weighted_tier_cost"
PAIR_BORROW_FINANCING = "excluded_disclosed_limitation"
PAIR_UNIVERSE_TREATMENT = "retrospective_yahoo_universe_no_point_in_time_membership"
PAIR_CANDIDATE_SOURCE = "sector_first_public_sector_map"


@dataclass
class PublicPairsWalkForwardResult:
    fold_table: pd.DataFrame
    fold_daily_results: pd.DataFrame
    fold_summary: pd.DataFrame
    liquidity_diagnostics: pd.DataFrame
    pair_diagnostics: pd.DataFrame


def run_public_pairs_walk_forward(
    prices: pd.DataFrame,
    benchmark_returns: pd.Series | pd.DataFrame,
    sector_map: pd.DataFrame,
    risk_free_returns: pd.Series | pd.DataFrame | None = None,
    *,
    benchmark_col: str = "benchmark_return",
    risk_free_col: str = "risk_free_return",
    formation_years: int = 3,
    evaluation_years: int = 1,
    step_years: int = 1,
    max_folds: int | None = None,
    top_liquid_tickers: int = 20,
    top_pair_count: int = 5,
    engle_granger_pvalue_threshold: float = 0.05,
) -> PublicPairsWalkForwardResult:
    """Run publication-derived pairs trading on the public Yahoo research panel."""
    required_sector_columns = {"ticker", "sector"}
    missing_sector_columns = required_sector_columns.difference(sector_map.columns)
    if missing_sector_columns:
        raise ValueError(
            "Sector map is missing required columns: "
            + ", ".join(sorted(missing_sector_columns))
        )

    benchmark = _coerce_return_series(benchmark_returns, benchmark_col)
    risk_free = (
        _coerce_return_series(risk_free_returns, risk_free_col)
        if risk_free_returns is not None
        else None
    )
    benchmark_start = benchmark.first_valid_index()
    if benchmark_start is None:
        raise ValueError("Benchmark series contains no valid return observations.")

    fold_prices = prices.loc[pd.to_datetime(prices["trade_date"]) >= benchmark_start]
    folds = generate_walk_forward_folds(
        fold_prices,
        formation_years=formation_years,
        evaluation_years=evaluation_years,
        step_years=step_years,
    )
    if max_folds is not None:
        if max_folds < 1:
            raise ValueError("max_folds must be at least 1 when supplied.")
        folds = folds[:max_folds]

    fold_rows, daily_frames, summary_frames, liquidity_frames, pair_frames = [], [], [], [], []
    candidates = [
        dict(zip(PAIR_PARAMETER_GRID, values))
        for values in product(*(PAIR_PARAMETER_GRID[name] for name in PAIR_PARAMETER_GRID))
    ]

    for fold in folds:
        formation = _slice(prices, fold.formation_start, fold.formation_end)
        evaluation = _slice(prices, fold.evaluation_start, fold.evaluation_end)
        evaluation_identities = prices.loc[
            pd.to_datetime(prices["trade_date"]) <= fold.evaluation_end, ["ticker"]
        ]
        context = build_public_fold_cost_context(
            prices,
            fold,
            evaluation_prices=evaluation_identities,
            identity_col="ticker",
        )
        del evaluation_identities
        liquidity_frames.append(context.liquidity_diagnostics)

        _, selected_pairs = select_pairs_in_window(
            formation,
            top_liquid_tickers=top_liquid_tickers,
            top_pair_count=top_pair_count,
            engle_granger_pvalue_threshold=engle_granger_pvalue_threshold,
            liquidity_tier_map=context.liquidity_tier_map,
            sector_map=sector_map,
            identity_col="ticker",
            eligibility_col="eligible_to_trade",
        )

        best, best_metrics = None, None
        for candidate in candidates:
            pair_panel = build_pair_return_panel(
                formation,
                selected_pairs,
                spread_window=int(candidate["spread_window"]),
                entry_z=float(candidate["entry_z"]),
                exit_z=float(candidate["exit_z"]),
                cost_scenario=str(candidate["cost_scenario"]),
            )
            daily = _ensure_daily_calendar(
                build_strategy_daily(pair_panel), benchmark, fold.formation_start, fold.formation_end
            )
            scored = _build_daily_results(fold, daily, benchmark)
            scored = scored.loc[
                (scored["trade_date"] >= fold.formation_start)
                & (scored["trade_date"] <= fold.formation_end)
            ]
            metrics = _score_candidate(scored)
            if best_metrics is None or metrics["objective_value"] > best_metrics["objective_value"] or (
                metrics["objective_value"] == best_metrics["objective_value"]
                and metrics["average_turnover"] < best_metrics["average_turnover"]
            ):
                best, best_metrics = candidate, metrics

        if best is None or best_metrics is None:
            raise ValueError(f"No valid pairs candidate for {fold.fold_id}.")

        pair_panel = build_pair_return_panel(
            evaluation,
            selected_pairs,
            spread_window=int(best["spread_window"]),
            entry_z=float(best["entry_z"]),
            exit_z=float(best["exit_z"]),
            cost_scenario=str(best["cost_scenario"]),
        )
        daily = _ensure_daily_calendar(
            build_strategy_daily(pair_panel), benchmark, fold.evaluation_start, fold.evaluation_end
        )
        daily = _build_daily_results(fold, daily, benchmark)
        daily = daily.loc[
            (daily["trade_date"] >= fold.evaluation_start)
            & (daily["trade_date"] <= fold.evaluation_end)
        ].reset_index(drop=True)
        daily_frames.append(daily)

        dated = daily.set_index("trade_date").sort_index()
        comparable = dated.loc[dated["benchmark_observed"]]
        strategy_nav = compute_nav(comparable["net_return"])
        benchmark_nav = compute_nav(comparable["benchmark_return"])
        summary = summarize_return_stream(
            "pairs_trading",
            dated["net_return"],
            turnover=dated["turnover"],
            risk_free_returns=risk_free,
            extra_fields={
                "fold_id": fold.fold_id,
                "window_label": "evaluation",
                "benchmark_observation_count": int(dated["benchmark_observed"].sum()),
                "benchmark_missing_count": int((~dated["benchmark_observed"]).sum()),
                "total_net_excess_return": float(dated["excess_return"].sum(skipna=True)),
                "net_excess_nav_difference": float(strategy_nav.iloc[-1] - benchmark_nav.iloc[-1]),
                "chosen_parameters": _format_parameters(best),
                "selected_pair_count": int(len(selected_pairs)),
                "capital_normalization": PAIR_CAPITAL_NORMALIZATION,
                "pair_cost_application": PAIR_COST_APPLICATION,
                "borrow_financing": PAIR_BORROW_FINANCING,
                "universe_treatment": PAIR_UNIVERSE_TREATMENT,
                "candidate_source": PAIR_CANDIDATE_SOURCE,
            },
        )
        summary_frames.append(summary)

        fold_rows.append(
            {
                "fold_id": fold.fold_id,
                "formation_start": fold.formation_start,
                "formation_end": fold.formation_end,
                "evaluation_start": fold.evaluation_start,
                "evaluation_end": fold.evaluation_end,
                "strategy_name": "pairs_trading",
                "identity_col": "ticker",
                "eligibility_col": "eligible_to_trade",
                "selection_objective": "net_excess_nav_vs_benchmark",
                "chosen_parameters": _format_parameters(best),
                "formation_objective_value": best_metrics["objective_value"],
                "formation_total_net_excess_return": best_metrics["total_net_excess_return"],
                "formation_average_turnover": best_metrics["average_turnover"],
                "selected_pair_count": int(len(selected_pairs)),
                "capital_normalization": PAIR_CAPITAL_NORMALIZATION,
                "pair_cost_application": PAIR_COST_APPLICATION,
                "borrow_financing": PAIR_BORROW_FINANCING,
                "universe_treatment": PAIR_UNIVERSE_TREATMENT,
                "candidate_source": PAIR_CANDIDATE_SOURCE,
            }
        )
        if not selected_pairs.empty:
            diagnostics = selected_pairs.copy()
            diagnostics.insert(0, "fold_id", fold.fold_id)
            diagnostics["chosen_parameters"] = _format_parameters(best)
            pair_frames.append(diagnostics)

    return PublicPairsWalkForwardResult(
        fold_table=pd.DataFrame(fold_rows),
        fold_daily_results=pd.concat(daily_frames, ignore_index=True) if daily_frames else pd.DataFrame(),
        fold_summary=pd.concat(summary_frames, ignore_index=True) if summary_frames else pd.DataFrame(),
        liquidity_diagnostics=pd.concat(liquidity_frames, ignore_index=True) if liquidity_frames else pd.DataFrame(),
        pair_diagnostics=pd.concat(pair_frames, ignore_index=True) if pair_frames else pd.DataFrame(),
    )


def _ensure_daily_calendar(
    daily: pd.DataFrame,
    benchmark: pd.Series,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    calendar = benchmark.loc[(benchmark.index >= start) & (benchmark.index <= end)].index
    frame = daily.reindex(calendar).copy() if not daily.empty else pd.DataFrame(index=calendar)
    for column in (
        "gross_return",
        "net_return",
        "turnover",
        "average_turnover",
        "short_exposure",
        "effective_cost_bps",
    ):
        if column not in frame.columns:
            frame[column] = 0.0
    no_strategy = frame["net_return"].isna() & frame["gross_return"].isna()
    fill_columns = [
        "gross_return",
        "net_return",
        "turnover",
        "average_turnover",
        "short_exposure",
        "effective_cost_bps",
    ]
    frame.loc[no_strategy, fill_columns] = 0.0
    frame["nav"] = compute_nav(frame["net_return"])
    frame.index.name = "trade_date"
    return frame


def _slice(prices: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    trade_dates = pd.to_datetime(prices["trade_date"])
    return prices.loc[(trade_dates >= start) & (trade_dates <= end)].copy()
