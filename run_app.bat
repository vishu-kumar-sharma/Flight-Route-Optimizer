@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Local virtual environment not found.
    echo Run: pip install -r requirements.txt
    echo Then start with: python -m streamlit run app.py
    exit /b 1
)

".venv\Scripts\python.exe" -m streamlit run app.py

