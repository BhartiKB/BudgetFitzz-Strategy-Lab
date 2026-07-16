$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) { & (Join-Path $Root "setup.ps1") }
$env:PYTHONPATH = Join-Path $Root "src"
& $Python (Join-Path $Root "scripts\record_demo.py")
& $Python (Join-Path $Root "scripts\finalize_submission.py")
