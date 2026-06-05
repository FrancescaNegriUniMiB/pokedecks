import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import pandas as pd

from util.query import get_engine, load_snapshot

from .modules.exclusions import suspicious_sets
from .modules.metrics import completeness_metrics, validity_metrics


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


def build_integration_metrics(
        total_cards: int,
        missing_before: int,
        enriched_via_pricecharting: int,
        enriched_via_ebay: int,
        still_missing_after: int,
        acquisition_failed_ids: List[str],
    ) -> Dict[str, Any]:
    '''Build integration/enrichment metrics for a pipeline run.'''
    enriched_total = enriched_via_pricecharting + enriched_via_ebay
    success_rate = (
        f"{100 * enriched_total / missing_before:.1f}%"
        if missing_before
        else "0.0%"
    )
    return {
        "total_cards": total_cards,
        "missing_before_enrichment": missing_before,
        "enriched_via_pricecharting": enriched_via_pricecharting,
        "enriched_via_ebay": enriched_via_ebay,
        "enriched_total": enriched_total,
        "still_missing_after": still_missing_after,
        "enrichment_success_rate": success_rate,
        "acquisition_failed_ids": len(acquisition_failed_ids),
        "acquisition_failed_id_list": acquisition_failed_ids,
    }


def export_integration_metrics(
        snapshot_date: str,
        output_dir: Path,
        metrics: Dict[str, Any],
    ) -> Path:
    '''Write integration metrics JSON to the quality output directory.'''
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"integration_{snapshot_date}.json"
    payload = {"snapshot_date": snapshot_date, **metrics}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def _print_quality_summary(
        summary: Dict[str, Any],
        paths: Dict[str, Path],
        before_enrichment: Optional[Dict[str, Any]],
    ) -> None:
    '''Print quality report sections to the terminal.'''
    comp = summary["completeness"]
    val = summary["validity"]

    click.echo("\n--- 1. Completeness ---")
    click.echo(f"Total cards: {comp['total_cards']}")
    click.echo(
        f"Market price filled: {comp['market_price_filled']} ({comp['market_price_filled_pct']})"
    )
    click.echo(
        f"Market price missing: {comp['market_price_missing']} ({comp['market_price_missing_pct']})"
    )
    click.echo(f"Missing name: {comp['missing_name']}, missing set_id: {comp['missing_set_id']}")
    click.echo("\nPrice source breakdown:")
    for col, stats in comp["price_source_breakdown"].items():
        click.echo(f"  - {col}: {stats['count']} ({stats['pct']})")

    click.echo("\n--- 2. Price validity ---")
    click.echo(f"Non-positive market_price: {val['non_positive_prices']}")
    if val["distribution"]:
        click.echo("Distribution:")
        for key, value in val["distribution"].items():
            click.echo(f"  {key}: {value:.4f}")

    click.echo("\n--- 3. Suspicious sets ---")
    click.echo(f"Flagged sets: {summary['suspicious_sets_count']}")
    for row in summary["suspicious_sets"][:5]:
        click.echo(
            f"  {row['set_id']} ({row.get('set_name')}): "
            f"mean={row['mean']:.2f}, std={row['std']:.4f}, n={row['count']}"
        )

    click.echo("\n--- 4. Top sets missing market_price ---")
    for row in summary["top_sets_missing_price"][:5]:
        click.echo(
            f"  {row['set_id']} ({row.get('set_name')}): {row['missing_count']} cards"
        )

    click.echo("\n--- 5. Exported files ---")
    for label, path in paths.items():
        click.echo(f"  {label}: {path}")

    if before_enrichment:
        before = before_enrichment["market_price_filled_pct"]
        after = summary["after_enrichment"]["market_price_filled_pct"]
        click.echo("\n--- 6. Enrichment delta ---")
        click.echo(f"Market price filled: {before} -> {after}")


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

    _print_quality_summary(summary, paths, before_enrichment)
    return summary
