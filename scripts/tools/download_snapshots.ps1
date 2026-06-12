$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
Set-Location -LiteralPath $Root
$PoetryExe = Join-Path $env:APPDATA "Python\Scripts\poetry.exe"
if (-not (Test-Path -LiteralPath $PoetryExe)) { $PoetryExe = "poetry" }
& $PoetryExe run python scripts/tools/download_snapshots.py @args
