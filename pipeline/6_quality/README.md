# Quality phase

Post-load data quality checks on a stored snapshot.

**Entry point:** `run.py` → `run_quality`

**Standalone:** `scripts/pipeline/quality.py`

---

## Data flow

```
SQL card_prices  ──►  run_quality  ──►  quality_{date}.log + terminal + data/quality/*.csv/json
```

---

## Modules

| Module | Role |
|--------|------|
| `modules/metrics.py` | `completeness_metrics`, `validity_metrics` |
| `modules/exclusions.py` | `suspicious_sets`, `analysis_excluded_set_ids`, `analysis_frame` (used by 7_analysis) |
| `modules/report.py` | `format_quality_summary` — human-readable log/terminal report |

## `run.py`

| Function | Role |
|----------|------|
| `run_quality` | Load snapshot, compute metrics, export CSV/JSON/log, echo summary |

**Internal helpers:** `_top_sets_missing_price` (in `run.py`)

Integration metrics (`integration_{date}.json`) are built and exported by `scripts/pipeline/run.py` after enrichment, then passed into `run_quality` as `integration_metrics`.

### Suspicious set rule

`mean(market_price) > SUSPICIOUS_SET_MEAN_THRESHOLD` AND `stddev < SUSPICIOUS_SET_STDDEV_THRESHOLD`

---

## Output files

| File | Content |
|------|---------|
| `quality_{date}.log` | Human-readable report (same text echoed to terminal) |
| `missing_market_price_{date}.csv` | Rows with null `market_price` |
| `summary_{date}.json` | All aggregate metrics (includes `suspicious_sets` records) |
| `integration_{date}.json` | Written by `scripts/pipeline/run.py` after enrichment; copied into `summary` when present |
