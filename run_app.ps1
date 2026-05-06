$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Local virtual environment not found."
    Write-Host "Run: pip install -r requirements.txt"
    Write-Host "Then start with: python -m streamlit run app.py"
    exit 1
}

& $python -m streamlit run app.py

