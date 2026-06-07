from datetime import date
from typing import Any, Dict, List

import click
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

import config

TABLE_NAME = "card_prices"
_SQL_CHUNK_SIZE = 999 // len(config.SCHEMA_COLUMNS)


def _init_table(engine: Engine) -> None:
    '''Create card_prices and add any missing schema columns.'''
    columns_sql = ",\n        ".join(
        f"{col} {sql_type}" for col, sql_type in config.SCHEMA_COLUMNS.items()
    )
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        {columns_sql},
        PRIMARY KEY (snapshot_date, id)
    )
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))
        conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_set_id ON {TABLE_NAME} (set_id)"))
        conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_name ON {TABLE_NAME} (name)"))
        existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({TABLE_NAME})"))}
        for col, sql_type in config.SCHEMA_COLUMNS.items():
            if col not in existing:
                conn.execute(text(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {col} {sql_type}"))


def write(
        engine: Engine,
        snapshot_date: date,
        rows: List[Dict[str, Any]],
        mode: str = "full",
    ) -> None:
    '''Write records to card_prices (full: replace snapshot; update: upsert rows).'''
    _init_table(engine)
    date_col = snapshot_date.isoformat()

    df = pd.DataFrame(rows, columns=list(config.SCHEMA_COLUMNS))
    df = df.where(pd.notna(df), None)

    if mode == "update":
        cols = ", ".join(config.SCHEMA_COLUMNS)
        with engine.begin() as conn:
            df.to_sql(
                "_staging", conn, if_exists="replace", index=False,
                method="multi", chunksize=_SQL_CHUNK_SIZE,
            )
            conn.execute(text(f"""
                INSERT OR REPLACE INTO {TABLE_NAME} ({cols})
                SELECT {cols} FROM _staging
            """))
            conn.execute(text("DROP TABLE _staging"))
        click.echo(f"Upserted {len(df)} rows in {TABLE_NAME} ({date_col})")
    else:
        with engine.begin() as conn:
            conn.execute(
                text(f"DELETE FROM {TABLE_NAME} WHERE snapshot_date = :snapshot_date"),
                {"snapshot_date": date_col},
            )
            df.to_sql(
                TABLE_NAME, conn, if_exists="append", index=False,
                method="multi", chunksize=_SQL_CHUNK_SIZE,
            )
        click.echo(f"Wrote {len(df)} rows to {TABLE_NAME} ({date_col})")
