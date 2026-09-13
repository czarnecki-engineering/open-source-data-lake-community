from __future__ import annotations

import pandas as pd


CURRENT_UNIVERSE_TREATMENT = "public_yahoo_retrospective"
CURRENT_UNIVERSE_LIMITATION_NOTE = (
    "Universe membership is the configured public Yahoo/yFinance security set; "
    "no point-in-time ASX 200 membership or complete delisting archive is modeled."
)
DATE_SPECIFIC_ELIGIBILITY_NOTE = (
    "Eligibility is date-specific: a ticker becomes eligible only after accumulating "
    "the required observed history in the public research panel."
)


def apply_date_specific_minimum_history_rule(
    prices: pd.DataFrame,
    min_history: int,
    ticker_col: str = "ticker",
    date_col: str = "trade_date",
) -> pd.DataFrame:
    if min_history <= 0:
        raise ValueError("min_history must be positive.")

    required_columns = {ticker_col, date_col}
    missing_columns = required_columns.difference(prices.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Price panel is missing required columns: {missing_list}")

    ordered = prices.copy()
    ordered[date_col] = pd.to_datetime(ordered[date_col])
    ordered = ordered.sort_values([ticker_col, date_col]).reset_index(drop=True)
    ordered["history_count"] = ordered.groupby(ticker_col, observed=True).cumcount() + 1
    ordered["minimum_history_required"] = int(min_history)
    ordered["history_shortfall"] = (min_history - ordered["history_count"]).clip(lower=0)
    ordered["eligible_flag"] = ordered["history_count"] >= min_history
    ordered["first_trade_date"] = ordered.groupby(ticker_col, observed=True)[date_col].transform("min")

    first_eligible_dates = (
        ordered.loc[ordered["eligible_flag"], [ticker_col, date_col]]
        .groupby(ticker_col, observed=True)[date_col]
        .min()
    )
    ordered["first_eligible_trade_date"] = ordered[ticker_col].map(first_eligible_dates)
    return ordered
