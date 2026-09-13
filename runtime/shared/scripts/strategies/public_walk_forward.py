from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Callable

import pandas as pd

from .mean_reversion import run_mean_reversion_strategy
from .metrics import compute_nav, summarize_return_stream
from .public_walk_forward_costs import build_public_fold_cost_context
from .trend_following import run_trend_following_strategy
from .walk_forward import WalkForwardFold, generate_walk_forward_folds


@dataclass(frozen=True)
class PublicStrategyDefinition:
    runner: Callable[..., object]
    min_history: int
    parameter_grid: dict[str, list[object]]


@dataclass
class PublicWalkForwardResult:
    fold_table: pd.DataFrame
    fold_daily_results: pd.DataFrame
    fold_summary: pd.DataFrame
    liquidity_diagnostics: pd.DataFrame


PUBLIC_STRATEGY_DEFINITIONS = {
    "trend_following": PublicStrategyDefinition(run_trend_following_strategy, 220, {
        "fast_window": [50, 100], "slow_window": [150, 200], "min_history": [220], "cost_scenario": ["base"]}),
    "mean_reversion": PublicStrategyDefinition(run_mean_reversion_strategy, 60, {
        "lookback_window": [10, 20], "entry_z": [-1.5, -2.0], "exit_z": [-0.25, -0.5], "min_history": [60], "cost_scenario": ["base"]}),
}


def run_public_walk_forward(
    strategy_name: str,
    prices: pd.DataFrame,
    benchmark_returns: pd.Series | pd.DataFrame,
    risk_free_returns: pd.Series | pd.DataFrame | None = None,
    *, benchmark_col: str = "benchmark_return", risk_free_col: str = "risk_free_return",
    formation_years: int = 3, evaluation_years: int = 1, step_years: int = 1,
    max_folds: int | None = None,
) -> PublicWalkForwardResult:
    """Run the publication-derived walk-forward experiment on the public Yahoo panel."""
    if strategy_name not in PUBLIC_STRATEGY_DEFINITIONS:
        raise KeyError(f"Unsupported public strategy: {strategy_name}")
    definition = PUBLIC_STRATEGY_DEFINITIONS[strategy_name]
    benchmark_series = _coerce_return_series(benchmark_returns, benchmark_col)
    risk_free_series = _coerce_return_series(risk_free_returns, risk_free_col) if risk_free_returns is not None else None
    benchmark_start = benchmark_series.first_valid_index()
    if benchmark_start is None:
        raise ValueError("Benchmark series contains no valid return observations.")
    fold_prices = prices.loc[pd.to_datetime(prices["trade_date"]) >= benchmark_start]
    folds = generate_walk_forward_folds(fold_prices, formation_years, evaluation_years, step_years)
    if max_folds is not None:
        folds = folds[:max_folds]
    if not folds:
        return PublicWalkForwardResult(pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    candidates = _expand_parameter_grid(definition.parameter_grid)
    fold_rows, daily_frames, summary_frames, liquidity_frames = [], [], [], []
    trade_dates = pd.to_datetime(prices["trade_date"])
    for fold in folds:
        formation_prices = _slice_strategy_history(
            prices,
            window_start=fold.formation_start,
            window_end=fold.formation_end,
            warmup_observations=definition.min_history,
        )
        evaluation_universe = prices.loc[trade_dates <= fold.evaluation_end, ["ticker"]]
        context = build_public_fold_cost_context(prices, fold, evaluation_universe, identity_col="ticker")
        del evaluation_universe
        liquidity_frames.append(context.liquidity_diagnostics)
        fixed = {"identity_col": "ticker", "eligibility_col": "eligible_to_trade", "liquidity_tier_map": context.liquidity_tier_map}
        best, metrics = _select_best_parameters(definition.runner, formation_prices, benchmark_series, candidates, fold, fixed)
        del formation_prices

        evaluation_prices = _slice_strategy_history(
            prices,
            window_start=fold.formation_start,
            window_end=fold.evaluation_end,
            warmup_observations=definition.min_history,
        )
        kwargs = dict(best); kwargs.update(fixed)
        run = definition.runner(evaluation_prices, **kwargs)
        del evaluation_prices
        daily = _build_daily_results(fold, run.daily_results, benchmark_series)
        del run
        daily = daily.loc[(daily["trade_date"] >= fold.evaluation_start) & (daily["trade_date"] <= fold.evaluation_end)].reset_index(drop=True)
        daily_frames.append(daily)
        summary_frames.append(_build_summary(strategy_name, fold, daily, best, risk_free_series))
        fold_rows.append({
            "fold_id": fold.fold_id, "formation_start": fold.formation_start, "formation_end": fold.formation_end,
            "evaluation_start": fold.evaluation_start, "evaluation_end": fold.evaluation_end, "strategy_name": strategy_name,
            "identity_col": "ticker", "eligibility_col": "eligible_to_trade",
            "selection_objective": "net_excess_nav_vs_benchmark",
            "benchmark_missing_policy": "exclude_from_objective_and_excess_metrics",
            "chosen_parameters": _format_parameters(best), "formation_objective_value": metrics["objective_value"],
            "formation_total_net_excess_return": metrics["total_net_excess_return"],
            "formation_average_turnover": metrics["average_turnover"],
            "formation_benchmark_observation_count": metrics["benchmark_observation_count"],
        })
    return PublicWalkForwardResult(pd.DataFrame(fold_rows), pd.concat(daily_frames, ignore_index=True),
        pd.concat(summary_frames, ignore_index=True), pd.concat(liquidity_frames, ignore_index=True))


def _slice_strategy_history(
    prices: pd.DataFrame,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
    warmup_observations: int,
    identity_col: str = "ticker",
) -> pd.DataFrame:
    trade_dates = pd.to_datetime(prices["trade_date"])
    window_mask = (trade_dates >= window_start) & (trade_dates <= window_end)
    window_indices = prices.index[window_mask]

    pre_window_index = pd.DataFrame(
        {identity_col: prices[identity_col], "trade_date": trade_dates},
        index=prices.index,
    ).loc[trade_dates < window_start]
    warmup_indices = (
        pre_window_index.sort_values([identity_col, "trade_date"])
        .groupby(identity_col, observed=True, group_keys=False)
        .tail(warmup_observations)
        .index
    )

    selected_indices = warmup_indices.append(window_indices)
    bounded = prices.loc[selected_indices].copy()
    bounded["trade_date"] = pd.to_datetime(bounded["trade_date"])
    return bounded.sort_values([identity_col, "trade_date"]).reset_index(drop=True)


def _expand_parameter_grid(grid):
    names = list(grid)
    return [dict(zip(names, values)) for values in product(*(grid[name] for name in names))]


def _coerce_return_series(returns, column):
    if isinstance(returns, pd.Series):
        series = returns.copy()
    else:
        frame = returns[["trade_date", column]].copy(); frame["trade_date"] = pd.to_datetime(frame["trade_date"])
        if frame["trade_date"].duplicated().any(): raise ValueError("Return frame contains duplicate trade dates.")
        series = frame.set_index("trade_date")[column]
    series.index = pd.to_datetime(series.index)
    if series.index.duplicated().any(): raise ValueError("Return series contains duplicate trade dates.")
    return pd.to_numeric(series.sort_index(), errors="coerce").rename(column)


def _select_best_parameters(runner, formation_prices, benchmark, candidates, fold, fixed):
    best = metrics = None
    for candidate in candidates:
        kwargs = dict(candidate); kwargs.update(fixed)
        run = runner(formation_prices, **kwargs)
        daily = _build_daily_results(fold, run.daily_results, benchmark)
        daily = daily.loc[(daily["trade_date"] >= fold.formation_start) & (daily["trade_date"] <= fold.formation_end)]
        scored = _score_candidate(daily)
        if metrics is None or scored["objective_value"] > metrics["objective_value"] or (scored["objective_value"] == metrics["objective_value"] and scored["average_turnover"] < metrics["average_turnover"]):
            best, metrics = candidate, scored
    return best, metrics


def _build_daily_results(fold, daily_results, benchmark):
    frame = daily_results.copy(); frame.index = pd.to_datetime(frame.index); frame.index.name = "trade_date"
    frame["benchmark_return"] = benchmark.reindex(frame.index); frame["benchmark_observed"] = frame["benchmark_return"].notna()
    frame["excess_return"] = frame["net_return"] - frame["benchmark_return"]
    frame["benchmark_nav"] = compute_nav(frame["benchmark_return"]); frame["excess_nav"] = compute_nav(frame["excess_return"])
    frame = frame.reset_index(); frame.insert(0, "fold_id", fold.fold_id); return frame


def _score_candidate(daily):
    comparable = daily.loc[daily["benchmark_observed"]]
    if comparable.empty: raise ValueError("No benchmark-aligned observations are available for formation scoring.")
    strategy_nav = compute_nav(comparable["net_return"]); benchmark_nav = compute_nav(comparable["benchmark_return"])
    return {"objective_value": float(strategy_nav.iloc[-1] - benchmark_nav.iloc[-1]),
        "total_net_excess_return": float(comparable["excess_return"].sum()), "average_turnover": float(comparable["turnover"].mean()),
        "benchmark_observation_count": int(len(comparable))}


def _build_summary(strategy_name, fold, daily, parameters, risk_free):
    dated = daily.set_index("trade_date").sort_index(); comparable = dated.loc[dated["benchmark_observed"]]
    strategy_nav = compute_nav(comparable["net_return"]); benchmark_nav = compute_nav(comparable["benchmark_return"])
    return summarize_return_stream(strategy_name, dated["net_return"], turnover=dated["turnover"], risk_free_returns=risk_free,
        extra_fields={"fold_id": fold.fold_id, "window_label": "evaluation", "benchmark_observation_count": int(dated["benchmark_observed"].sum()),
        "benchmark_missing_count": int((~dated["benchmark_observed"]).sum()), "total_net_excess_return": float(dated["excess_return"].sum(skipna=True)),
        "net_excess_nav_difference": float(strategy_nav.iloc[-1] - benchmark_nav.iloc[-1]), "chosen_parameters": _format_parameters(parameters)})


def _format_parameters(parameters):
    return "|".join(f"{key}={parameters[key]}" for key in sorted(parameters))
