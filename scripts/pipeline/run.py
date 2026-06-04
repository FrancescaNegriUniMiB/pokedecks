#!/usr/bin/env python3

import asyncio
import sys
from datetime import date
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import click

import config
from pipeline import import_phase

_run_acquisition = import_phase("1_acquisition.run")
_run_preprocess = import_phase("2_preprocess.run")
_run_enrichment = import_phase("3_enrichment.run")
_run_postprocess = import_phase("4_postprocess.run")
_run_storing = import_phase("5_storing.run")
_quality = import_phase("6_quality.run")
_run_analysis = import_phase("7_analysis.run")

run_acquisition = _run_acquisition.run_acquisition
run_preprocess = _run_preprocess.run_preprocess
run_enrichment = _run_enrichment.run_enrichment
run_postprocess = _run_postprocess.run_postprocess
run_storing = _run_storing.run_storing
run_quality = _quality.run_quality
build_integration_metrics = _quality.build_integration_metrics
completeness_from_records = _quality.completeness_from_records
export_integration_metrics = _quality.export_integration_metrics
run_analysis = _run_analysis.run_analysis


def run_pipeline(
        snapshot_date: date,
        database_url: str,
        mode: str = "full",
        skip_quality: bool = False,
        skip_analysis: bool = False,
        quality_dir: Optional[Path] = None,
        analysis_dir: Optional[Path] = None,
    ) -> None:
    '''
    Run the full PokeDecks pipeline including quality checks and analysis.
    '''
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "", 1)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    quality_path = quality_dir or Path(config.DEFAULT_QUALITY_DIR)
    analysis_path = analysis_dir or Path(config.DEFAULT_ANALYSIS_DIR)
    date_str = snapshot_date.isoformat()

    click.echo(f"\n=== Phase 1/7: 1_acquisition (mode={mode}, date={date_str}) ===")
    acquired, failed_ids = run_acquisition(mode, database_url)

    if not acquired:
        click.echo("Nothing to process.")
        return

    click.echo("\n=== Phase 2/7: 2_preprocess ===")
    records = run_preprocess(snapshot_date, acquired)
    before_enrichment = completeness_from_records(records)
    click.echo(
        f"Preprocess: {len(records)} records, "
        f"{before_enrichment['market_price_filled_pct']} with market_price (API only)"
    )

    click.echo("\n=== Phase 3/7: 3_enrichment ===")
    records, enriched_pc, enriched_ebay = asyncio.run(run_enrichment(records))
    after_enrichment = completeness_from_records(records)
    integration_metrics = build_integration_metrics(
        len(records),
        before_enrichment["market_price_missing"],
        enriched_pc,
        enriched_ebay,
        after_enrichment["market_price_missing"],
        failed_ids,
    )
    export_integration_metrics(date_str, quality_path, integration_metrics)

    click.echo(
        f"Enrichment delta: "
        f"{before_enrichment['market_price_filled_pct']} -> "
        f"{after_enrichment['market_price_filled_pct']} market_price filled"
    )

    click.echo("\n=== Phase 4/7: 4_postprocess ===")
    cleaned = run_postprocess(records)
    click.echo(f"Postprocess: {len(cleaned)} records passed validation")

    click.echo("\n=== Phase 5/7: 5_storing ===")
    run_storing(snapshot_date, database_url, cleaned, failed_ids, mode=mode)

    if not skip_quality:
        click.echo("\n=== Phase 6/7: 6_quality ===")
        run_quality(
            date_str,
            database_url,
            quality_path,
            before_enrichment=before_enrichment,
            integration_metrics=integration_metrics,
        )

    if not skip_analysis:
        click.echo("\n=== Phase 7/7: 7_analysis ===")
        run_analysis(date_str, database_url, analysis_path)

    click.echo(f"\nPipeline complete for snapshot {date_str}.")


@click.command()
@click.option(
    "--mode",
    type=click.Choice(["full", "update"]),
    default="full",
    help="full: fetch all cards. update: fetch only sets not yet in database.",
)
@click.option(
    "--date",
    "snapshot_date",
    default=lambda: date.today().isoformat(),
    help="Snapshot date stamped on records (ISO). Default is today.",
)
@click.option(
    "--database-url",
    default=config.DEFAULT_DATABASE_URL,
    help="SQLAlchemy database URL (default: sqlite:///./data/pokedecks.db).",
)
@click.option(
    "--quality-dir",
    default=config.DEFAULT_QUALITY_DIR,
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    help="Directory for quality report files.",
)
@click.option(
    "--analysis-dir",
    default=config.DEFAULT_ANALYSIS_DIR,
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    help="Directory for analysis output files.",
)
@click.option(
    "--skip-quality",
    is_flag=True,
    default=False,
    help="Skip the quality check phase after storing.",
)
@click.option(
    "--skip-analysis",
    is_flag=True,
    default=False,
    help="Skip the analysis phase after quality checks.",
)
def main(
        mode: str,
        snapshot_date: str,
        database_url: str,
        quality_dir: str,
        analysis_dir: str,
        skip_quality: bool,
        skip_analysis: bool,
    ) -> None:
    '''
    PokeDecks: build a Pokémon card price database.
    '''
    run_pipeline(
        date.fromisoformat(snapshot_date),
        database_url,
        mode=mode,
        skip_quality=skip_quality,
        skip_analysis=skip_analysis,
        quality_dir=Path(quality_dir),
        analysis_dir=Path(analysis_dir),
    )


if __name__ == "__main__":
    main()
