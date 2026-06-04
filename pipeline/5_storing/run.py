from datetime import date
from typing import Any, Dict, List

import click

from .modules import db


def run_storing(
        snapshot_date: date,
        database_url: str,
        records: List[Dict[str, Any]],
        failed_ids: List[str],
        mode: str = "full",
    ) -> None:
    '''Write records to the SQL database.'''
    if failed_ids:
        click.echo(f"Warning: {len(failed_ids)} cards failed to fetch.", err=True)

    if not records:
        click.echo("No records to store.", err=True)
        return

    engine = db.get_engine(database_url)
    if mode == "update":
        db.write_append(engine, snapshot_date, records)
    else:
        db.write_idempotent(engine, snapshot_date, records)
