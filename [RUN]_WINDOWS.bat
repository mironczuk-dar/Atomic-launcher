@echo off
REM ==========================
REM [RUN]_WINDOWS.bat
REM ==========================

REM --- PRZECHODZIMY DO KATALOGU, W KTÓRYM JEST SKRYPT ---
cd /d "%~dp0"
echo Current directory: %CD%

REM --- SPRAWDZENIE PYTHONA ---
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed!
    echo Please install Python 3 and add it to PATH.
    pause
    exit /b 1
)
echo Python is installed.

REM --- SPRAWDZENIE INTERNETU ---
ping -n 1 8.8.8.8 >nul
IF %ERRORLEVEL% EQU 0 (
    echo Internet connection found. Checking for updates...

    REM --- SPRAWDZENIE CZY TO JEST REPOZYTORIUM GIT ---
    if exist ".git" (
        git pull origin main
    ) ELSE (
        echo No Git repository found. Skipping update.
    )

    REM --- AKTUALIZACJA PAKIETÓW ---
    python -m pip install --upgrade pygame-ce pytmx >nul
    echo Updates finished or already up to date.
) ELSE (
    echo No internet connection. Skipping updates.
)

REM --- URUCHAMIANIE GRY ---
echo Starting DonutPi OS...
python code\main.py

pause
