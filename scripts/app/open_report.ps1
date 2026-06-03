$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
Set-Location $Root

if (-not (Test-Path "data/pokedecks.db")) {
    Write-Host "No data/pokedecks.db. Run scripts/setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Opening analysis report at http://localhost:8501"
poetry run streamlit run frontend/analysis_app.py
