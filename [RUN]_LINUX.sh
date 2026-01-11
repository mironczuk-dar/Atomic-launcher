#!/bin/bash

echo "Checking for Python..."

if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed!"
    exit 1
fi
echo "Python is installed."

# PRZECHODZIMY DO FOLDERU LAUNCHERA
cd "/home/pi/Atomic-launcher"

# --- UPDATING ---
if ping -q -c 1 -W 1 8.8.8.8 >/dev/null; then
    echo "Internet connection found. Checking for updates..."
    git pull origin main
    sudo pip install --upgrade pygame-ce pytmx --break-system-packages --quiet
    echo "Updates finished or already up to date."
else
    echo "No internet connection. Skipping updates."
fi

echo "Starting DonutPi OS..."

if [ -z "$DISPLAY" ] && [ "$XDG_SESSION_TYPE" != "wayland" ]; then
    echo "[System] Wykryto terminal (brak okien). Uruchamiam serwer X..."
    exec startx /usr/bin/python3 /home/pi/Atomic-launcher/code/main.py
else
    echo "[System] Wykryto środowisko graficzne. Uruchamiam bezpośrednio..."
    python3 code/main.py
fi
