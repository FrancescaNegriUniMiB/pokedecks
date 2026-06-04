from typing import Any, Dict, List, Tuple

import click

from .modules import tcgdex
from util.query import get_engine, load_stored_set_ids


def run_acquisition(
        mode: str,
        database_url: str,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
    '''Fetch card details from TCGdex: set list → set details → card details.'''
    all_sets = tcgdex.fetch_set_list()
    if not all_sets:
        return [], []

    if mode == "update":
        stored_set_ids = load_stored_set_ids(get_engine(database_url))
        sets_to_fetch = [
            s for s in all_sets if s.get("id") and s["id"] not in stored_set_ids
        ]
        click.echo(
            f"Update: {len(stored_set_ids)} sets in database, "
            f"{len(all_sets)} on TCGdex, {len(sets_to_fetch)} new"
        )
    else:
        sets_to_fetch = [s for s in all_sets if s.get("id")]
        click.echo(f"Full run: {len(sets_to_fetch)} sets from TCGdex list…")

    if not sets_to_fetch:
        return [], []

    acquired, failed_ids = tcgdex.fetch_set_details(sets_to_fetch)
    if not acquired and not failed_ids:
        click.echo("Acquisition: no cards found in selected sets.")
        return [], []

    click.echo(
        f"Acquisition: {len(acquired)} cards with details, "
        f"{len(failed_ids)} failed, {len(sets_to_fetch)} sets processed"
    )
    return acquired, failed_ids
