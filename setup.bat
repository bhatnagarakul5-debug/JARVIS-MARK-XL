@echo off
title J.A.R.V.I.S. Automated Setup Engine
echo ===================================================
echo   J.A.R.V.I.S. Mark 58 -- Automated 1-Click Setup
echo ===================================================
echo.

cd /d "%~dp0"

echo [1/4] Detecting Python Launcher...
set PYCMD=

python --version >nul 2>&1
if %errorlevel% equ 0 set PYCMD=python

if "%PYCMD%"=="" (
    py -3 --version >nul 2>&1
    if %errorlevel% equ 0 set PYCMD=py -3
)

if "%PYCMD%"=="" (
    py --version >nul 2>&1
    if %errorlevel% equ 0 set PYCMD=py
)

if "%PYCMD%"=="" (
    python3 --version >nul 2>&1
    if %errorlevel% equ 0 set PYCMD=python3
)

if "%PYCMD%"=="" (
    echo [ERROR] No working Python installation found on this system.
    echo.
    echo PLEASE FIX:
    echo 1. Install Python 3.10+ from https://www.python.org/downloads/
    echo 2. Check the box "Add Python to PATH" during installation!
    echo 3. Open Windows Settings ^> Apps ^> Advanced app settings ^> App execution aliases
    echo    and turn OFF "App Installer python.exe".
    echo.
    pause
    exit /b 1
)

echo [OK] Using Python Launcher: %PYCMD%
%PYCMD% --version

echo.
echo [2/4] Enabling Windows Long Paths (Fixes MAX_PATH errors)...
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f >nul 2>&1

echo.
echo [3/4] Creating Isolated Virtual Environment (venv)...
if not exist "venv" (
    %PYCMD% -m venv --system-site-packages venv
    if %errorlevel% neq 0 (
        echo [ERROR] Could not create virtual environment.
        pause
        exit /b 1
    )
)

echo.
echo [4/4] Installing Required Dependencies inside venv...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo.
echo Checking PyAudio Audio Driver...
python -c "import pyaudio" >nul 2>&1
if %errorlevel% neq 0 (
    echo [NOTICE] Installing fallback audio binaries for Windows...
    pip install pipwin >nul 2>&1
    venv\Scripts\pipwin install pyaudio >nul 2>&1
)

echo.
echo Setting Up Config Files...
if not exist "config\api_keys.json" (
    if exist "config\api_keys.json.example" (
        copy "config\api_keys.json.example" "config\api_keys.json" >nul
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
