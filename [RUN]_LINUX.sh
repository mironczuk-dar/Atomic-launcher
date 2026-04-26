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
        git pull origin main
    fi

    "$PIP" install --upgrade pip --quiet
    "$PIP" install --upgrade -r requirements.txt --quiet

    echo "Updates finished or already up to date."
else
    echo "No internet connection. Skipping updates."
fi

echo "Starting DonutPi OS..."
"$PYTHON" code/main.py