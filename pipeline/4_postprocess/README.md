# Postprocess phase (4)

Normalizes field types and filters records to the warehouse schema before database write.

**Entry point:** `run.py` → `run_postprocess`

---

## Data flow

```
List[WarehouseRecord]  ──►  run_postprocess  ──►  List[WarehouseRecord]
                                    │
                                    └── modules/normalize.py
```

---

## Modules

| Module | Role |
|--------|------|
| `modules/normalize.py` | `normalize_records` — cast types, project `config.SCHEMA_COLUMNS` |

## `run.py`

### `run_postprocess`

| | |
|---|---|
| **Input** | `records: List[Dict[str, Any]]` — enriched warehouse records |
| **Output** | `List[Dict[str, Any]]` — normalized, schema-valid records |
| **Side effects** | none |
