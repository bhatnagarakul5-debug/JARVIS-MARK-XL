@echo off
title J.A.R.V.I.S. Automated Setup Engine
echo ===================================================
echo   J.A.R.V.I.S. Mark XLI -- Automated 1-Click Setup
echo ===================================================
echo.

cd /d "%~dp0"

echo [1/4] Checking Python Installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please install Python 3.10+ from python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

echo [2/4] Creating Isolated Virtual Environment (venv)...
if not exist "venv" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Could not create virtual environment.
        pause
        exit /b 1
    )
)

echo [3/4] Installing Required Dependencies inside venv...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some packages had warnings, but setup will continue.
)

echo [4/4] Setting Up Config Files...
if not exist "config\api_keys.json" (
    if exist "config\api_keys.json.example" (
        copy "config\api_keys.json.example" "config\api_keys.json"
        echo Created config\api_keys.json from template.
    ) else (
        echo {"gemini_api_key": ""} > "config\api_keys.json"
    )
)

echo.
echo ===================================================
echo   SETUP COMPLETE! 
echo ===================================================
echo.
echo  NEXT STEPS:
echo  1. Open config\api_keys.json and add your Gemini API Key.
echo  2. Double-click main.bat to launch JARVIS!
echo.
pause
