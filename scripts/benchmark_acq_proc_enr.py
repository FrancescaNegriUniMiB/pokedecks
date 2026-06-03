#!/usr/bin/env python3
'''Benchmark acquisition + processing + enrichment with per-phase timings.'''

import asyncio
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from pipeline.acquisition.run import run_acquisition
from pipeline.enrichment.run import run_enrichment
from pipeline.processing.run import run_processing
from pipeline.quality.run import completeness_from_records


def fmt(seconds: float) -> str:
    m, s = divmod(int(round(seconds)), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"


def main() -> None:
    snapshot = date.today()
    t_total = time.perf_counter()

    print(f"=== Phase 1/3: acquisition (mode=full, date={snapshot}) ===")
    t0 = time.perf_counter()
    acquired, failed_ids = run_acquisition("full", config.DEFAULT_DATABASE_URL)
    t_acq = time.perf_counter() - t0
    print(f"Acquisition: {len(acquired)} acquired, {len(failed_ids)} failed — {fmt(t_acq)}")

    print("\n=== Phase 2/3: processing ===")
    t0 = time.perf_counter()
    records = run_processing(snapshot, acquired)
    before = completeness_from_records(records)
    t_proc = time.perf_counter() - t0
    print(
        f"Processing: {len(records)} records, "
        f"{before['market_price_filled_pct']} with market_price — {fmt(t_proc)}"
    )

    print("\n=== Phase 3/3: enrichment ===")
    t0 = time.perf_counter()
    records, enriched_pc, enriched_ebay = asyncio.run(run_enrichment(records))
    after = completeness_from_records(records)
    t_enr = time.perf_counter() - t0
    print(
        f"Enrichment: {before['market_price_filled_pct']} -> "
        f"{after['market_price_filled_pct']} market_price — {fmt(t_enr)}"
    )
    print(
        f"  PC={enriched_pc}, eBay={enriched_ebay}, "
        f"still missing={after['market_price_missing']}"
    )

    t_all = time.perf_counter() - t_total
    print("\n=== TIMING SUMMARY ===")
    print(f"  Acquisition : {fmt(t_acq)} ({t_acq:.1f}s)")
    print(f"  Processing  : {fmt(t_proc)} ({t_proc:.1f}s)")
    print(f"  Enrichment  : {fmt(t_enr)} ({t_enr:.1f}s)")
    print(f"  TOTAL       : {fmt(t_all)} ({t_all:.1f}s)")


if __name__ == "__main__":
    main()
