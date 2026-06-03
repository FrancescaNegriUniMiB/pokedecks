# Storing phase

Writes records to the **SQL database** and provides query helpers.

**Entry point:** `run.py` → `run_storing`

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
| `db.py` | schema init, writes, set-id lookup, user collection CRUD |
| `query.py` | read helpers: `load_snapshot`, `search_cards`, `get_set_completion_cost`, … |
