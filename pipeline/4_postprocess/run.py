from typing import Any, Dict, List

from .modules.normalize import normalize_records


def run_postprocess(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    '''Normalize field types then keep only valid schema records.'''
    return normalize_records(records)
