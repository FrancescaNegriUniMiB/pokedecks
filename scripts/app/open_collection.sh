#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PATH="${HOME}/.local/bin:${PATH}"

if [[ ! -f data/pokedecks.db ]]; then
  echo "No data/pokedecks.db. Run ./scripts/setup.sh and follow the data instructions." >&2
  exit 1
fi

echo "Opening set completion app (RQ4) at http://localhost:8502"
poetry run streamlit run frontend/collection_app.py --server.port 8502
