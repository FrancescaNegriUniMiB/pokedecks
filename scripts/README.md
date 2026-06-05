# Scripts

Entry points for setup, pipeline runs, utilities, and Streamlit launchers.

## Setup (project root)

| OS | Command |
|----|---------|
| macOS / Linux / Git Bash | `./scripts/setup.sh` |
| Windows PowerShell | `powershell -ExecutionPolicy Bypass -File scripts/setup.ps1` |

## Pipeline

| Script | Purpose |
|--------|---------|
| `pipeline/run.py` | Full pipeline (acquisition → analysis); also `build_integration_metrics` / `export_integration_metrics` after enrichment |
| `pipeline/analyze.py` | RQ1–RQ3 analysis only |
| `pipeline/quality.py` | Quality checks only |

```bash
poetry run python scripts/pipeline/run.py --mode full
poetry run python scripts/pipeline/analyze.py --date 2026-05-31
poetry run python scripts/pipeline/quality.py --date 2026-05-31
```

## Tools

| Script | Purpose |
|--------|---------|
| `tools/query_examples.py` | SQL demo queries (FAQ 6) |

## Apps (Streamlit)

| OS | Analysis report (RQ1–RQ3) | Set completion (RQ4) |
|----|---------------------------|----------------------|
| macOS / Linux | `./scripts/app/open_report.sh` | `./scripts/app/open_collection.sh` |
| Windows | `powershell -ExecutionPolicy Bypass -File scripts/app/open_report.ps1` | `powershell -ExecutionPolicy Bypass -File scripts/app/open_collection.ps1` |
