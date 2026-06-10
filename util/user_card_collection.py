'''RQ4: persist which cards a user owns (free-text username, local SQLite).'''

from typing import Set

from sqlalchemy import text
from sqlalchemy.engine import Engine

COLLECTION_TABLE = "user_collection"


def init_collection_table(engine: Engine) -> None:
    '''Create user_collection and migrate legacy per-snapshot rows if needed.'''
    with engine.begin() as conn:
        existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({COLLECTION_TABLE})"))}
        if not existing:
            conn.execute(text(f"""
                CREATE TABLE {COLLECTION_TABLE} (
                    username TEXT NOT NULL,
                    card_id TEXT NOT NULL,
                    PRIMARY KEY (username, card_id)
                )
            """))
            return
        if "snapshot_date" not in existing:
            return
        conn.execute(text(f"""
            CREATE TABLE _user_collection_new (
                username TEXT NOT NULL,
                card_id TEXT NOT NULL,
                PRIMARY KEY (username, card_id)
            )
        """))
        conn.execute(text(f"""
            INSERT OR IGNORE INTO _user_collection_new (username, card_id)
            SELECT username, card_id FROM {COLLECTION_TABLE}
        """))
        conn.execute(text(f"DROP TABLE {COLLECTION_TABLE}"))
        conn.execute(text(f"ALTER TABLE _user_collection_new RENAME TO {COLLECTION_TABLE}"))


def get_owned_card_ids(username: str, engine: Engine) -> Set[str]:
    '''Return card IDs owned by a user (independent of price snapshot).'''
    init_collection_table(engine)
    query = text(
        f"""
        SELECT card_id FROM {COLLECTION_TABLE}
        WHERE username = :username
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"username": username}).fetchall()
    return {row[0] for row in rows}


def add_owned_card(username: str, card_id: str, engine: Engine) -> None:
    '''Mark a card as owned in the user card collection.'''
    init_collection_table(engine)
    query = text(
        f"""
        INSERT OR IGNORE INTO {COLLECTION_TABLE} (username, card_id)
        VALUES (:username, :card_id)
        """
    )
    with engine.begin() as conn:
        conn.execute(query, {"username": username, "card_id": card_id})


def remove_owned_card(username: str, card_id: str, engine: Engine) -> None:
    '''Remove a card from the user card collection.'''
    init_collection_table(engine)
    query = text(
        f"""
        DELETE FROM {COLLECTION_TABLE}
        WHERE username = :username AND card_id = :card_id
        """
    )
    with engine.begin() as conn:
        conn.execute(query, {"username": username, "card_id": card_id})
