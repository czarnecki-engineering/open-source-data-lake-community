from __future__ import annotations

import numpy as np
import pandas as pd


PUBLIC_UNIVERSE_TREATMENT = "public_yahoo_retrospective"
PUBLIC_UNIVERSE_LIMITATION_NOTE = (
    "The research panel uses the configured public Yahoo/yFinance security universe. "
    "It does not model point-in-time ASX 200 membership or a complete delisting archive."
)
RETURN_PRICE_RULE = (
    "Use Yahoo adj_close returns when both current and prior adjusted prices are positive; "
    "otherwise fall back to close returns for that observation."
)


def build_asx_research_panel(
    curated: pd.DataFrame,
    min_history: int = 1,
) -> pd.DataFrame:
    """Adapt the curated Yahoo ASX panel to the public research contract."""
    if min_history <= 0:
        raise ValueError("min_history must be positive.")

    required_columns = {"ticker", "trade_date", "close", "adj_close", "volume"}
    missing_columns = required_columns.difference(curated.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Curated ASX panel is missing required columns: {missing_list}")

    panel = curated.loc[:, ["ticker", "trade_date", "close", "adj_close", "volume"]].copy()
    panel["ticker"] = panel["ticker"].astype("string").str.strip().str.upper()
    if panel["ticker"].isna().any() or panel["ticker"].eq("").any():
        raise ValueError("Curated ASX panel contains blank ticker values.")

    panel["trade_date"] = pd.to_datetime(panel["trade_date"], errors="coerce")
    if panel["trade_date"].isna().any():
        raise ValueError("Curated ASX panel contains invalid trade_date values.")

    panel["close"] = pd.to_numeric(panel["close"], errors="coerce")
    panel["adj_close"] = pd.to_numeric(panel["adj_close"], errors="coerce")
    panel["volume"] = pd.to_numeric(panel["volume"], errors="coerce")
    if panel[["close", "adj_close", "volume"]].isna().any().any():
        raise ValueError("Curated ASX panel contains null or non-numeric price/volume values.")

    if panel.duplicated(["ticker", "trade_date"]).any():
        raise ValueError("Curated ASX panel contains duplicate ticker/trade_date rows.")

    panel = panel.sort_values(["ticker", "trade_date"]).reset_index(drop=True)
    grouped = panel.groupby("ticker", observed=True)
    adjusted_return = grouped["adj_close"].pct_change(fill_method=None)
    close_return = grouped["close"].pct_change(fill_method=None)
    prior_adjusted_close = grouped["adj_close"].shift(1)
    invalid_adjusted_pair = (panel["adj_close"] <= 0) | (prior_adjusted_close <= 0)
    panel["daily_return"] = adjusted_return.where(~invalid_adjusted_pair, close_return)
    panel["dollar_volume"] = panel["close"] * panel["volume"]
    panel["history_observation_count"] = (
        panel.groupby("ticker", observed=True).cumcount() + 1
    )
    panel["eligible_to_trade"] = panel["history_observation_count"] >= int(min_history)

    panel.attrs["universe_treatment"] = PUBLIC_UNIVERSE_TREATMENT
    panel.attrs["universe_limitation_note"] = PUBLIC_UNIVERSE_LIMITATION_NOTE
    panel.attrs["return_price_rule"] = RETURN_PRICE_RULE
    panel.attrs["liquidity_proxy"] = "close_x_volume"
    panel.attrs["min_history"] = int(min_history)
    return panel


def summarize_asx_research_panel_quality(
    panel: pd.DataFrame,
    extreme_return_floor: float = -1.0,
    extreme_return_ceiling: float = 10.0,
) -> dict[str, object]:
    """Report public Yahoo research-panel data-quality diagnostics without changing data."""
    if extreme_return_floor >= extreme_return_ceiling:
        raise ValueError("extreme_return_floor must be less than extreme_return_ceiling.")

    required_columns = {
        "ticker",
        "trade_date",
        "close",
        "adj_close",
        "volume",
        "daily_return",
        "dollar_volume",
    }
    missing_columns = required_columns.difference(panel.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Research panel is missing required columns: {missing_list}")

    ordered = panel.loc[:, sorted(required_columns)].copy()
    ordered["trade_date"] = pd.to_datetime(ordered["trade_date"], errors="coerce")
    ordered = ordered.sort_values(["ticker", "trade_date"]).reset_index(drop=True)

    prior_adjusted_close = ordered.groupby("ticker", observed=True)["adj_close"].shift(1)
    adjusted_fallback = (ordered["adj_close"] <= 0) | (prior_adjusted_close <= 0)

    dollar_volume = pd.to_numeric(ordered["dollar_volume"], errors="coerce")
    invalid_dollar_volume = dollar_volume.isna() | ~np.isfinite(dollar_volume) | (dollar_volume < 0)

    daily_return = pd.to_numeric(ordered["daily_return"], errors="coerce")
    extreme_return = (daily_return <= extreme_return_floor) | (daily_return > extreme_return_ceiling)

    return {
        "rows": int(len(ordered)),
        "tickers": int(ordered["ticker"].nunique()),
        "date_min": ordered["trade_date"].min(),
        "date_max": ordered["trade_date"].max(),
        "non_positive_adjusted_price_rows": int((ordered["adj_close"] <= 0).sum()),
        "adjusted_price_fallback_rows": int(adjusted_fallback.sum()),
        "invalid_or_negative_dollar_volume_rows": int(invalid_dollar_volume.sum()),
        "extreme_return_floor": float(extreme_return_floor),
        "extreme_return_ceiling": float(extreme_return_ceiling),
        "extreme_return_rows": int(extreme_return.sum()),
        "minimum_daily_return": float(daily_return.min()),
        "maximum_daily_return": float(daily_return.max()),
    }
