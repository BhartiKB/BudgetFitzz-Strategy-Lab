param([switch]$Final)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) { & (Join-Path $Root "setup.ps1") }
$env:PYTHONPATH = Join-Path $Root "src"
$ArgsList = @((Join-Path $Root "scripts\validate_submission.py"))
if ($Final) { $ArgsList += "--final" }
& $Python @ArgsList

