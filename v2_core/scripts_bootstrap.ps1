param(
    [switch]$RunApi
)

$ErrorActionPreference = "Stop"

Write-Host "[1/3] Creating virtual environment..."
python -m venv .venv

Write-Host "[2/3] Installing dependencies..."
. .\.venv\Scripts\Activate.ps1
pip install -e .[dev]

Write-Host "[3/3] Setup complete."

if ($RunApi) {
    Write-Host "Starting API on http://localhost:8100 ..."
    uvicorn apps.api.main:app --reload --port 8100
}

