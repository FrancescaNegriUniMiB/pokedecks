# Cleaning phase

Normalizes field types and filters records to the warehouse schema before database write.

**Entry point:** `run.py` → `run_cleaning`

---

## Data flow

```
List[WarehouseRecord]  ──►  run_cleaning  ──►  List[WarehouseRecord]
                              _normalize → _validate
```

---

## `run.py`

### `run_cleaning`

| | |
|---|---|
| **Input** | `records: List[Dict[str, Any]]` — enriched warehouse records |
| **Output** | `List[Dict[str, Any]]` — normalized, schema-valid records only |
| **Side effects** | none |

### `_normalize` (internal)

Casts `set_total_cards` to `int` and price columns to `float` (`None` → `NaN`).

### `_validate` (internal)

Drops records without `id`; keeps only keys in `config.SCHEMA_COLUMNS`.
