# Acquisition phase

Downloads card data from **TCGdex**.

**Entry point:** `run.py` → `run_acquisition`

---

## Run modes

| Mode | Behaviour |
|------|-----------|
| `full` | `fetch_set_list` → `fetch_set_details` on every set |
| `update` | same, but only sets not yet in the database |

---

## Flow

```
run_acquisition
  └─ fetch_set_list()              GET /sets
  └─ fetch_set_details(sets)
       ├─ bar 1 "Sets"             GET /sets/{id} per set %
       └─ bar 2 "Cards"            parallel GET /cards/{id}%
```

---

## `modules/tcgdex.py`

| Function | Description |
|----------|-------------|
| `_request_json` | HTTP GET with retries |
| `fetch_set_list` | Set summary list from `/sets` |
| `fetch_set_details` | Set indexing + card download (`_fetch_cards` nested inside) |
