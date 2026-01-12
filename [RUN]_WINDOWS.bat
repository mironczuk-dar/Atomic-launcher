@echo off
REM ==========================
REM [RUN]_WINDOWS_UPDATER.bat
REM ==========================

cd /d "%~dp0"

REM --- SPRAWDZENIE PYTHONA ---
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed! Proszę zainstaluj Python 3.
    pause
    exit /b 1
)

REM --- SPRAWDZENIE INTERNETU ---
ping -n 1 8.8.8.8 >nul
IF %ERRORLEVEL% EQU 0 (
    echo Internet connection found. Checking for updates...

    REM --- PRÓBA AKTUALIZACJI PRZEZ GIT ---
    where git >nul 2>nul
    IF %ERRORLEVEL% EQU 0 (
        if exist ".git" (
            echo Updating via Git...
            git pull origin main
        )
    ) ELSE (
        REM --- OPCJA DLA UŻYTKOWNIKA BEZ GIT (POBIERANIE ZIP) ---
        echo Git not found. Downloading latest version via CURL...
        
        REM Zmień poniższy URL na adres Twojego repozytorium
        set "REPO_URL=https://github.com/TWOJA_NAZWA/TWOJE_REPO/archive/refs/heads/main.zip"
        
        curl -L -o update.zip %REPO_URL%
        
        if exist "update.zip" (
            echo Extracting updates...
            REM Rozpakowywanie za pomocą wbudowanego PowerShell
            powershell -Command "Expand-Archive -Path 'update.zip' -DestinationPath 'temp_update' -Force"
            
            REM Przenoszenie plików (zakładając, że GitHub pakuje w folder 'repo-main')
            xcopy /s /e /y "temp_update\*-main\*" "."
            
            REM Sprzątanie
            rd /s /q "temp_update"
            del update.zip
            echo Update complete!
        )
    )

    REM --- AKTUALIZACJA PAKIETÓW PYTHON ---
    echo Checking Python packages...
    python -m pip install --upgrade pygame-ce pytmx >nul
) ELSE (
    echo No internet connection. Starting in offline mode.
)

REM --- URUCHAMIANIE GRY ---
echo Starting DonutPi OS...
python code\main.py

pause
