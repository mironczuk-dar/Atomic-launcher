@echo off
echo Checking for Python...

REM CHECKING IF PYTHON IS INSTALLED
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python is not installed or not added to PATH!
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo Python is installed.

REM --- UPDATING ---
REM CHECKING IF THERE'S INTERNET BY PINGING GOOGLE
ping -n 1 -w 1000 8.8.8.8 >nul
IF %ERRORLEVEL%==0 (
    echo Internet connection found. Checking for updates...
    pip install --upgrade pygame-ce pytmx --quiet
    echo Updates finished or already up to date.
) ELSE (
    echo No internet connection. Skipping updates.
)
REM ---------------------------

echo Starting DonutPi OS...
python code\main.py

pause
