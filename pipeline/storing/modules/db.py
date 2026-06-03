import math
from datetime import date
from typing import Any, Dict, List, Set

import click
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

import config

TABLE_NAME = "card_prices"
COLLECTION_TABLE = "user_collection"


def get_engine(database_url: str) -> Engine:
    '''Create a SQLAlchemy engine for the given database URL.'''
    return create_engine(database_url, future=True)


def _column_type(col: str) -> str:
    if col in {
        "snapshot_date", "id", "name", "rarity", "set_number",
        "image_url", "set_id", "set_name", "set_release_date", "illustrator",
    }:
        return "TEXT"
    if col in {"set_total_cards", "dex_id"}:
        return "INTEGER"
    return "REAL"


def _existing_columns(engine: Engine, table: str) -> set:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {row[1] for row in rows}


def _migrate_columns(engine: Engine) -> None:
    existing = _existing_columns(engine, TABLE_NAME)
    if not existing:
        return

    for col in config.SCHEMA_COLUMNS:
        if col not in existing:
            with engine.begin() as conn:
                conn.execute(
                    text(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {col} {_column_type(col)}")
                )


def init_table(engine: Engine) -> None:
    '''Create the card_prices table if it does not exist and migrate new columns.'''
    columns_sql = ",\n        ".join(
        f"{col} {_column_type(col)}" for col in config.SCHEMA_COLUMNS
    )
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        {columns_sql},
        PRIMARY KEY (snapshot_date, id)
    )
    """
    idx_set = f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_set_id ON {TABLE_NAME} (set_id)"
    idx_name = f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_name ON {TABLE_NAME} (name)"
    with engine.begin() as conn:
        conn.execute(text(ddl))
        conn.execute(text(idx_set))
        conn.execute(text(idx_name))

    _migrate_columns(engine)


def init_collection_table(engine: Engine) -> None:
    '''Create the user_collection table for the RQ4 frontend.'''
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


def _rows_to_frame(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=config.SCHEMA_COLUMNS)
    for col in df.columns:
        if col in {"set_total_cards", "dex_id"}:
            df[col] = df[col].apply(
                lambda v: None
                if v is None or (isinstance(v, float) and math.isnan(v))
                else int(v)
            )
        elif col.startswith("price_") or col == "market_price":
            df[col] = df[col].apply(
                lambda v: None
                if v is None or (isinstance(v, float) and math.isnan(v))
                else float(v)
            )
    return df


def write_idempotent(engine: Engine, snapshot_date: date, rows: List[Dict[str, Any]]) -> None:
    '''Replace all rows for snapshot_date in the database.'''
    if not rows:
        click.echo("No rows to write to database.", err=True)
        return

    init_table(engine)
    init_collection_table(engine)
    date_col = snapshot_date.isoformat()
    df = _rows_to_frame(rows)

    with engine.begin() as conn:
        conn.execute(
            text(f"DELETE FROM {TABLE_NAME} WHERE snapshot_date = :snapshot_date"),
            {"snapshot_date": date_col},
        )
        df.to_sql(TABLE_NAME, conn, if_exists="append", index=False, method="multi")

    click.echo(f"Wrote {len(df)} rows to {TABLE_NAME} ({date_col})")


def write_append(engine: Engine, snapshot_date: date, rows: List[Dict[str, Any]]) -> None:
    '''Upsert rows without removing other cards from the same snapshot date.'''
    if not rows:
        click.echo("No rows to write to database.", err=True)
        return

    init_table(engine)
    init_collection_table(engine)
    date_col = snapshot_date.isoformat()
    df = _rows_to_frame(rows)
    cols = ", ".join(config.SCHEMA_COLUMNS)
    params = ", ".join(f":{col}" for col in config.SCHEMA_COLUMNS)

    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text(f"INSERT OR REPLACE INTO {TABLE_NAME} ({cols}) VALUES ({params})"),
                row.to_dict(),
            )

    click.echo(f"Upserted {len(df)} rows in {TABLE_NAME} ({date_col})")


def load_stored_set_ids(engine: Engine) -> set:
    '''Return set IDs present in the SQL database.'''
    init_table(engine)
    with engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT DISTINCT set_id FROM {TABLE_NAME} WHERE set_id IS NOT NULL")
        )
        return {str(row[0]) for row in result}


def load_stored_set_ids_from_db(database_url: str) -> set:
    '''Return set IDs present in the SQL database.'''
    return load_stored_set_ids(get_engine(database_url))


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
    '''Mark a card as owned in the user collection.'''
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
    '''Remove a card from the user collection.'''
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
