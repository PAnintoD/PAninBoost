@echo off
title FPS Booster - Launcher
color 0A

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Install dependencies if missing
echo Checking dependencies...
python -c "import psutil, customtkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing required packages: psutil, customtkinter...
    python -m pip install psutil customtkinter --quiet
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies. Check your internet connection.
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed successfully.
)

:: Determine the script directory
set "SCRIPT_DIR=%~dp0"
set "BOOSTER_SCRIPT=%SCRIPT_DIR%fps_booster.py"

:: Check the script exists
if not exist "%BOOSTER_SCRIPT%" (
    echo [ERROR] fps_booster.py not found in: %SCRIPT_DIR%
    pause
    exit /b 1
)

:: Re-launch as Administrator if not elevated
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Requesting Administrator privileges...
    powershell -Command "Start-Process -FilePath 'python.exe' -ArgumentList '\"%BOOSTER_SCRIPT%\"' -Verb RunAs"
    exit /b 0
)

:: Already elevated — run directly
python "%BOOSTER_SCRIPT%"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] FPS Booster exited with an error (code %errorlevel%).
    pause
)
