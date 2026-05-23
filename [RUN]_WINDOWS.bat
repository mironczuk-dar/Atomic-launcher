@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM --- ROOT DIRECTORY ---
cd /d "%~dp0"
set "ROOT=%~dp0"

REM --- PATHS ---
set "CODE_DIR=%ROOT%src"
set "EMBEDDED_DIR=%ROOT%windows_python"
set "PYTHON=%EMBEDDED_DIR%\python.exe"

REM --- CHECK PYTHON ---
if not exist "%PYTHON%" (
    echo.
    echo [ERROR] Portable Python runtime not found at:
    echo %PYTHON%
    echo.
    pause
    exit /b 1
)

REM =============================================
REM INTERNET & UPDATE SYNC
REM =============================================
ping -n 1 8.8.8.8 >nul

IF %ERRORLEVEL% EQU 0 (
    echo Internet connection found. Syncing environment components...

    REM =========================================
    REM GIT UPDATE
    REM =========================================
    
    set "PORTABLE_GIT=%ROOT%PortableGit\cmd\git.exe"

    if exist "%PORTABLE_GIT%" (
        if exist ".git" (
            echo Updating Launcher via Portable Git...
            "%PORTABLE_GIT%" pull origin main
        )
    ) else (
        where git >nul 2>nul
        IF !ERRORLEVEL! EQU 0 (
            if exist ".git" (
                echo Updating Launcher via System Git...
                git pull origin main
            )
        )
    )

    REM =========================================
    REM DEPENDENCY CHECK
    REM =========================================
    echo Updating engine modules...
    
    REM Because this is a full Python instance, these commands run flawlessly 
    REM from any working directory on your system.
    "%PYTHON%" -m pip install --upgrade pip --disable-pip-version-check
    "%PYTHON%" -m pip install --upgrade pygame-ce pytmx opencv-python --disable-pip-version-check

) ELSE (
    echo No internet connection found. Starting Launcher in offline mode.
)

REM =============================================
REM START APPLICATION
REM =============================================
echo.
echo Starting Atomic Launcher...
echo.

cd /d "%CODE_DIR%"
"%PYTHON%" main.py

echo.
echo Application closed.
pause