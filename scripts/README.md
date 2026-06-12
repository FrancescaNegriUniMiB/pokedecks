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

## Cloud snapshot (GitHub Actions)

Workflow: `.github/workflows/update-snapshot.yml` — scheduled 2026-06-09, 2026-06-16, 2026-07-08, 2026-07-15 at 08:00 Europe/Rome. First run uses `--mode full`; later runs use `--mode update` with the previous artifact.

## Tools

| Script | Purpose |
|--------|---------|
| `tools/download_snapshots.py` | Download pre-built snapshots from GitHub |
| `tools/download_snapshots.sh` | macOS / Linux wrapper for `download_snapshots.py` |
| `tools/download_snapshots.ps1` | Windows wrapper for `download_snapshots.py` |
| `tools/publish-snapshot.sh` | Publish local `data/` as a GitHub Release (requires `gh`) |
| `tools/query_examples.py` | SQL demo queries |

Fetches the last 3 GitHub Releases into `data/` (no `gh` required). CI also publishes a release on each successful snapshot run.

| OS | Command |
|----|---------|
| macOS / Linux | `./scripts/tools/download_snapshots.sh` |
| Windows | `powershell -ExecutionPolicy Bypass -File scripts/tools/download_snapshots.ps1` |

See `tools/download_snapshots.py` for options (`--limit`, `--source`, `--repo`, `--dest`).

## Apps (Streamlit)

| OS | Analysis report (RQ1–RQ3) | Set completion (RQ4) |
|----|---------------------------|----------------------|
| macOS / Linux | `./scripts/app/open_report.sh` | `./scripts/app/open_collection.sh` |
| Windows | `powershell -ExecutionPolicy Bypass -File scripts/app/open_report.ps1` | `powershell -ExecutionPolicy Bypass -File scripts/app/open_collection.ps1` |
