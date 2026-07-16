$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $VenvPython) {
  $Python = $VenvPython
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $Python = (Get-Command python).Source
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  $Python = (Get-Command py).Source
} else {
  throw "Python 3.11+ is required to launch the offline platform."
}
& $Python (Join-Path $Root "app\server.py") --port 8501
