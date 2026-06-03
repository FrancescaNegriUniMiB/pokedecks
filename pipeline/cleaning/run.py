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


def _normalize(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    '''Cast record fields to the expected warehouse types.'''
    normalized = []
    for record in records:
        row = dict(record)
        total = row.get("set_total_cards")
        if total is not None:
            row["set_total_cards"] = int(total)
        for col in _PRICE_COLUMNS:
            val = row.get(col)
            row[col] = float("nan") if val is None else float(val)
        normalized.append(row)
    return normalized


def _validate(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    '''Keep only records with a valid id and the expected schema columns.'''
    valid = []
    for record in records:
        if not record.get("id"):
            continue
        valid.append({col: record.get(col) for col in config.SCHEMA_COLUMNS})
    return valid


def run_cleaning(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    '''Normalize field types then keep only valid schema records.'''
    return _validate(_normalize(records))
