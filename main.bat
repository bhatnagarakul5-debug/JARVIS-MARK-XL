@echo off
title J.A.R.V.I.S. Mark XLI (Creator: Akul Bhatnagar -- ESTD 2025)
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main.py
) else (
    python main.py
)
pause
