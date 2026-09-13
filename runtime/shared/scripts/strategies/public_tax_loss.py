from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .costs import basis_points_to_rate, resolve_cost_scenario
from .public_costs import build_public_fold_liquidity_tiers


TAX_LOSS_LOOKBACK_DAYS = 252
TAX_LOSS_WINDOW_RADIUS = 10
TAX_LOSS_CONTROL_SHIFT_DAYS = 60
TAX_LOSS_SELECTION_OFFSET_DAYS = 11
TAX_LOSS_SELECTION_QUANTILE = 0.10
TAX_LOSS_COST_SCENARIO = "base"
TAX_LOSS_UNIVERSE_TREATMENT = "public_yahoo_retrospective"
TAX_LOSS_COST_APPLICATION = "symmetric_round_trip_cost_event_and_control"
TAX_LOSS_MISSING_WINDOW_POLICY = "require_complete_security_and_benchmark_windows"


@dataclass
class PublicTaxLossResult:
    event_study: pd.DataFrame
    summary: pd.DataFrame
    liquidity_diagnostics: pd.DataFrame


def run_public_tax_loss_event_study(
    prices: pd.DataFrame,
    benchmark_returns: pd.DataFrame | pd.Series,
    *,
    lookback_days: int = TAX_LOSS_LOOKBACK_DAYS,
    window_radius: int = TAX_LOSS_WINDOW_RADIUS,
    control_shift_days: int = TAX_LOSS_CONTROL_SHIFT_DAYS,
    selection_offset_days: int = TAX_LOSS_SELECTION_OFFSET_DAYS,
    selection_quantile: float = TAX_LOSS_SELECTION_QUANTILE,
    cost_scenario: str = TAX_LOSS_COST_SCENARIO,
    max_years: int | None = None,
) -> PublicTaxLossResult:
    required = {"ticker", "trade_date", "adj_close", "daily_return", "dollar_volume"}
    missing = required.difference(prices.columns)
    if missing:
        raise ValueError("Public tax-loss panel is missing required columns: " + ", ".join(sorted(missing)))
    if selection_offset_days <= window_radius:
        raise ValueError("selection_offset_days must be greater than window_radius.")
    if not 0 < selection_quantile < 1:
        raise ValueError("selection_quantile must be between zero and one.")
    if max_years is not None and max_years < 1:
        raise ValueError("max_years must be at least 1 when supplied.")

    frame = prices.loc[:, sorted(required)].copy()
    frame["trade_date"] = pd.to_datetime(frame["trade_date"])
    frame = frame.sort_values(["ticker", "trade_date"]).reset_index(drop=True)
    if frame.duplicated(["ticker", "trade_date"]).any():
        raise ValueError("Public tax-loss panel contains duplicate ticker/trade_date rows.")
    frame["trailing_12m_return"] = (
        frame.groupby("ticker", observed=True)["adj_close"]
        .transform(lambda series: series / series.shift(lookback_days) - 1.0)
    )

    benchmark = _coerce_benchmark_series(benchmark_returns)
    calendar = pd.DatetimeIndex(sorted(frame["trade_date"].dropna().unique()))
    scenario = resolve_cost_scenario(cost_scenario)

    records: list[dict[str, object]] = []
    liquidity_frames: list[pd.DataFrame] = []
    years = sorted(frame["trade_date"].dt.year.unique())
    if max_years is not None:
        years = years[:max_years]

    for year in years:
        event_anchor = pd.Timestamp(year=int(year), month=6, day=30)
        eligible_dates = calendar[calendar <= event_anchor]
        if len(eligible_dates) == 0:
            continue
        event_date = eligible_dates[-1]
        event_loc = calendar.get_loc(event_date)
        control_loc = event_loc - control_shift_days
        selection_loc = event_loc - selection_offset_days
        if selection_loc < 0 or control_loc - window_radius < 0 or event_loc + window_radius >= len(calendar):
            continue

        selection_date = calendar[selection_loc]
        control_date = calendar[control_loc]
        event_window_dates = calendar[event_loc - window_radius : event_loc + window_radius + 1]
        control_window_dates = calendar[control_loc - window_radius : control_loc + window_radius + 1]

        snapshot = frame.loc[
            frame["trade_date"] == selection_date,
            ["ticker", "trailing_12m_return"],
        ].dropna(subset=["ticker", "trailing_12m_return"])
        if snapshot.empty:
            continue

        cutoff = snapshot["trailing_12m_return"].quantile(selection_quantile)
        selected = snapshot.loc[snapshot["trailing_12m_return"] <= cutoff].copy()
        if selected.empty:
            continue

        formation_start = selection_date - pd.DateOffset(years=3)
        liquidity = build_public_fold_liquidity_tiers(
            prices=frame,
            formation_start=formation_start,
            formation_end=selection_date,
            evaluation_identities=selected["ticker"],
            identity_col="ticker",
        )
        diagnostics = liquidity.diagnostics.copy()
        diagnostics.insert(0, "year", int(year))
        diagnostics.insert(1, "selection_date", selection_date)
        liquidity_frames.append(diagnostics)

        benchmark_event = _strict_window_return(benchmark, event_window_dates)
        benchmark_control = _strict_window_return(benchmark, control_window_dates)

        for row in selected.itertuples(index=False):
            ticker = row.ticker
            asset_returns = (
                frame.loc[frame["ticker"] == ticker, ["trade_date", "daily_return"]]
                .set_index("trade_date")["daily_return"]
                .sort_index()
            )
            event_return = _strict_window_return(asset_returns, event_window_dates)
            control_return = _strict_window_return(asset_returns, control_window_dates)
            tier = str(liquidity.tier_map.loc[ticker])
            cost_bps = scenario.cost_bps_for_tier(tier)
            round_trip_cost = scenario.tax_loss_trade_legs * basis_points_to_rate(cost_bps)

            net_event = event_return - round_trip_cost if pd.notna(event_return) else np.nan
            net_control = control_return - round_trip_cost if pd.notna(control_return) else np.nan
            abnormal_event = net_event - benchmark_event if pd.notna(net_event) and pd.notna(benchmark_event) else np.nan
            abnormal_control = net_control - benchmark_control if pd.notna(net_control) and pd.notna(benchmark_control) else np.nan

            records.append(
                {
                    "year": int(year),
                    "ticker": ticker,
                    "selection_date": selection_date,
                    "event_date": event_date,
                    "control_date": control_date,
                    "selection_trailing_12m_return": float(row.trailing_12m_return),
                    "selection_cutoff": float(cutoff),
                    "liquidity_tier": tier,
                    "turnover_cost_bps_per_leg": float(cost_bps),
                    "round_trip_cost_rate": float(round_trip_cost),
                    "event_window_return": event_return,
                    "control_window_return": control_return,
                    "return_difference": event_return - control_return if pd.notna(event_return) and pd.notna(control_return) else np.nan,
                    "net_event_window_return": net_event,
                    "net_control_window_return": net_control,
                    "net_return_difference": net_event - net_control if pd.notna(net_event) and pd.notna(net_control) else np.nan,
                    "benchmark_event_window_return": benchmark_event,
                    "benchmark_control_window_return": benchmark_control,
                    "abnormal_net_event_window_return": abnormal_event,
                    "abnormal_net_control_window_return": abnormal_control,
                    "abnormal_net_return_difference": abnormal_event - abnormal_control if pd.notna(abnormal_event) and pd.notna(abnormal_control) else np.nan,
                    "complete_event_window": bool(pd.notna(event_return) and pd.notna(benchmark_event)),
                    "complete_control_window": bool(pd.notna(control_return) and pd.notna(benchmark_control)),
                }
            )

    event_study = pd.DataFrame(records)
    if event_study.empty:
        complete = event_study.copy()
    else:
        complete = event_study.loc[
            event_study["complete_event_window"] & event_study["complete_control_window"]
        ].copy()
    summary = pd.DataFrame([
        {
            "strategy": "public_tax_loss_selling_event_study",
            "universe_treatment": TAX_LOSS_UNIVERSE_TREATMENT,
            "lookback_days": lookback_days,
            "window_radius_days": window_radius,
            "control_shift_days": control_shift_days,
            "selection_offset_days": selection_offset_days,
            "selection_quantile": selection_quantile,
            "cost_scenario": scenario.name,
            "cost_application": TAX_LOSS_COST_APPLICATION,
            "missing_window_policy": TAX_LOSS_MISSING_WINDOW_POLICY,
            "event_observation_count": int(len(event_study)),
            "complete_matched_observation_count": int(len(complete)),
            "year_count": int(complete["year"].nunique()) if not complete.empty else 0,
            "mean_event_window_return": complete["event_window_return"].mean() if not complete.empty else np.nan,
            "mean_control_window_return": complete["control_window_return"].mean() if not complete.empty else np.nan,
            "mean_return_difference": complete["return_difference"].mean() if not complete.empty else np.nan,
            "mean_net_event_window_return": complete["net_event_window_return"].mean() if not complete.empty else np.nan,
            "mean_net_control_window_return": complete["net_control_window_return"].mean() if not complete.empty else np.nan,
            "mean_net_return_difference": complete["net_return_difference"].mean() if not complete.empty else np.nan,
            "mean_abnormal_net_event_window_return": complete["abnormal_net_event_window_return"].mean() if not complete.empty else np.nan,
            "mean_abnormal_net_control_window_return": complete["abnormal_net_control_window_return"].mean() if not complete.empty else np.nan,
            "mean_abnormal_net_return_difference": complete["abnormal_net_return_difference"].mean() if not complete.empty else np.nan,
            "positive_net_difference_fraction": complete["net_return_difference"].gt(0).mean() if not complete.empty else np.nan,
        }
    ])
    liquidity_diagnostics = pd.concat(liquidity_frames, ignore_index=True) if liquidity_frames else pd.DataFrame()
    return PublicTaxLossResult(event_study=event_study, summary=summary, liquidity_diagnostics=liquidity_diagnostics)


def _coerce_benchmark_series(benchmark_returns: pd.DataFrame | pd.Series) -> pd.Series:
    if isinstance(benchmark_returns, pd.Series):
        series = benchmark_returns.copy()
    else:
        required = {"trade_date", "benchmark_return"}
        missing = required.difference(benchmark_returns.columns)
        if missing:
            raise ValueError("Benchmark returns are missing required columns: " + ", ".join(sorted(missing)))
        series = benchmark_returns.loc[:, ["trade_date", "benchmark_return"]].copy()
        series["trade_date"] = pd.to_datetime(series["trade_date"])
        if series["trade_date"].duplicated().any():
            raise ValueError("Benchmark returns contain duplicate trade dates.")
        series = series.set_index("trade_date")["benchmark_return"]
    series.index = pd.to_datetime(series.index)
    if series.index.duplicated().any():
        raise ValueError("Benchmark return series contains duplicate trade dates.")
    return pd.to_numeric(series.sort_index(), errors="coerce")


def _strict_window_return(series: pd.Series, window_dates: pd.DatetimeIndex) -> float:
    aligned = pd.to_numeric(series.reindex(window_dates), errors="coerce")
    if len(aligned) != len(window_dates) or aligned.isna().any():
        return np.nan
    return float((1.0 + aligned).prod() - 1.0)
