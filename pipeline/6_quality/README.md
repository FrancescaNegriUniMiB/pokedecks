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

## Modules

| Module | Role |
|--------|------|
| `modules/metrics.py` | `completeness_metrics`, `validity_metrics` |
| `modules/exclusions.py` | `suspicious_sets`, `analysis_excluded_set_ids`, `analysis_frame` (used by 7_analysis) |

## `run.py`

| Function | Role |
|----------|------|
| `run_quality` | Load snapshot, compute metrics, export CSV/JSON, print summary |
| `build_integration_metrics` | Integration JSON payload from 3_enrichment counts + failed IDs |
| `export_integration_metrics` | Writes `integration_{date}.json` |

**Internal helpers:** `_top_sets_missing_price` (in `run.py`)

### Suspicious set rule

`mean(market_price) > SUSPICIOUS_SET_MEAN_THRESHOLD` AND `stddev < SUSPICIOUS_SET_STDDEV_THRESHOLD`

---

## Output files

| File | Content |
|------|---------|
| `missing_market_price_{date}.csv` | Rows with null `market_price` |
| `summary_{date}.json` | All aggregate metrics (includes `suspicious_sets` records) |
