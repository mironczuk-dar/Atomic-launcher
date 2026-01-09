@echo off
echo Checking for Python...

:: CHECKING IF PYTHON IS INSTALLED
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed!
    echo Please install Python and add it to PATH.
    pause
    exit /b 1
)

echo Python is installed.

:: --- UPDATING ---
:: CHECKING INTERNET CONNECTION (PING GOOGLE DNS)
ping -n 1 -w 1000 8.8.8.8 >nul
if %errorlevel% equ 0 (
    echo Internet connection found. Checking for updates...

    :: 1. UPDATING CODE FROM GITHUB
    echo Pulling latest code from GitHub...
    git pull origin main --no-rebase

    :: 2. UPDATING LIBRARIES
    echo Updating libraries...
    python -m pip install --upgrade pygame-ce pytmx --quiet

    echo Updates finished or already up to date.
) else (
    echo No internet connection. Skipping updates.
)
:: ---------------------------

echo Starting DonutPi OS...
python code\main.py

pause
