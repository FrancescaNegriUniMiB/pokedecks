from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


def load_snapshot(snapshot_date: str, engine: Engine) -> pd.DataFrame:
    '''Load all rows for a specific snapshot date from SQL.'''
    query = text(
        "SELECT * FROM card_prices WHERE snapshot_date = :snapshot_date ORDER BY id"
    )
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"snapshot_date": snapshot_date})


def search_cards(name: str, engine: Engine, limit: int = 50) -> pd.DataFrame:
    '''Search cards by name across all stored snapshots.'''
    query = text(
        """
        SELECT * FROM card_prices
        WHERE name LIKE :pattern
        ORDER BY snapshot_date DESC, id
        LIMIT :limit
        """
    )
    with engine.connect() as conn:
        return pd.read_sql(
            query, conn, params={"pattern": f"%{name}%", "limit": limit}
        )


def get_card_history(card_id: str, engine: Engine) -> pd.DataFrame:
    '''Return price history for a single card across all snapshots.'''
    query = text(
        """
        SELECT * FROM card_prices
        WHERE id = :card_id
        ORDER BY snapshot_date
        """
    )
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"card_id": card_id})


def list_sets(snapshot_date: str, engine: Engine) -> pd.DataFrame:
    '''Return distinct sets for a snapshot date.'''
    query = text(
        """
        SELECT DISTINCT set_id, set_name
        FROM card_prices
        WHERE snapshot_date = :snapshot_date AND set_id IS NOT NULL
        ORDER BY set_name
        """
    )
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"snapshot_date": snapshot_date})


def get_set_cards(set_id: str, snapshot_date: str, engine: Engine) -> pd.DataFrame:
    '''Return all cards in a set for a snapshot date.'''
    query = text(
        """
        SELECT * FROM card_prices
        WHERE set_id = :set_id AND snapshot_date = :snapshot_date
        ORDER BY set_number, id
        """
    )
    with engine.connect() as conn:
        return pd.read_sql(
            query,
            conn,
            params={"set_id": set_id, "snapshot_date": snapshot_date},
        )


def get_set_completion_cost(
        set_id: str,
        snapshot_date: str,
        engine: Engine,
        owned_card_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
    '''Compute total, owned and remaining completion cost for a set.'''
    cards = get_set_cards(set_id, snapshot_date, engine)
    priced = cards[cards["market_price"].notna()]
    total_cost = float(priced["market_price"].sum())
    missing_price_count = int(cards["market_price"].isna().sum())

    owned_ids = set(owned_card_ids or [])
    owned = priced[priced["id"].isin(owned_ids)]
    owned_cost = float(owned["market_price"].sum())
    remaining = priced[~priced["id"].isin(owned_ids)]
    remaining_cost = float(remaining["market_price"].sum())

    return {
        "set_id": set_id,
        "snapshot_date": snapshot_date,
        "total_cards": len(cards),
        "priced_cards": len(priced),
        "missing_price_count": missing_price_count,
        "total_cost": total_cost,
        "owned_cost": owned_cost,
        "remaining_cost": remaining_cost,
        "owned_count": len(owned_ids & set(priced["id"])),
    }
