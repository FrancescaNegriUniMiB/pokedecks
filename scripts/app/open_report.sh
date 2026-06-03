#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PATH="${HOME}/.local/bin:${PATH}"

if [[ ! -f data/pokedecks.db ]]; then
  echo "No data/pokedecks.db. Run ./scripts/setup.sh and follow the data instructions." >&2
  exit 1
fi

echo "Opening analysis report (Streamlit) at http://localhost:8501"
poetry run streamlit run frontend/analysis_app.py
