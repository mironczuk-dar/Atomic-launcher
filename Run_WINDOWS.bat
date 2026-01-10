@echo off
setlocal

:: ALWAYS RUN FROM SCRIPT DIRECTORY
cd /d "%~dp0"

echo Checking for Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found.
    pause
    exit /b 1
)

echo Checking for Git...
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo Git not found.
    pause
    exit /b 1
)

echo Verifying installations...
echo Python and Git are installed.

:: CHECK INTERNET
ping -n 1 -w 1000 8.8.8.8 >nul
if %errorlevel% equ 0 (
    echo Internet connection found. Checking for updates...

    if exist ".git" (
        git pull origin main --no-rebase
    ) else (
        echo Not a git repository. Skipping git pull.
    )

    python -m pip install --upgrade pygame-ce pytmx --quiet
) else (
    echo No internet connection. Skipping updates.
)

echo Starting DonutPi OS...
python code\main.py

pause