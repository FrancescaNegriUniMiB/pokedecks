$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location -LiteralPath $Root

function Info($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "WARNING: $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

$RequiredPythonVersion = "3.14.3"

function Add-ToPath([string]$dir) {
    if ($dir -and (Test-Path -LiteralPath $dir) -and ($env:Path -notlike "*$dir*")) {
        $env:Path = "$dir;$env:Path"
    }
}

function Refresh-PythonPath {
    Add-ToPath (Join-Path $env:LOCALAPPDATA "Python\bin")
    Add-ToPath (Join-Path $env:LOCALAPPDATA "Programs\Python\Launcher")
    foreach ($base in @($env:LOCALAPPDATA, $env:ProgramFiles)) {
        $root = Join-Path $base "Programs\Python"
        if (-not (Test-Path -LiteralPath $root)) { continue }
        foreach ($d in (Get-ChildItem -Path $root -Directory -Filter "Python314*" -ErrorAction SilentlyContinue)) {
            Add-ToPath $d.FullName
            Add-ToPath (Join-Path $d.FullName "Scripts")
        }
    }
    foreach ($pathValue in @(
        [Environment]::GetEnvironmentVariable("Path", "User"),
        [Environment]::GetEnvironmentVariable("Path", "Machine")
    )) {
        if (-not $pathValue) { continue }
        foreach ($segment in $pathValue -split ";") {
            if ($segment -match "[Pp]ython") { Add-ToPath $segment }
        }
    }
}

function Test-Python([string]$exe, [string[]]$prefix = @()) {
    & $exe @prefix -c "import sys; raise SystemExit(0 if sys.version_info[:3]==(3,14,3) else 1)" 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { return $null }
    return @{ pyCmd = $exe; pyArgs = $prefix }
}

function Find-Python {
    Refresh-PythonPath
    foreach ($base in @($env:LOCALAPPDATA, $env:ProgramFiles)) {
        $exe = Join-Path $base "Programs\Python\Python314\python.exe"
        if (-not (Test-Path -LiteralPath $exe)) { continue }
        $found = Test-Python $exe @()
        if ($found) { return $found }
    }
    foreach ($c in @(
        @{ exe = "python3.14"; prefix = @() },
        @{ exe = "python"; prefix = @() },
        @{ exe = "py"; prefix = @("-3.14") }
    )) {
        $found = Test-Python $c.exe $c.prefix
        if ($found) { return $found }
    }
    return $null
}

function Install-Python {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Fail "Python $RequiredPythonVersion not found and winget unavailable."
    }
    Info "Installing Python $RequiredPythonVersion..."
    & winget install --id Python.Python.3.14 -e --version $RequiredPythonVersion --accept-package-agreements --accept-source-agreements
    Refresh-PythonPath
}

$python = Find-Python
if (-not $python) {
    Install-Python
    $python = Find-Python
}
if (-not $python) { Fail "Python $RequiredPythonVersion not found. Restart PowerShell and re-run setup.ps1." }

if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    Info "Installing Poetry..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $installer = (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content
    $installer | & $python.pyCmd @($python.pyArgs) -
    Add-ToPath (Join-Path $env:APPDATA "Python\Scripts")
    if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) { Fail "Poetry install failed." }
}

& poetry env use $(if ($python.pyArgs.Count) { $RequiredPythonVersion } else { $python.pyCmd }) 2>$null
& poetry install
if ($LASTEXITCODE -ne 0) { Fail "poetry install failed" }

& poetry run python -c "import matplotlib, seaborn, streamlit, pandas, sqlalchemy, aiohttp, selectolax"
if ($LASTEXITCODE -ne 0) { Fail "Dependency check failed" }

New-Item -ItemType Directory -Force -Path data, data/quality, data/analysis | Out-Null

if (-not (Test-Path -LiteralPath "data/pokedecks.db")) {
    Warn "No data/pokedecks.db."
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
