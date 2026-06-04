# Postprocess phase (4)

Normalizes field types and filters records to the warehouse schema before database write.

**Entry point:** `run.py` → `run_postprocess`

---

## Data flow

```
List[WarehouseRecord]  ──►  run_postprocess  ──►  List[WarehouseRecord]
                              (single loop: skip invalid id, cast types, project schema)
```

---

## `run.py`

### `run_postprocess`

| | |
|---|---|
| **Input** | `records: List[Dict[str, Any]]` — enriched warehouse records |
| **Output** | `List[Dict[str, Any]]` — normalized, schema-valid records only |
| **Side effects** | none |

Per record: skip if no `id`; cast `set_total_cards` to `int` and price columns to `float` (`None` → `NaN`); keep only `config.SCHEMA_COLUMNS`.
