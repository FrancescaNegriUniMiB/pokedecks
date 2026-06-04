#!/usr/bin/env python3

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import click

import config
from pipeline import import_phase

run_quality = import_phase("6_quality.run").run_quality


@click.command()
@click.option(
    "--date",
    "snapshot_date",
    default=lambda: date.today().isoformat(),
    help="Snapshot date to check (ISO). Default is today.",
)
@click.option(
    "--database-url",
    default=config.DEFAULT_DATABASE_URL,
    help="SQLAlchemy database URL.",
)
@click.option(
    "--output-dir",
    default=config.DEFAULT_QUALITY_DIR,
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    help="Directory for quality report files.",
)
def main(snapshot_date: str, database_url: str, output_dir: str) -> None:
    '''Run quality checks on a stored snapshot.'''
    run_quality(snapshot_date, database_url, Path(output_dir))


if __name__ == "__main__":
    main()
