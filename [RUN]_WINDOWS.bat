@echo off
REM ==========================
REM Run.bat for Windows
REM ==========================

echo Checking for Python...

REM --- CHECK IF PYTHON IS INSTALLED ---
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed!
    echo Please install Python 3 and add it to PATH.
    pause
    exit /b 1
)
echo Python is installed.

REM --- CHANGE TO LAUNCHER DIRECTORY ---
cd /d "%~dp0"

REM --- CHECK INTERNET CONNECTION ---
ping -n 1 8.8.8.8 >nul
IF %ERRORLEVEL% EQU 0 (
    echo Internet connection found. Checking for updates...
    
    REM --- PULL LATEST CODE FROM GITHUB ---
    git pull origin main

    REM --- UPDATE PYTHON LIBRARIES ---
    python -m pip install --upgrade pygame-ce pytmx >nul
    echo Updates finished or already up to date.
) ELSE (
    echo No internet connection. Skipping updates.
)

echo Starting DonutPi OS...

REM --- LAUNCH THE GAME ---
python code\main.py

pause
