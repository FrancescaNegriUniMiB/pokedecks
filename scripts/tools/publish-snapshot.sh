#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

TAG="${1:-snapshot-$(date +%F)}"
ZIP="/tmp/pokedecks-${TAG}.zip"

if [ ! -f data/pokedecks.db ]; then
  echo "Missing data/pokedecks.db — run the pipeline first."
  exit 1
fi

zip -r "$ZIP" data/pokedecks.db data/quality data/analysis
echo "Created $ZIP ($(du -h "$ZIP" | cut -f1))"

gh release view "$TAG" >/dev/null 2>&1 && {
  echo "Release $TAG already exists. Uploading asset..."
  gh release upload "$TAG" "$ZIP" --clobber
} || {
  gh release create "$TAG" "$ZIP" \
    --title "PokeDecks snapshot ${TAG#snapshot-}" \
    --notes "Pre-built data/ for cross-platform testing (db, quality, analysis)."
}

echo ""
echo "Download on another machine:"
echo "  gh release download $TAG -p '*.zip' -D ."
echo "  unzip pokedecks-${TAG}.zip"
