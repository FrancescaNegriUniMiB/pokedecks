from datetime import date
from typing import Any, Dict, List

from pipeline.processing.modules.build_record import build_record


def run_processing(
        snapshot_date: date,
        acquired: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
    '''Build flat warehouse records from acquired TCGdex details.'''
    return [
        build_record(snapshot_date, detail)
        for detail in acquired
    ]
