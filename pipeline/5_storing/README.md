# Storing phase (5)

Writes records to the **SQL database** (pipeline step only).

**Entry point:** `run.py` → `run_storing`

Read helpers live in **`util/query.py`** (outside `pipeline/`).

---

## `run_storing`

| **Input** | |
|-----------|--|
| `snapshot_date` | `date` |
| `database_url` | `str` — SQLAlchemy URL |
| `records` | `List[Dict]` |
| `failed_ids` | `List[str]` |
| `mode` | `"full"` (replace snapshot) or `"update"` (upsert) |

---

## Modules

| File | Role |
|------|------|
| `db.py` | `write(mode=…)` only — schema + insert into `card_prices` |

RQ4 owned-cards CRUD lives in **`util/user_card_collection.py`** (same SQLite file, driven by the frontend).
