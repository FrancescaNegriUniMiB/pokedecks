# Analysis phase

Research-question analysis on stored snapshots (RQ1–RQ3).

**Entry point:** `run.py` → `run_analysis`

**Standalone:** `scripts/pipeline/analyze.py`

---

## Data flow

```
SQL card_prices  ──►  run_analysis  ──►  data/analysis/{date}/*.png + analysis_summary.json
                                              │
                                              └──►  frontend/analysis_app.py (viewer)
```

---

## Modules

| Module | RQ | Output |
|--------|-----|--------|
| `rq1_value_drivers.py` | Price drivers (rarity, age, pokemon, illustrator) | 4 PNG + metrics |
| `rq2_expensive_cards.py` | Expensive card distribution by release year | 1 PNG + metrics |
| `rq3_set_cost_trend.py` | Set completion cost vs release year | 1 PNG + metrics |

Trainer kit sets (`tk-*`) are excluded from analysis. Cross-sectional methodology (same market snapshot, different release years).
