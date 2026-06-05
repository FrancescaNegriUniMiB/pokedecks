import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import pandas as pd

from util.query import get_engine, load_snapshot

from .modules.exclusions import suspicious_sets
from .modules.metrics import completeness_metrics, validity_metrics
from .modules.report import format_quality_summary


def _top_sets_missing_price(df: pd.DataFrame, top_n: int = 10) -> List[Dict[str, Any]]:
    missing = df[df["market_price"].isna() & df["set_id"].notna()]
    counts = (
        missing.groupby(["set_id", "set_name"], dropna=False)
        .size()
        .reset_index(name="missing_count")
        .sort_values("missing_count", ascending=False)
        .head(top_n)
    )
    return counts.to_dict(orient="records")


def run_quality(
        snapshot_date: str,
        database_url: str,
        output_dir: Path,
        before_enrichment: Optional[Dict[str, Any]] = None,
        integration_metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
    '''Run quality checks for a snapshot and write report files.'''
    engine = get_engine(database_url)
    df = load_snapshot(snapshot_date, engine)

    if df.empty:
        click.echo(f"No data for snapshot {snapshot_date}.", err=True)
        return {}

    suspicious = suspicious_sets(df)
    summary = {
        "completeness": completeness_metrics(df),
        "validity": validity_metrics(df),
        "suspicious_sets_count": len(suspicious),
        "top_sets_missing_price": _top_sets_missing_price(df),
        "suspicious_sets": suspicious.to_dict(orient="records"),
        "snapshot_date": snapshot_date,
        "after_enrichment": None,
    }
    summary["after_enrichment"] = summary["completeness"]
    if before_enrichment:
        summary["before_enrichment"] = before_enrichment
    if integration_metrics:
        summary["integration"] = integration_metrics

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, Path] = {}

    missing_path = output_dir / f"missing_market_price_{snapshot_date}.csv"
    df[df["market_price"].isna()].to_csv(missing_path, index=False)
    paths["missing_market_price"] = missing_path

    summary_path = output_dir / f"summary_{snapshot_date}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    paths["summary"] = summary_path

    log_path = output_dir / f"quality_{snapshot_date}.log"
    paths["quality_log"] = log_path
    report = format_quality_summary(summary, paths, before_enrichment)
    log_path.write_text(report, encoding="utf-8")
    click.echo(report)
    return summary
