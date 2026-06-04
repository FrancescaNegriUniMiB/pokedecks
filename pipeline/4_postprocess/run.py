from typing import Any, Dict, List

import config

_PRICE_COLUMNS = [
    "price_cardmarket_avg",
    "price_cardmarket_low",
    "price_cardmarket_trend",
    "price_tcgplayer_market",
    "price_tcgplayer_low",
    "market_price",
    "price_ungraded",
    "price_psa10",
    "price_graded_avg",
]


def run_postprocess(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    '''Normalize field types then keep only valid schema records.'''
    valid = []
    for record in records:
        if not record.get("id"):
            continue
        row = dict(record)
        total = row.get("set_total_cards")
        if total is not None:
            row["set_total_cards"] = int(total)
        for col in _PRICE_COLUMNS:
            val = row.get(col)
            row[col] = float("nan") if val is None else float(val)
        valid.append({col: row.get(col) for col in config.SCHEMA_COLUMNS})
    return valid
