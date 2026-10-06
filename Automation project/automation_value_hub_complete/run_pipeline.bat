@echo off
setlocal

set MONTH=%1
if "%MONTH%"=="" set MONTH=2026-08

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest
python main.py --month %MONTH%

endlocal
