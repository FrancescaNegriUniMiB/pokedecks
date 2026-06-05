# Analysis phase

Research-question analysis on stored snapshots (RQ1–RQ3).

**Entry point:** `run.py` → `run_analysis`

**Standalone:** `scripts/pipeline/analyze.py`

---

## Data flow

```
SQL card_prices  ──►  util.query.load_snapshot  ──►  run_analysis  ──►  data/analysis/{date}/*.png
                                                                              │
                                                                              └──►  frontend/analysis_app.py
```

---

## Modules

| Module | RQ | Output |
|--------|-----|--------|
| `rq1_value_drivers.py` | Price drivers (rarity, age, pokemon, illustrator) | 4 PNG + metrics |
| `rq2_expensive_cards.py` | Expensive card distribution by release year | 1 PNG + metrics |
| `rq3_set_cost_trend.py` | Set completion cost vs release year | 1 PNG + metrics |

Exclusions via `6_quality.modules.exclusions` (`tk-*` prefixes + `suspicious_sets`), imported in `run.py` as `_exclusions` only. Listed in `analysis_summary.json` → `excluded_set_ids`. Cross-sectional methodology (same market snapshot, different release years).

## `run.py`

| Function | Role |
|----------|------|
| `run_analysis` | Load snapshot, build priced frame, run RQ1–RQ3, write `analysis_summary.json` |
