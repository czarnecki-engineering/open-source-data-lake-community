from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

from .costs import apply_turnover_costs, resolve_cost_scenario
from .metrics import compute_nav


def select_pairs_in_window(
    prices: pd.DataFrame,
    top_liquid_tickers: int = 20,
    top_pair_count: int = 5,
    engle_granger_pvalue_threshold: float = 0.05,
    liquidity_tier_map: pd.Series | None = None,
    sector_map: pd.Series | pd.DataFrame | None = None,
    identity_col: str = "ticker",
    eligibility_col: str | None = "eligible_to_trade",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Select liquid residual-stationarity-screened pairs from a formation window.

    Pair generation follows the publication sector-first convention. If enough
    same-sector candidates exist to fill ``top_pair_count``, only same-sector
    candidates are screened. Otherwise the remaining cross-sector combinations
    form the documented fallback candidate set.
    """
    required = {identity_col, "trade_date", "dollar_volume", "adj_close"}
    if eligibility_col is not None:
        required.add(eligibility_col)
    missing = required.difference(prices.columns)
    if missing:
        raise ValueError(f"Pair formation panel is missing required columns: {', '.join(sorted(missing))}")

    working = prices.copy()
    working["trade_date"] = pd.to_datetime(working["trade_date"])
    if eligibility_col is not None:
        latest = (
            working.sort_values([identity_col, "trade_date"])
            .groupby(identity_col, observed=True)
            .tail(1)
        )
        eligible = latest.loc[latest[eligibility_col].astype(bool), identity_col]
        working = working.loc[working[identity_col].isin(eligible)].copy()

    liquidity = (
        working.groupby(identity_col, observed=True)["dollar_volume"]
        .median()
        .sort_values(ascending=False)
    )
    candidate_identities = liquidity.head(top_liquid_tickers).index.tolist()
    positive_prices = prices.loc[prices["adj_close"] > 0, ["trade_date", identity_col, "adj_close"]]
    price_matrix = (
        positive_prices.loc[positive_prices[identity_col].isin(candidate_identities)]
        .pivot(index="trade_date", columns=identity_col, values="adj_close")
        .sort_index()
    )
    tier_lookup = (
        pd.Series(liquidity_tier_map, dtype="string").reindex(candidate_identities).to_dict()
        if liquidity_tier_map is not None
        else {identity: "lower" for identity in candidate_identities}
    )
    sector_lookup = _coerce_sector_map(sector_map, identity_col)
    candidate_pairs = _generate_candidate_pairs(
        candidate_identities,
        sector_lookup,
        top_pair_count=top_pair_count,
    )

    rows: list[dict[str, object]] = []
    for left_identity, right_identity, candidate_source in candidate_pairs:
        metrics = _fit_pair(price_matrix, left_identity, right_identity)
        if metrics is None:
            continue
        pvalue = metrics["cointegration_pvalue"]
        rows.append(
            {
                "pair_id": f"{left_identity}_{right_identity}",
                "left_identity": left_identity,
                "right_identity": right_identity,
                "left_ticker": str(left_identity),
                "right_ticker": str(right_identity),
                "left_sector": sector_lookup.get(left_identity, ""),
                "right_sector": sector_lookup.get(right_identity, ""),
                "left_liquidity_tier": tier_lookup.get(left_identity, "lower"),
                "right_liquidity_tier": tier_lookup.get(right_identity, "lower"),
                "candidate_source": candidate_source,
                **metrics,
                "passed_cointegration": bool(pd.notna(pvalue) and pvalue <= engle_granger_pvalue_threshold),
            }
        )

    pair_table = pd.DataFrame(rows)
    if pair_table.empty:
        return pair_table, pair_table.copy()
    pair_table = pair_table.sort_values(
        ["passed_cointegration", "fit_statistic", "cointegration_pvalue"],
        ascending=[False, True, True],
    ).reset_index(drop=True)
    selected = pair_table.loc[pair_table["passed_cointegration"]].head(top_pair_count).reset_index(drop=True)
    return pair_table, selected


def _coerce_sector_map(
    sector_map: pd.Series | pd.DataFrame | None,
    identity_col: str,
) -> dict[object, str]:
    if sector_map is None:
        return {}
    if isinstance(sector_map, pd.DataFrame):
        required = {identity_col, "sector"}
        missing = required.difference(sector_map.columns)
        if missing:
            raise ValueError(f"Sector map is missing required columns: {', '.join(sorted(missing))}")
        rows = sector_map[[identity_col, "sector"]].drop_duplicates(subset=[identity_col], keep="last")
        series = rows.set_index(identity_col)["sector"]
    else:
        series = pd.Series(sector_map)
    return {
        identity: str(value).strip()
        for identity, value in series.items()
        if pd.notna(value) and str(value).strip()
    }


def _generate_candidate_pairs(
    candidate_identities: list[object],
    sector_lookup: dict[object, str],
    *,
    top_pair_count: int,
) -> list[tuple[object, object, str]]:
    same_sector: list[tuple[object, object, str]] = []
    fallback: list[tuple[object, object, str]] = []
    for left, right in combinations(candidate_identities, 2):
        left_sector = sector_lookup.get(left, "")
        right_sector = sector_lookup.get(right, "")
        if left_sector and right_sector and left_sector == right_sector and left_sector != "Unmapped":
            same_sector.append((left, right, "same_sector"))
        else:
            fallback.append((left, right, "sector_fallback"))
    return same_sector if len(same_sector) >= top_pair_count else same_sector + fallback


def build_pair_return_panel(
    trading_prices: pd.DataFrame,
    selected_pairs: pd.DataFrame,
    spread_window: int,
    entry_z: float,
    exit_z: float,
    cost_scenario: str = "base",
    identity_col: str = "ticker",
    eligibility_col: str | None = "eligible_to_trade",
) -> pd.DataFrame:
    if selected_pairs.empty:
        return pd.DataFrame()

    prices = trading_prices.copy()
    prices["trade_date"] = pd.to_datetime(prices["trade_date"])
    prices.loc[prices["adj_close"] <= 0, "adj_close"] = np.nan
    price_matrix = prices.pivot(index="trade_date", columns=identity_col, values="adj_close").sort_index()
    return_matrix = price_matrix.pct_change(fill_method=None)

    eligibility = None
    if eligibility_col is not None:
        eligibility = (
            prices.pivot(index="trade_date", columns=identity_col, values=eligibility_col)
            .sort_index()
            .fillna(False)
            .astype(bool)
        )

    scenario = resolve_cost_scenario(cost_scenario)
    frames = []
    for _, pair in selected_pairs.iterrows():
        left = pair["left_identity"]
        right = pair["right_identity"]
        if left not in price_matrix.columns or right not in price_matrix.columns:
            continue

        hedge = float(pair["hedge_ratio"])
        denominator = 1.0 + abs(hedge)
        left_weight = 1.0 / denominator
        right_weight = abs(hedge) / denominator
        spread = _compute_log_spread(
            price_matrix[left], price_matrix[right], hedge, float(pair["intercept"])
        )
        spread_mean = spread.rolling(spread_window).mean()
        spread_std = spread.rolling(spread_window).std().replace(0.0, np.nan)
        spread_z = ((spread - spread_mean) / spread_std).replace([np.inf, -np.inf], np.nan)
        position = _build_pair_position(spread_z, entry_z, exit_z)

        observed = price_matrix[left].notna() & price_matrix[right].notna()
        if eligibility is not None:
            observed &= eligibility[left].reindex(position.index).fillna(False)
            observed &= eligibility[right].reindex(position.index).fillna(False)
        position = position.where(observed.reindex(position.index).fillna(False), 0.0)

        previous_position = position.shift(1).fillna(0.0)
        raw_spread_return = return_matrix[left] - hedge * return_matrix[right]
        gross_return = previous_position * (raw_spread_return / denominator)
        gross_return = gross_return.where(previous_position.ne(0.0), 0.0)
        turnover = position.diff().abs().fillna(0.0)

        left_bps = scenario.cost_bps_for_tier(str(pair["left_liquidity_tier"]))
        right_bps = scenario.cost_bps_for_tier(str(pair["right_liquidity_tier"]))
        effective_bps = left_weight * left_bps + right_weight * right_bps
        net_return = apply_turnover_costs(gross_return, turnover, turnover_cost_bps=effective_bps)

        short_exposure = pd.Series(0.0, index=position.index, dtype=float)
        short_exposure.loc[position > 0] = right_weight
        short_exposure.loc[position < 0] = left_weight
        frames.append(
            pd.DataFrame(
                {
                    "trade_date": position.index,
                    "pair_id": pair["pair_id"],
                    "left_identity": left,
                    "right_identity": right,
                    "left_ticker": pair["left_ticker"],
                    "right_ticker": pair["right_ticker"],
                    "pair_gross_return": gross_return.values,
                    "pair_net_return": net_return.values,
                    "pair_turnover": turnover.values,
                    "pair_turnover_cost_bps": effective_bps,
                    "left_liquidity_tier": pair["left_liquidity_tier"],
                    "right_liquidity_tier": pair["right_liquidity_tier"],
                    "spread": spread.values,
                    "spread_z": spread_z.values,
                    "pair_position": position.values,
                    "pair_short_exposure": short_exposure.values,
                    "gross_exposure_denominator": denominator,
                }
            )
        )
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_strategy_daily(pair_return_panel: pd.DataFrame) -> pd.DataFrame:
    if pair_return_panel.empty:
        return pd.DataFrame(
            columns=["gross_return", "net_return", "turnover", "average_turnover", "short_exposure", "effective_cost_bps", "nav"]
        )
    daily = (
        pair_return_panel.groupby("trade_date", observed=True)
        .agg(
            gross_return=("pair_gross_return", "mean"),
            net_return=("pair_net_return", "mean"),
            turnover=("pair_turnover", "mean"),
            average_turnover=("pair_turnover", "mean"),
            short_exposure=("pair_short_exposure", "mean"),
            effective_cost_bps=("pair_turnover_cost_bps", "mean"),
        )
        .sort_index()
    )
    daily["nav"] = compute_nav(daily["net_return"])
    return daily


def _fit_pair(price_matrix: pd.DataFrame, left_identity: object, right_identity: object) -> dict[str, float] | None:
    pair = price_matrix[[left_identity, right_identity]].dropna()
    if len(pair) < 10:
        return None
    left_log = np.log(pair[left_identity].astype(float))
    right_log = np.log(pair[right_identity].astype(float))
    intercept, hedge_ratio = _estimate_hedge_ratio(left_log, right_log)
    spread = left_log - (intercept + hedge_ratio * right_log)
    spread_volatility = float(spread.std(ddof=1))
    if np.isclose(spread_volatility, 0.0):
        fit_statistic, pvalue = float("-inf"), 0.0
    else:
        fit_statistic, pvalue = _residual_stationarity_test(spread)
    return {
        "hedge_ratio": hedge_ratio,
        "intercept": intercept,
        "fit_statistic": fit_statistic,
        "cointegration_pvalue": pvalue,
        "spread_volatility": spread_volatility,
        "formation_observations": float(len(pair)),
    }


def _estimate_hedge_ratio(left_log: pd.Series, right_log: pd.Series) -> tuple[float, float]:
    x = right_log.to_numpy(dtype=float)
    y = left_log.to_numpy(dtype=float)
    design = np.column_stack([np.ones(len(x)), x])
    coefficients, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
    return float(coefficients[0]), float(coefficients[1])


def _residual_stationarity_test(spread: pd.Series) -> tuple[float, float]:
    residuals = spread.dropna().to_numpy(dtype=float)
    lagged = residuals[:-1]
    delta = np.diff(residuals)
    if len(delta) < 3:
        return np.nan, np.nan
    denominator = float(np.dot(lagged, lagged))
    if denominator == 0.0:
        return np.nan, np.nan
    phi_hat = float(np.dot(lagged, delta) / denominator)
    errors = delta - phi_hat * lagged
    dof = len(delta) - 1
    if dof <= 0:
        return np.nan, np.nan
    sigma2 = float(np.dot(errors, errors) / dof)
    standard_error = np.sqrt(sigma2 / denominator)
    if standard_error == 0.0:
        return np.nan, np.nan
    t_stat = phi_hat / standard_error
    return float(t_stat), float(stats.t.cdf(t_stat, df=dof))


def _compute_log_spread(left: pd.Series, right: pd.Series, hedge_ratio: float, intercept: float) -> pd.Series:
    return np.log(left.astype(float)) - (intercept + hedge_ratio * np.log(right.astype(float)))


def _build_pair_position(spread_z: pd.Series, entry_z: float, exit_z: float) -> pd.Series:
    position = pd.Series(np.nan, index=spread_z.index, dtype=float)
    position.loc[spread_z.le(-entry_z)] = 1.0
    position.loc[spread_z.ge(entry_z)] = -1.0
    position.loc[spread_z.abs().le(exit_z)] = 0.0
    return position.ffill().fillna(0.0)
