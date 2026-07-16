param([string]$Python = "")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $Python) {
  $Bundled = "C:\Users\bhart\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  if (Test-Path -LiteralPath $Bundled) { $Python = $Bundled }
  elseif (Get-Command python -ErrorAction SilentlyContinue) { $Python = (Get-Command python).Source }
  else { throw "Python 3.11+ was not found." }
}
if (-not (Test-Path -LiteralPath (Join-Path $Root ".venv\Scripts\python.exe"))) {
  & $Python -m venv --system-site-packages (Join-Path $Root ".venv")
}
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$env:PYTHONPATH = Join-Path $Root "src"
& $VenvPython -m pip install --no-deps --no-build-isolation -e $Root
& $VenvPython -c "import numpy,pandas,pydantic,PIL,reportlab; print('Runtime dependencies ready')"
& $VenvPython -m unittest discover -s (Join-Path $Root "tests") -v
