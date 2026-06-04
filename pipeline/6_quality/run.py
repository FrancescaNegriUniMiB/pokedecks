import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import pandas as pd

import config
from pipeline import import_phase
from util.query import load_snapshot

get_engine = import_phase("5_storing.modules.db").get_engine


def _pct(n: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{100 * n / total:.1f}%"


def _completeness_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    total = len(df)
    missing_market = int(df["market_price"].isna().sum()) if total else 0
    filled_market = total - missing_market

    breakdown = {}
    for col in [
        "price_cardmarket_avg",
        "price_tcgplayer_market",
        "price_ungraded",
        "price_psa10",
        "price_graded_avg",
    ]:
        if col in df.columns:
            count = int(df[col].notna().sum())
            breakdown[col] = {"count": count, "pct": _pct(count, total)}

    return {
        "total_cards": total,
        "market_price_filled": filled_market,
        "market_price_filled_pct": _pct(filled_market, total),
        "market_price_missing": missing_market,
        "market_price_missing_pct": _pct(missing_market, total),
        "missing_name": int(df["name"].isna().sum()) if "name" in df.columns else 0,
        "missing_set_id": int(df["set_id"].isna().sum()) if "set_id" in df.columns else 0,
        "price_source_breakdown": breakdown,
    }


def _validity_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    priced = df[df["market_price"].notna()].copy()
    if priced.empty:
        return {"non_positive_prices": 0, "distribution": {}}

    non_positive = int((priced["market_price"] <= 0).sum())
    stats = priced["market_price"].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.99])
    return {
        "non_positive_prices": non_positive,
        "distribution": {k: float(v) for k, v in stats.to_dict().items()},
    }


def _suspicious_sets(df: pd.DataFrame) -> pd.DataFrame:
    priced = df[df["market_price"].notna() & df["set_id"].notna()].copy()
    if priced.empty:
        return pd.DataFrame()

    grouped = (
        priced.groupby(["set_id", "set_name"], dropna=False)["market_price"]
        .agg(["count", "mean", "std"])
        .reset_index()
    )
    grouped["std"] = grouped["std"].fillna(0.0)
    mask = (
        (grouped["mean"] > config.SUSPICIOUS_SET_MEAN_THRESHOLD)
        & (grouped["std"] < config.SUSPICIOUS_SET_STDDEV_THRESHOLD)
    )
    return grouped[mask].sort_values("mean", ascending=False)


def _top_sets_missing_price(df: pd.DataFrame, top_n: int = 10) -> List[Dict[str, Any]]:
    missing = df[df["market_price"].isna() & df["set_id"].notna()]
    if missing.empty:
        return []

    counts = (
        missing.groupby(["set_id", "set_name"], dropna=False)
        .size()
        .reset_index(name="missing_count")
        .sort_values("missing_count", ascending=False)
        .head(top_n)
    )
    return counts.to_dict(orient="records")


def completeness_from_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    '''Compute completeness metrics from in-memory pipeline records.'''
    if not records:
        return _completeness_metrics(pd.DataFrame())
    return _completeness_metrics(pd.DataFrame(records))


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

    suspicious = _suspicious_sets(df)
    summary = {
        "completeness": _completeness_metrics(df),
        "validity": _validity_metrics(df),
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

    suspicious_path = output_dir / f"suspicious_sets_{snapshot_date}.csv"
    suspicious.to_csv(suspicious_path, index=False)
    paths["suspicious_sets"] = suspicious_path

    summary_path = output_dir / f"summary_{snapshot_date}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    paths["summary"] = summary_path

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

    return summary
