from typing import Any, Dict

import pandas as pd

PRICE_SOURCE_COLUMNS = (
    "price_cardmarket_avg",
    "price_tcgplayer_market",
    "price_ungraded",
    "price_psa10",
    "price_graded_avg",
)


def completeness_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    '''How many cards have key fields and price sources populated.'''
    total = len(df)
    market_filled = int(df["market_price"].notna().sum())

    return {
        "total_cards": total,
        "market_price_filled": market_filled,
        "market_price_filled_pct": f"{100 * market_filled / total:.1f}%" if total else "0.0%",
        "market_price_missing": total - market_filled,
        "market_price_missing_pct": f"{100 * (total - market_filled) / total:.1f}%" if total else "0.0%",
        "missing_name": int(df["name"].isna().sum()),
        "missing_set_id": int(df["set_id"].isna().sum()),
        "price_source_breakdown": {
            col: {
                "count": (n := int(df[col].notna().sum())),
                "pct": f"{100 * n / total:.1f}%" if total else "0.0%",
            }
            for col in PRICE_SOURCE_COLUMNS
        },
    }


def validity_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    '''Distribution and sanity checks on populated market_price values.'''
    priced = df.loc[df["market_price"].notna(), "market_price"]
    stats = priced.describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.99])
    return {
        "non_positive_prices": int((priced <= 0).sum()),
        "distribution": {k: float(v) for k, v in stats.to_dict().items()},
    }
