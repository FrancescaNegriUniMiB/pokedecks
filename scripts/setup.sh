#!/usr/bin/env bash
# PokeDecks — one-shot setup (macOS, Linux, Git Bash on Windows)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

info()  { echo "==> $*"; }
warn()  { echo "WARNING: $*" >&2; }
fail()  { echo "ERROR: $*" >&2; exit 1; }

info "PokeDecks setup — project root: $ROOT"

# --- Poetry on PATH (installer default) ---
export PATH="${HOME}/.local/bin:${PATH}"

install_poetry() {
  if command -v poetry >/dev/null 2>&1; then
    return 0
  fi
  info "Poetry not found — installing via official installer..."
  if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 is required to install Poetry. Install Python 3.14 first (see README → Recommended setup)."
  fi
  curl -sSL https://install.python-poetry.org | python3 -
  export PATH="${HOME}/.local/bin:${PATH}"
  command -v poetry >/dev/null 2>&1 || fail "Poetry install failed. Add ~/.local/bin to PATH and retry."
}

ensure_python_314() {
  if command -v pyenv >/dev/null 2>&1; then
    info "pyenv found — ensuring Python 3.14.3..."
    pyenv install -s 3.14.3
    pyenv local 3.14.3
    return 0
  fi

  if command -v python3.14 >/dev/null 2>&1; then
    PY314="$(command -v python3.14)"
  elif python3 -c "import sys; exit(0 if sys.version_info[:3]==(3,14,3) else 1)" 2>/dev/null; then
    PY314="$(command -v python3)"
  else
    warn "Python 3.14.3 not found and pyenv is not installed."
    cat >&2 <<'EOF'

Install Python 3.14.3, then re-run this script:

  macOS (Homebrew):   brew install python@3.14
  macOS/Linux pyenv:  curl https://pyenv.run | bash
                      pyenv install 3.14.3 && pyenv local 3.14.3
  Ubuntu/Debian:      sudo add-apt-repository ppa:deadsnakes/ppa
                      sudo apt update && sudo apt install python3.14 python3.14-venv
  Windows:            run scripts/setup.ps1 instead of this script

EOF
    fail "Missing Python 3.14.3"
  fi

  info "Using Python: $PY314"
  poetry env use "$PY314" 2>/dev/null || poetry env use 3.14 2>/dev/null || true
}

install_poetry
ensure_python_314

info "Installing project dependencies (poetry install)..."
poetry install

info "Verifying imports..."
poetry run python -c "
import matplotlib, seaborn, streamlit, pandas, sqlalchemy, aiohttp, selectolax
print('All core dependencies OK.')
"

mkdir -p data/quality data/analysis

if [[ -f data/pokedecks.db ]]; then
  SNAPSHOT="$(poetry run python -c "
from sqlalchemy import text
from util.query import get_engine
e = get_engine('sqlite:///./data/pokedecks.db')
with e.connect() as c:
    print(c.execute(text('SELECT MAX(snapshot_date) FROM card_prices')).scalar() or '')
" 2>/dev/null || echo "")"
  info "Database found: data/pokedecks.db (latest snapshot: ${SNAPSHOT:-unknown})"
else
  warn "No data/pokedecks.db — database is not committed to git."
  cat <<'EOF'

Next steps (pick one):

  A) Download pre-built snapshots:
       ./scripts/download_snapshots.sh

  B) Full dataset (~1h 15min):
       poetry run python scripts/pipeline/run.py --mode full

EOF
fi

cat <<'EOF'

Setup complete.

View analysis report (RQ1–RQ3 charts):
  ./scripts/app/open_report.sh

Set completion app (RQ4):
  ./scripts/app/open_collection.sh

CLI demos:
  poetry run python scripts/tools/query_examples.py
  poetry run python scripts/pipeline/quality.py --date YYYY-MM-DD

EOF
