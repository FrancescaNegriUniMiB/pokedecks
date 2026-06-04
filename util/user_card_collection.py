'''RQ4: persist which cards a user owns (free-text username, local SQLite).'''

from typing import Set

from sqlalchemy import text
from sqlalchemy.engine import Engine

COLLECTION_TABLE = "user_collection"


def init_collection_table(engine: Engine) -> None:
    '''Create the user_collection table for the RQ4 Streamlit app.'''
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {COLLECTION_TABLE} (
        username TEXT NOT NULL,
        card_id TEXT NOT NULL,
        snapshot_date TEXT NOT NULL,
        PRIMARY KEY (username, card_id, snapshot_date)
    )
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))


def get_owned_card_ids(
        username: str,
        snapshot_date: str,
        engine: Engine,
    ) -> Set[str]:
    '''Return card IDs owned by a user for a snapshot date.'''
    init_collection_table(engine)
    query = text(
        f"""
        SELECT card_id FROM {COLLECTION_TABLE}
        WHERE username = :username AND snapshot_date = :snapshot_date
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(
            query,
            {"username": username, "snapshot_date": snapshot_date},
        ).fetchall()
    return {row[0] for row in rows}


def add_owned_card(
        username: str,
        card_id: str,
        snapshot_date: str,
        engine: Engine,
    ) -> None:
    '''Mark a card as owned in the user card collection.'''
    init_collection_table(engine)
    query = text(
        f"""
        INSERT OR IGNORE INTO {COLLECTION_TABLE} (username, card_id, snapshot_date)
        VALUES (:username, :card_id, :snapshot_date)
        """
    )
    with engine.begin() as conn:
        conn.execute(
            query,
            {"username": username, "card_id": card_id, "snapshot_date": snapshot_date},
        )


def remove_owned_card(
        username: str,
        card_id: str,
        snapshot_date: str,
        engine: Engine,
    ) -> None:
    '''Remove a card from the user card collection.'''
    init_collection_table(engine)
    query = text(
        f"""
        DELETE FROM {COLLECTION_TABLE}
        WHERE username = :username AND card_id = :card_id AND snapshot_date = :snapshot_date
        """
    )
    with engine.begin() as conn:
        conn.execute(
            query,
            {"username": username, "card_id": card_id, "snapshot_date": snapshot_date},
        )
