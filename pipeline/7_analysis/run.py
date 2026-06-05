import json
from pathlib import Path
from typing import Any, Dict

import click

from pipeline import import_phase
from util.query import get_engine, load_snapshot

from .modules.rq1_value_drivers import run_rq1
from .modules.rq2_expensive_cards import run_rq2
from .modules.rq3_set_cost_trend import run_rq3

_exclusions = import_phase("6_quality.modules.exclusions")
analysis_frame = _exclusions.analysis_frame
analysis_excluded_set_ids = _exclusions.analysis_excluded_set_ids


def run_analysis(
        snapshot_date: str,
        database_url: str,
        output_dir: Path,
    ) -> Dict[str, Any]:
    '''Run RQ1–RQ3 analysis and export charts plus summary JSON.'''
    engine = get_engine(database_url)
    df = load_snapshot(snapshot_date, engine)
    if df.empty:
        click.echo(f"No data for snapshot {snapshot_date}.", err=True)
        return {}

    run_dir = output_dir / snapshot_date
    run_dir.mkdir(parents=True, exist_ok=True)

    priced = analysis_frame(df)
    summary = {
        "snapshot_date": snapshot_date,
        "excluded_set_ids": analysis_excluded_set_ids(df),
        "rq1": run_rq1(priced, run_dir),
        "rq2": run_rq2(priced, run_dir),
        "rq3": run_rq3(priced, run_dir),
    }

    summary_path = run_dir / "analysis_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    click.echo(f"Analysis complete: {run_dir}")
    return summary
