import math
from datetime import date
from typing import Any, Dict, List

import click
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

import config

TABLE_NAME = "card_prices"


def write(
        engine: Engine,
        snapshot_date: date,
        rows: List[Dict[str, Any]],
        mode: str = "full",
    ) -> None:
    '''Write records to card_prices (full: replace snapshot; update: upsert rows).'''

    def init_table() -> None:
        columns_sql = ",\n        ".join(
            f"{col} {sql_type}" for col, sql_type in config.SCHEMA_COLUMNS.items()
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

        with engine.connect() as conn:
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({TABLE_NAME})"))}
        for col, sql_type in config.SCHEMA_COLUMNS.items():
            if col not in existing:
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            f"ALTER TABLE {TABLE_NAME} ADD COLUMN {col} {sql_type}"
                        )
                    )

    if not rows:
        click.echo("No rows to write to database.", err=True)
        return

    init_table()
    date_col = snapshot_date.isoformat()

    df = pd.DataFrame(rows, columns=list(config.SCHEMA_COLUMNS))
    for col, sql_type in config.SCHEMA_COLUMNS.items():
        if sql_type == "INTEGER":
            df[col] = df[col].apply(
                lambda v: None
                if v is None or (isinstance(v, float) and math.isnan(v))
                else int(v)
            )
        elif sql_type == "REAL":
            df[col] = df[col].apply(
                lambda v: None
                if v is None or (isinstance(v, float) and math.isnan(v))
                else float(v)
            )

    if mode == "update":
        cols = ", ".join(config.SCHEMA_COLUMNS)
        params = ", ".join(f":{col}" for col in config.SCHEMA_COLUMNS)
        with engine.begin() as conn:
            for _, row in df.iterrows():
                conn.execute(
                    text(f"INSERT OR REPLACE INTO {TABLE_NAME} ({cols}) VALUES ({params})"),
                    row.to_dict(),
                )
        click.echo(f"Upserted {len(df)} rows in {TABLE_NAME} ({date_col})")
    else:
        with engine.begin() as conn:
            conn.execute(
                text(f"DELETE FROM {TABLE_NAME} WHERE snapshot_date = :snapshot_date"),
                {"snapshot_date": date_col},
            )
            df.to_sql(TABLE_NAME, conn, if_exists="append", index=False, method="multi")
        click.echo(f"Wrote {len(df)} rows to {TABLE_NAME} ({date_col})")
