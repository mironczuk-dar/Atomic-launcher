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

# Check if Raspberry Pi and install GPIO backends if needed
MODEL_FILE="/proc/device-tree/model"
if [ -f "$MODEL_FILE" ]; then
    MODEL=$(tr -d '\0' < "$MODEL_FILE")
    echo "Device model: $MODEL"
    if echo "$MODEL" | grep -q "Raspberry Pi"; then
        echo "Raspberry Pi detected. Installing GPIO backends..."
        sudo apt update --quiet
        sudo apt install -y --quiet swig python3-dev build-essential python3-rpi.gpio python3-pigpio python3-lgpio
        echo "GPIO backends installed."
        echo "Recreating virtual environment with system site packages..."
        rm -rf .venv
        python3 -m venv --system-site-packages .venv
    else
        echo "Not a Raspberry Pi, skipping GPIO backend install."
    fi
else
    echo "Model file not found, assuming not Raspberry Pi."
fi

# Create venv if missing
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Use venv Python/Pip
PYTHON=".venv/bin/python"
PIP=".venv/bin/pip"

echo "Using Python: $($PYTHON --version)"

# --- UPDATING ---
if ping -q -c 1 -W 1 8.8.8.8 >/dev/null; then
    echo "Internet connection found. Checking for updates..."

    if [ ! -d ".git" ]; then
        echo "Nie znaleziono repozytorium git w $(pwd)"
    else
        git pull origin pi-testing
    fi

    "$PIP" install --upgrade pip --quiet
    "$PIP" install --upgrade -r requirements.txt --quiet

    echo "Updates finished or already up to date."
else
    echo "No internet connection. Skipping updates."
fi

echo "Starting Atomic Launcher..."
"$PYTHON" src/main.py