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

# --- UPDATING ---
if ping -q -c 1 -W 1 8.8.8.8 >/dev/null; then
    echo "Internet connection found. Checking for updates..."
    
    if [ ! -d ".git" ]; then
        echo "Nie znaleziono repozytorium git w $(pwd)"
    else
        git pull origin main
    fi

    sudo pip install --upgrade pygame-ce pytmx --break-system-packages --quiet
    echo "Updates finished or already up to date."
else
    echo "No internet connection. Skipping updates."
fi

echo "Starting DonutPi OS..."
python3 code/main.py
