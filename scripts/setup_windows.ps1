$ErrorActionPreference = "Stop"

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$python = if ($env:SLIDE_MAKER_PYTHON) { $env:SLIDE_MAKER_PYTHON } else { "python" }

& $python -m venv .venv

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Failed to create virtual environment."
}

& $venvPython -m pip install --upgrade pip setuptools wheel
& $venvPython -m pip install -r requirements.txt

Push-Location (Join-Path $root "pptx-project")
npm install
Pop-Location

Write-Host ""
Write-Host "Windows setup finished."
Write-Host "Run the desktop UI:"
Write-Host "  .\.venv\Scripts\python.exe .\ui_app.py"
Write-Host ""
Write-Host "Preview only:"
Write-Host "  .\.venv\Scripts\python.exe .\ui_app.py --demo"
