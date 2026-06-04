# Quality phase

Post-load data quality checks on a stored snapshot.

**Entry point:** `run.py` → `run_quality`

**Standalone:** `scripts/pipeline/quality.py`

---

## Data flow

```
SQL card_prices  ──►  run_quality  ──►  console summary + data/quality/*.csv/json
```

---

## `run.py`

| Function | Role |
|----------|------|
| `run_quality` | Load snapshot, compute metrics, export CSV/JSON, print summary |
| `completeness_from_records` | Completeness on in-memory pipeline records |
| `build_integration_metrics` | Integration JSON payload from 3_enrichment counts + failed IDs |
| `export_integration_metrics` | Writes `integration_{date}.json` |

**Internal helpers:** `_completeness_metrics`, `_validity_metrics`, `_suspicious_sets`, `_top_sets_missing_price`

### Suspicious set rule

`mean(market_price) > SUSPICIOUS_SET_MEAN_THRESHOLD` AND `stddev < SUSPICIOUS_SET_STDDEV_THRESHOLD`

---

## Output files

| File | Content |
|------|---------|
| `missing_market_price_{date}.csv` | Rows with null `market_price` |
| `suspicious_sets_{date}.csv` | Flagged sets |
| `summary_{date}.json` | All aggregate metrics |
