@echo off
setlocal EnableDelayedExpansion

REM =============================================
REM [RUN]_WINDOWS.bat
REM Atomic Launcher - Embedded Python Runtime
REM =============================================

REM --- ROOT DIRECTORY ---
cd /d "%~dp0"

REM --- PATHS ---
set "ROOT=%~dp0"
set "CODE_DIR=%ROOT%src"
set "EMBEDDED_DIR=%ROOT%windows_python_3.14.5"

set "PYTHON=%EMBEDDED_DIR%\python.exe"

REM --- PYTHON MODULE PATHS ---
set "PYTHONPATH=%CODE_DIR%"

REM --- CHECK PYTHON ---
if not exist "%PYTHON%" (
    echo.
    echo [ERROR] Embedded Python not found:
    echo %PYTHON%
    echo.
    pause
    exit /b 1
)

REM =============================================
REM ENABLE SITE PACKAGES FOR EMBEDDED PYTHON
REM =============================================

for %%f in ("%EMBEDDED_DIR%\python*._pth") do (
    findstr /C:"import site" "%%f" >nul
    if errorlevel 1 (
        echo import site>>"%%f"
    )
)

REM =============================================
REM ENSURE PIP EXISTS (STANDALONE WHEEL BOOTSTRAP)
REM =============================================

echo Checking embedded pip...

"%PYTHON%" -m pip --version >nul 2>nul

if errorlevel 1 (
    echo [INFO] Pip not found in embedded environment. Fetching standalone components...
    
    REM 1. Create a temporary site-packages folder if it doesn't exist
    if not exist "%EMBEDDED_DIR%\Lib\site-packages" mkdir "%EMBEDDED_DIR%\Lib\site-packages"
    
    REM 2. Use Windows curl to bypass Python's missing socket extensions
    curl -sL -o "%EMBEDDED_DIR%\pip.whl" "https://bootstrap.pypa.io/pip/pip.pyz"
    
    if exist "%EMBEDDED_DIR%\pip.whl" (
        echo [INFO] Extracting pip architecture...
        
        REM Extract the package using built-in PowerShell zip tools
        powershell -Command "Expand-Archive -Path '%EMBEDDED_DIR%\pip.whl' -DestinationPath '%EMBEDDED_DIR%\Lib\site-packages' -Force"
        del "%EMBEDDED_DIR%\pip.whl"
        
        REM 3. Append site-packages path to Python's configuration map if not present
        for %%f in ("%EMBEDDED_DIR%\python*._pth") do (
            findstr /C:"Lib\site-packages" "%%f" >nul
            if errorlevel 1 (
                echo Lib\site-packages>>"%%f"
            )
        )
        
        REM Final check verification
        "%PYTHON%" -m pip --version >nul 2>nul
        if errorlevel 1 (
            echo [ERROR] The environment extraction layout failed. Your zip package may be corrupted.
            pause
            exit /b 1
        )
        echo [SUCCESS] Standalone pip initialized successfully.
    ) else (
        echo [ERROR] Failed to fetch the standalone pip hub. Check your network adapter.
        pause
        exit /b 1
    )
)

REM =============================================
REM INTERNET CHECK
REM =============================================

ping -n 1 8.8.8.8 >nul

IF %ERRORLEVEL% EQU 0 (

    echo Internet connection found.
    echo Checking for updates...

    REM =========================================
    REM GIT UPDATE
    REM =========================================

    where git >nul 2>nul

    IF %ERRORLEVEL% EQU 0 (

        if exist ".git" (
            echo Updating via Git...
            git pull origin main
        )

    ) ELSE (

        REM =====================================
        REM ZIP UPDATE
        REM =====================================

        echo Git not found.
        echo Downloading latest version...

        set "ZIP_URL=https://github.com/mironczuk-dar/Atomic-launcher/archive/refs/heads/main.zip"

        curl -L -o update.zip "%ZIP_URL%"

        if exist "update.zip" (

            echo Extracting update...

            powershell -Command "Expand-Archive -Path 'update.zip' -DestinationPath 'temp_update' -Force"

            for /d %%d in ("temp_update\*") do (
                xcopy "%%d\*" "%ROOT%" /s /e /y /i >nul
            )

            rd /s /q "temp_update"
            del update.zip

            echo Update complete.
        )
    )

    REM =========================================
    REM PYTHON PACKAGES
    REM =========================================

    echo Updating Python packages...

    "%PYTHON%" -m pip install --upgrade pip --disable-pip-version-check

    "%PYTHON%" -m pip install --upgrade ^
        pygame-ce ^
        pytmx ^
        opencv-python ^
        --disable-pip-version-check

) ELSE (

    echo No internet connection.
    echo Starting in offline mode.
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