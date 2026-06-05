# PokeDecks 2.0

PokeDecks is a Python data pipeline that extracts Pokémon TCG card prices from TCGdex, enriches missing prices via PriceCharting and eBay, stores everything in a **SQL database**, and answers research questions on the Pokémon card market.

The reference market is **English**.

Every run fetches card data from TCGdex from scratch (`full`) or only new sets (`update`). There is no file cache.

---

## Research questions

Macro-theme: **Pokémon card prices** in the context of growing collectibles culture and scalping among young collectors.


| ID              | Question                                                                                                                                  | Analysis                                                                                           |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **RQ1**         | What makes a card valuable? Age? Rarity? Pokémon depicted? Illustrator?                                                                   | `pipeline/7_analysis/modules/rq1_value_drivers.py` — boxplots, top Pokémon/illustrators, age scatter |
| **RQ2**         | How are expensive cards distributed? Are more high-value cards appearing in recent sets (scalper era), or is it still a niche phenomenon? | `rq2_expensive_cards.py` — count/% cards ≥ $50 by set release year                                 |
| **RQ3**         | Are sets getting more expensive to complete (excluding general inflation)?                                                                | `rq3_set_cost_trend.py` — cross-sectional: avg set completion cost vs release year                 |
| **RQ4** (extra) | How much does it cost to complete a set?                                                                                                  | `frontend/collection_app.py` — select set, mark owned cards, track remaining cost                  |


RQ1–RQ3 use a **cross-sectional** methodology: all prices reflect the same market snapshot; release year is used as a proxy for “era”, not CPI-adjusted time series.

---

## Exam compliance (Data Management)


| Guideline           | Requirement                                                          | PokeDecks coverage                                                   |
| ------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| FAQ 5 — Acquisition | ≥2 sources; API or scraping                                          | TCGdex API + PriceCharting/eBay scraping                             |
| FAQ 6 — Storage     | DBMS + ≥2 queries                                                    | SQLite `card_prices`; `util/query.py` + `scripts/tools/query_examples.py` |
| FAQ 7 — Integration | ≥2 datasets, automated, error metrics                                | Preprocess + enrichment; `scripts/pipeline/run.py` → `integration_{date}.json` |
| FAQ 9 — Quality     | Before/after integration metrics                                     | `summary_{date}.json` with `before_enrichment` / `after_enrichment`  |
| Pipeline            | Acquisition → storage → profiling → integration → analysis → quality | All phases in `pipeline/`                                            |
| Analysis            | Answer research questions                                            | `pipeline/7_analysis/` + Streamlit viewer                            |


---

## Key features

- **Multiple sources** — TCGdex as the primary source; automatic PriceCharting → eBay enrichment only where `market_price` is null.
- **Price coverage** — Cardmarket from the TCGdex API; `market_price = max(cardmarket_avg, tcgplayer_market)`; scrape fallback via PriceCharting/eBay.
- **Two run modes** — `full`: all cards; `update`: only sets not yet in the database.
- **SQL storage** — table `card_prices`, primary key `(snapshot_date, id)`.
- **Quality reports** — post-load checks with before/after enrichment comparison.
- **Analysis phase** — automated RQ1–RQ3 charts and JSON summary.
- **Streamlit apps** — analysis viewer + set completion tracker (RQ4).

---

## Repository structure

```
pokedecks_2.0/
├── scripts/
│   ├── README.md
│   ├── setup.sh              # one-shot setup (macOS / Linux / Git Bash)
│   ├── setup.ps1             # one-shot setup (Windows PowerShell)
│   ├── pipeline/
│   │   ├── run.py            # full pipeline CLI
│   │   ├── analyze.py        # analysis-only CLI
│   │   └── quality.py        # quality-only CLI
│   └── tools/
│       └── query_examples.py
│   └── app/
│       ├── open_report.sh    # launch analysis Streamlit viewer
│       ├── open_collection.sh
│       ├── open_report.ps1
│       └── open_collection.ps1
├── config.py
├── pipeline/               # numbered phases 1–7 only
│   ├── 1_acquisition/
│   ├── 2_preprocess/
│   ├── 3_enrichment/
│   ├── 4_postprocess/
│   ├── 5_storing/
│   ├── 6_quality/
│   └── 7_analysis/
├── util/                   # query.py (engine + reads), user_card_collection.py (RQ4)
├── frontend/
│   ├── analysis_app.py
│   └── collection_app.py
└── data/
    ├── pokedecks.db
    ├── quality/
    └── analysis/
```

```
1_acquisition → 2_preprocess → 3_enrichment → 4_postprocess → 5_storing → 6_quality → 7_analysis
```

---

## Requirements

- Python **3.14.3** (see setup scripts below — pyenv not required)
- Poetry **≥ 2.0** (installed automatically by setup scripts)
- Internet access (TCGdex API + scraping during pipeline runs)
- Dependencies: `requests`, `aiohttp`, `selectolax`, `pandas`, `sqlalchemy`, `click`, `tqdm`, `matplotlib`, `seaborn`, `streamlit`

---

## Installation

### Quick start (developers)

```bash
cd pokedecks_2.0
poetry install
```

### Evaluator / professor setup (recommended)

The database and generated reports (`data/*.db`, `data/quality/`, `data/analysis/`) are **not in git**. For evaluation, use the **submission archive** provided with the project (includes pre-built data), or run a quick demo pipeline (see below).

Pick **one** setup script for your operating system:


| OS                       | Command                                                      |
| ------------------------ | ------------------------------------------------------------ |
| **macOS / Linux**        | `chmod +x scripts/setup.sh && ./scripts/setup.sh`            |
| **Windows (PowerShell)** | `powershell -ExecutionPolicy Bypass -File scripts/setup.ps1` |
| **Windows (Git Bash)**   | same as macOS/Linux                                          |


What the setup script does:

1. Installs **Poetry** if missing (official installer)
2. Ensures **Python 3.14.3** (via pyenv if available, otherwise prints install hints)
3. Runs `**poetry install`**
4. Verifies all dependencies import correctly
5. Checks for `data/pokedecks.db` and prints next steps

#### View the report (after setup + data present)


| OS            | Analysis report (RQ1–RQ3)                                              | Set completion app (RQ4)                                                   |
| ------------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| macOS / Linux | `./scripts/app/open_report.sh`                                         | `./scripts/app/open_collection.sh`                                         |
| Windows       | `powershell -ExecutionPolicy Bypass -File scripts/app/open_report.ps1` | `powershell -ExecutionPolicy Bypass -File scripts/app/open_collection.ps1` |


Opens Streamlit at **[http://localhost:8501](http://localhost:8501)** (browser opens automatically).

#### If no database is present


| Option                 | Time          | Command                                                           |
| ---------------------- | ------------- | ----------------------------------------------------------------- |
| **A — Submission zip** | instant       | Extract archive so `data/pokedecks.db` and `data/analysis/` exist |
| **B — Quick demo**     | not supported | use `--mode update` after a partial run, or submission archive    |
| **C — Full dataset**   | ~1h 15min     | `poetry run python scripts/pipeline/run.py --mode full`           |


#### Manual Python 3.14 install (if setup script stops)


| OS            | Suggested install                                                                                                         |
| ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| macOS         | `brew install python@3.14` or [pyenv](https://github.com/pyenv/pyenv) + `pyenv install 3.14.3`                            |
| Ubuntu/Debian | `sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.14 python3.14-venv`                               |
| Windows       | `winget install Python.Python.3.14` or [python.org downloads](https://www.python.org/downloads/) — enable **Add to PATH** |


Then re-run the setup script for your OS.

#### Other CLI checks (optional)

```bash
poetry run python scripts/tools/query_examples.py          # SQL demo queries (FAQ 6)
poetry run python scripts/pipeline/quality.py --date 2026-05-31
poetry run python scripts/pipeline/analyze.py --date 2026-05-31
```

---

## Usage

```bash
poetry run python scripts/pipeline/run.py [OPTIONS]
```


| Option            | Default                         | Description                                |
| ----------------- | ------------------------------- | ------------------------------------------ |
| `--mode`          | `full`                          | `full`: all cards. `update`: only new sets |
| `--date`          | `today`                         | Date stamped on records (ISO)              |
| `--database-url`  | `sqlite:///./data/pokedecks.db` | SQLAlchemy connection URL                  |
| `--quality-dir`   | `./data/quality`                | Directory for QC report files              |
| `--analysis-dir`  | `./data/analysis`               | Directory for analysis output              |
| `--skip-quality`  | off                             | Skip quality check after storing           |
| `--skip-analysis` | off                             | Skip analysis phase after quality          |


### Expected runtimes


| Scenario                            | Approximate time                  |
| ----------------------------------- | --------------------------------- |
| Full run ~23k cards (`--mode full`) | **~1h 15min** (measured)          |
| `--mode update` (new sets only)     | minutes, proportional to new sets |


### Examples

```bash
# Full pipeline (quality + analysis at end)
poetry run python scripts/pipeline/run.py --mode full

# Analysis only on existing snapshot
poetry run python scripts/pipeline/analyze.py --date 2026-05-31

# Query demos (FAQ 6)
poetry run python scripts/tools/query_examples.py

# Streamlit: analysis charts
poetry run streamlit run frontend/analysis_app.py

# Streamlit: set completion tracker (RQ4)
poetry run streamlit run frontend/collection_app.py
```

---

## Database schema

Table `**card_prices**`, 21 columns (see `config.SCHEMA_COLUMNS`: name → SQLite type). Primary key: `(snapshot_date, id)`.

Additional columns for analysis: `set_release_date`, `illustrator`, `dex_id`.

Table `**user_collection**` for RQ4: `(username, card_id, snapshot_date)`.

---

## Quality reports

Written to `data/quality/` after each run (unless `--skip-quality`):


| File                              | Content                                         |
| --------------------------------- | ----------------------------------------------- |
| `quality_{date}.log`              | Human-readable quality report (also printed to terminal) |
| `integration_{date}.json`         | Enrichment success/failure metrics (written by `scripts/pipeline/run.py` after phase 3) |
| `missing_market_price_{date}.csv` | Cards without `market_price`                    |
| `summary_{date}.json`             | Completeness, validity, flagged suspicious sets |


### Quality improvement (case study)

Trainer kit sets (`tk-*`) often match the quality `suspicious_sets` rule (uniform high prices from sealed-product matching). Analysis exclusions live in `pipeline/6_quality/modules/exclusions.py`; see `excluded_set_ids` in `data/analysis/{date}/analysis_summary.json`.

---

## Analysis output

Written to `data/analysis/{date}/`:


| File                        | Content                                        |
| --------------------------- | ---------------------------------------------- |
| `rq1_*.png`                 | RQ1 charts (rarity, pokemon, illustrator, age) |
| `rq2_expensive_by_year.png` | RQ2 expensive card distribution                |
| `rq3_set_cost_by_year.png`  | RQ3 set cost trend                             |
| `analysis_summary.json`     | Numeric metrics for all RQs                    |


---

## Querying data

```python
from util.query import get_engine, load_snapshot, search_cards, get_set_completion_cost

engine = get_engine("sqlite:///./data/pokedecks.db")
df = load_snapshot("2026-05-31", engine)
cost = get_set_completion_cost("swsh4.5", "2026-05-31", engine)
```

---

## License

Personal project — Data Management exam project.