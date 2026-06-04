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
| `db.py` | engine, `card_prices` schema, writes, set-id lookup for acquisition |
| `collection.py` | `user_collection` table and CRUD (RQ4 frontend) |
