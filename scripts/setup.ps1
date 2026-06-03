# PokeDecks 2.0 — one-shot setup (Windows PowerShell)
# Run from project root:  powershell -ExecutionPolicy Bypass -File scripts/setup.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Info($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "WARNING: $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

Info "PokeDecks setup — project root: $Root"

# --- Python 3.14 ---
$py = $null
foreach ($candidate in @("py -3.14", "python3.14", "python")) {
    try {
        $ver = Invoke-Expression "$candidate -c `"import sys; print('.'.join(map(str, sys.version_info[:3])))`"" 2>$null
        if ($ver -eq "3.14.3" -or $ver -like "3.14.*") {
            $py = $candidate
            break
        }
    } catch {}
}

if (-not $py) {
    Warn "Python 3.14 not found."
    @"

Install Python 3.14, then re-run this script:

  winget install Python.Python.3.14
  — or download from https://www.python.org/downloads/
  — check "Add Python to PATH" during install

"@ | Write-Host
    Fail "Missing Python 3.14"
}
Info "Using Python: $py"

# --- Poetry ---
$poetry = Get-Command poetry -ErrorAction SilentlyContinue
if (-not $poetry) {
    Info "Poetry not found — installing..."
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | Invoke-Expression "$py -"
    $env:Path = "$env:APPDATA\Python\Scripts;$env:LOCALAPPDATA\Programs\Python\Python314\Scripts;$env:Path"
    $poetry = Get-Command poetry -ErrorAction SilentlyContinue
    if (-not $poetry) { Fail "Poetry install failed. Restart terminal and retry." }
}

Info "Installing project dependencies..."
& poetry install
if ($LASTEXITCODE -ne 0) { Fail "poetry install failed" }

Info "Verifying imports..."
& poetry run python -c "import matplotlib, seaborn, streamlit, pandas, sqlalchemy, aiohttp, selectolax; print('All core dependencies OK.')"
if ($LASTEXITCODE -ne 0) { Fail "Dependency check failed" }

New-Item -ItemType Directory -Force -Path data, data/quality, data/analysis | Out-Null

if (Test-Path "data/pokedecks.db") {
    Info "Database found: data/pokedecks.db"
} else {
    Warn "No data/pokedecks.db — database is not committed to git."
    @"

Next steps (pick one):

  A) Submission archive: extract the provided zip with data/pokedecks.db, then:
       powershell -ExecutionPolicy Bypass -File scripts/app/open_report.ps1

  B) Quick demo (~5–15 min):
       poetry run python scripts/pipeline/run.py --mode full

  C) Full dataset (~1h 15min):
       poetry run python scripts/pipeline/run.py --mode full

"@ | Write-Host
}

@"

Setup complete.

View analysis report (RQ1–RQ3):
  powershell -ExecutionPolicy Bypass -File scripts/app/open_report.ps1

Set completion app (RQ4):
  powershell -ExecutionPolicy Bypass -File scripts/app/open_collection.ps1

"@ | Write-Host
