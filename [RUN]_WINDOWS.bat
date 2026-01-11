@echo off
setlocal

:: ALWAYS RUN FROM SCRIPT DIRECTORY
cd /d "%~dp0"

:: ----- Sprawdzenia -----
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found.
    pause
    exit /b 1
)

where git >nul 2>nul
if %errorlevel% neq 0 (
    echo Git not found.
    pause
    exit /b 1
)

:: ----- Sprawdzenie internetu i aktualizacje -----
ping -n 1 -w 1000 8.8.8.8 >nul
if %errorlevel% equ 0 (
    if exist ".git" (
        git pull origin main --no-rebase
    )
    python -m pip install --upgrade pygame-ce pytmx --quiet
)

:: ----- Uruchomienie launchera BEZ terminala -----
start "" pythonw code/main.py

:: ---- Nie blokujemy terminala ----
exit /b 0