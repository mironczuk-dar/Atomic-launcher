#!/bin/bash

echo "Checking for Python..."

# CHECKING IF PYTHON IS INSTALLED
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed!"
    echo "Please install it using your package manager."
    exit 1
fi

echo "Python is installed."

# --- UPDATING ---
# CHECKING IF THERE'S INTERNET BY PINGING GOOGLE
if ping -q -c 1 -W 1 8.8.8.8 >/dev/null; then
    echo "Internet connection found. Checking for updates..."
    
    # 1. UPDATING CODE FROM GITHUB
    echo "Pulling latest code from GitHub..."
    git pull origin main --no-rebase
    
    # 2. UPDATING LIBRARIES
    sudo pip install --upgrade pygame-ce pytmx --break-system-packages --quiet
    
    echo "Updates finished or already up to date."
else
    echo "No internet connection. Skipping updates."
fi
# ---------------------------

echo "Starting DonutPi OS..."
export DISPLAY=:0
python3 code/main.py