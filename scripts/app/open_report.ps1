$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
Set-Location -LiteralPath $Root

function Add-ToPath([string]$dir) {
    if ($dir -and (Test-Path -LiteralPath $dir) -and ($env:Path -notlike "*$dir*")) {
        $env:Path = "$dir;$env:Path"
    }
}
Add-ToPath (Join-Path $env:APPDATA "Python\Scripts")
Add-ToPath (Join-Path $env:LOCALAPPDATA "Programs\Python\Python314\Scripts")

if (-not (Test-Path -LiteralPath "data/pokedecks.db")) {
    Write-Host "No data/pokedecks.db. Run scripts/setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Opening analysis report at http://localhost:8501"
& poetry run streamlit run frontend/analysis_app.py
