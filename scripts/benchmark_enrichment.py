#!/usr/bin/env python3
'''Benchmark enrichment only, using pre-processing records rebuilt from SQLite.'''

import asyncio
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import click
import pandas as pd
from sqlalchemy import create_engine

import config
from pipeline.enrichment.run import run_enrichment
from pipeline.quality.run import completeness_from_records

BASELINE_ENRICHMENT_SEC = 3690.9
BASELINE_MISSING = 3922


def fmt(seconds: float) -> str:
    m, s = divmod(int(round(seconds)), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"


def _num(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def load_pre_enrichment_records(
        database_url: str,
        snapshot_date: str,
        limit_missing: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
    '''Load warehouse rows and reset them to post-processing state (API prices only).'''
    engine = create_engine(database_url, future=True)
    df = pd.read_sql(
        "SELECT * FROM card_prices WHERE snapshot_date = :d",
        engine,
        params={"d": snapshot_date},
    )
    records = df.where(pd.notnull(df), None).to_dict("records")

    for record in records:
        cm_avg = _num(record.get("price_cardmarket_avg"))
        tcg_market = _num(record.get("price_tcgplayer_market"))
        record["market_price"] = max(cm_avg or 0, tcg_market or 0) or None
        record["price_ungraded"] = None
        record["price_psa10"] = None
        record["price_graded_avg"] = None

    if limit_missing is None:
        return records

    missing = [r for r in records if r.get("market_price") is None]
    keep_ids = {r["id"] for r in missing[:limit_missing]}
    return [
        r for r in records
        if r.get("market_price") is not None or r.get("id") in keep_ids
    ]


@click.command()
@click.option(
    "--snapshot-date",
    default="2026-05-31",
    show_default=True,
    help="Snapshot to load from SQLite (pre-enrichment state is rebuilt from API price columns).",
)
@click.option(
    "--database-url",
    default=config.DEFAULT_DATABASE_URL,
    show_default=True,
    help="SQLAlchemy database URL.",
)
@click.option(
    "--limit-missing",
    type=int,
    default=None,
    help="If set, enrich only the first N cards missing market_price (quick smoke test).",
)
@click.option(
    "--baseline-seconds",
    type=float,
    default=BASELINE_ENRICHMENT_SEC,
    show_default=True,
    help="Previous full enrichment duration to compare against (seconds).",
)
def main(
        snapshot_date: str,
        database_url: str,
        limit_missing: Optional[int],
        baseline_seconds: float,
    ) -> None:
    '''Run enrichment in isolation and print timing vs baseline.'''
    records = load_pre_enrichment_records(database_url, snapshot_date, limit_missing)
    before = completeness_from_records(records)
    missing = sum(1 for r in records if r.get("market_price") is None)

    click.echo(
        f"Loaded {len(records)} records from {snapshot_date} "
        f"({missing} missing market_price, {before['market_price_filled_pct']} API-filled)"
    )
    if limit_missing:
        click.echo(f"Limit: enriching up to {limit_missing} missing cards only")

    t0 = time.perf_counter()
    _, enriched_pc, enriched_ebay = asyncio.run(run_enrichment(records))
    elapsed = time.perf_counter() - t0
    after = completeness_from_records(records)

    delta = baseline_seconds - elapsed
    click.echo(
        f"\nEnrichment: {before['market_price_filled_pct']} -> "
        f"{after['market_price_filled_pct']} market_price — {fmt(elapsed)} ({elapsed:.1f}s)"
    )
    click.echo(
        f"  PC={enriched_pc}, eBay={enriched_ebay}, "
        f"still missing={after['market_price_missing']}"
    )
    click.echo("\n=== ENRICHMENT BENCHMARK ===")
    click.echo(f"  This run   : {fmt(elapsed)} ({elapsed:.1f}s)")
    click.echo(f"  Baseline   : {fmt(baseline_seconds)} ({baseline_seconds:.1f}s)  [pre-refactor, ~{BASELINE_MISSING} missing]")
    if limit_missing is None:
        click.echo(f"  Delta      : {fmt(abs(delta))} {'faster' if delta > 0 else 'slower'}")


if __name__ == "__main__":
    main()
