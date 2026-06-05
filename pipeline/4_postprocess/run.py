from typing import Any, Dict, List

import config


def run_postprocess(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    '''Normalize field types then keep only valid schema records.'''
    price_cols = [col for col, sql_type in config.SCHEMA_COLUMNS.items() if sql_type == "REAL"]
    valid = []
    for record in records:
        row = dict(record)
        if row.get("set_total_cards") is not None:
            row["set_total_cards"] = int(row["set_total_cards"])
        for col in price_cols:
            row[col] = float("nan") if row.get(col) is None else float(row[col])
        valid.append({col: row.get(col) for col in config.SCHEMA_COLUMNS})
    return valid
