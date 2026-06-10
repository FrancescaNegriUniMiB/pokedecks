# PokeDecks - one-shot setup (Windows PowerShell)
# Run from project root:  powershell -ExecutionPolicy Bypass -File scripts/setup.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location -LiteralPath $Root

function Info($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "WARNING: $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

$versionCheck = 'import sys; print(".".join(map(str, sys.version_info[:3])))'

function Add-ToPath([string]$dir) {
    if ($dir -and (Test-Path -LiteralPath $dir) -and ($env:Path -notlike "*$dir*")) {
        $env:Path = "$dir;$env:Path"
    }
}

function Refresh-PythonPath {
    $bases = @($env:LOCALAPPDATA, $env:ProgramFiles)
    $patterns = @("Python314", "Python3.14", "Python3.14.*")

    foreach ($base in $bases) {
        $pythonRoot = Join-Path $base "Programs\Python"
        if (Test-Path -LiteralPath $pythonRoot) {
            foreach ($pattern in $patterns) {
                foreach ($m in (Get-ChildItem -Path $pythonRoot -Directory -Filter $pattern -ErrorAction SilentlyContinue)) {
                    Add-ToPath $m.FullName
                    Add-ToPath (Join-Path $m.FullName "Scripts")
                }
            }
        }
    }

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath) {
        foreach ($segment in $userPath -split ";") {
            if ($segment -match "[Pp]ython") { Add-ToPath $segment }
        }
    }
}

function Refresh-PoetryPath {
    Add-ToPath (Join-Path $env:APPDATA "Python\Scripts")
    Add-ToPath (Join-Path $env:APPDATA "pypoetry\venv\Scripts")
}

function Find-Python314 {
    $candidates = @(
        @{ exe = "py";         prefix = @("-3.14"); label = "py -3.14" },
        @{ exe = "python3.14"; prefix = @();        label = "python3.14" },
        @{ exe = "python";     prefix = @();        label = "python" }
    )

    $bases = @($env:LOCALAPPDATA, $env:ProgramFiles)
    $patterns = @("Python314", "Python3.14", "Python3.14.*")
    foreach ($base in $bases) {
        $pythonRoot = Join-Path $base "Programs\Python"
        if (Test-Path -LiteralPath $pythonRoot) {
            foreach ($pattern in $patterns) {
                foreach ($m in (Get-ChildItem -Path $pythonRoot -Directory -Filter $pattern -ErrorAction SilentlyContinue)) {
                    $exe = Join-Path $m.FullName "python.exe"
                    if (Test-Path -LiteralPath $exe) {
                        $candidates += @{ exe = $exe; prefix = @(); label = $exe }
                    }
                }
            }
        }
    }

    foreach ($c in $candidates) {
        try {
            $ver = & $c.exe @($c.prefix) -c $versionCheck 2>$null
            if ($LASTEXITCODE -eq 0 -and $ver -like "3.14.*") {
                return @{ py = $c.label; pyCmd = $c.exe; pyArgs = $c.prefix }
            }
        } catch {}
    }
    return $null
}

function Install-Python314 {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        Fail "Python 3.14 not found and winget is unavailable. Install from https://www.python.org/downloads/ (enable Add to PATH), then re-run this script."
    }
    Info "Installing Python 3.14 via winget..."
    & winget install --id Python.Python.3.14 -e --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335189 -and $LASTEXITCODE -ne -1978335212) {
        Fail "winget install Python.Python.3.14 failed (exit $LASTEXITCODE)"
    }
    Refresh-PythonPath
}

# --- Main ---

Info "PokeDecks setup - project root: $Root"

# Python 3.14
$python = Find-Python314
if (-not $python) {
    Install-Python314
    $python = Find-Python314
}
if (-not $python) {
    Fail "Python 3.14 not found. Close this terminal, open a new one, and re-run setup.ps1"
}
Info "Using Python: $($python.py)"

# Poetry
if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    Info "Installing Poetry..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | & $python.pyCmd @($python.pyArgs + '-')
    Refresh-PoetryPath
    if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) { Fail "Poetry install failed. Restart terminal and retry." }
}

Info "Installing dependencies..."
& poetry install
if ($LASTEXITCODE -ne 0) { Fail "poetry install failed" }

Info "Verifying imports..."
& poetry run python -c "import matplotlib, seaborn, streamlit, pandas, sqlalchemy, aiohttp, selectolax; print('All core dependencies OK.')"
if ($LASTEXITCODE -ne 0) { Fail "Dependency check failed" }

New-Item -ItemType Directory -Force -Path data, data/quality, data/analysis | Out-Null

if (Test-Path -LiteralPath "data/pokedecks.db") {
    Info "Database found: data/pokedecks.db"
} else {
    Warn "No data/pokedecks.db - database is not committed to git."
    @"

Next steps (pick one):

  A) Pre-built archive: extract the snapshot with data/pokedecks.db, then:
       powershell -ExecutionPolicy Bypass -File scripts/app/open_report.ps1

  B) Full dataset (~1h 15min):
       poetry run python scripts/pipeline/run.py --mode full

"@ | Write-Host
}

@"

Setup complete.

View analysis report (RQ1-RQ3):
  powershell -ExecutionPolicy Bypass -File scripts/app/open_report.ps1

Set completion app (RQ4):
  powershell -ExecutionPolicy Bypass -File scripts/app/open_collection.ps1

"@ | Write-Host
