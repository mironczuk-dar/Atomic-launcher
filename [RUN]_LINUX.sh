#!/bin/bash

# Ustaw katalog launchera na ten, w którym znajduje się skrypt
cd "$(dirname "$0")" || { echo "Nie mogę zmienić katalogu!"; exit 1; }

echo "Current directory: $(pwd)"

echo "Checking for Python..."
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed!"
    exit 1
fi
echo "Python is installed."

# 1. Determine if we need system site packages (for Raspberry Pi)
USE_SYSTEM_SITE_PACKAGES=false
MODEL_FILE="/proc/device-tree/model"

if [ -f "$MODEL_FILE" ]; then
    MODEL=$(tr -d '\0' < "$MODEL_FILE")
    echo "Device model: $MODEL"
    if echo "$MODEL" | grep -q "Raspberry Pi"; then
        echo "Raspberry Pi detected. Installing GPIO backends..."
        sudo apt-get update --quiet
        sudo apt-get install -y --quiet swig python3-dev build-essential python3-rpi.gpio python3-pigpio python3-lgpio
        echo "GPIO backends installed."
        USE_SYSTEM_SITE_PACKAGES=true
    else
        echo "Not a Raspberry Pi, skipping GPIO backend install."
    fi
else
    echo "Model file not found, assuming not Raspberry Pi."
fi

# 2. Robust Virtual Environment Creation & Auto-Install
if [ ! -d ".venv" ] || [ ! -f ".venv/bin/pip" ]; then
    echo "Checking virtual environment status..."
    rm -rf .venv

    # Try creating the venv with or without Pi-specific flags
    if [ "$USE_SYSTEM_SITE_PACKAGES" = true ]; then
        echo "Creating virtual environment with system site packages..."
        python3 -m venv --system-site-packages .venv 2>/dev/null
    else
        echo "Creating standard virtual environment..."
        python3 -m venv .venv 2>/dev/null
    fi

    # If it failed because pip/venv is missing on a Debian/Ubuntu system
    if [ ! -f ".venv/bin/pip" ]; then
        echo "Virtual environment creation failed. Detecting package manager..."
        
        if command -v apt-get &> /dev/null; then
            echo "Debian/Ubuntu system detected. Attempting to install missing venv package..."
            
            # Dynamically find the current python version suffix (e.g., python3.14-venv)
            PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
            VENV_PACKAGE="python3.${PYTHON_VERSION#3.}-venv"
            
            echo "This requires administrator privileges. Please enter your password to install $VENV_PACKAGE:"
            sudo apt-get update && sudo apt-get install -y "$VENV_PACKAGE"
            
            # Retry creating the venv after installation
            echo "Retrying virtual environment creation..."
            if [ "$USE_SYSTEM_SITE_PACKAGES" = true ]; then
                python3 -m venv --system-site-packages .venv
            else
                python3 -m venv .venv
            fi
        fi
        
        # Double check if the retry worked
        if [ ! -f ".venv/bin/pip" ]; then
            echo "=========================================================="
            echo "ERROR: Could not automatically install the venv package."
            echo "Please manually install the python3-venv package for your system."
            echo "=========================================================="
            exit 1
        fi
    fi
fi

# 3. Use venv Python/Pip
PYTHON=".venv/bin/python"
PIP=".venv/bin/pip"

echo "Using Python: $($PYTHON --version)"

# 4. Git Updates and Dependencies
if ping -q -c 1 -W 1 8.8.8.8 >/dev/null; then
    echo "Internet connection found. Checking for updates..."

    if [ ! -d ".git" ]; then
        echo "Nie znaleziono repozytorium git w $(pwd)"
    else
        echo "Updating Launcher via System Git..."
        git pull origin main
    fi

    echo "Installing/Updating requirements..."
    "$PIP" install --upgrade pip --quiet
    "$PIP" install --upgrade -r requirements.txt --quiet

    echo "Updates finished or already up to date."
else
    echo "No internet connection. Skipping updates."
fi

# 5. Launch
echo "Starting program..."
"$PYTHON" src/main.py