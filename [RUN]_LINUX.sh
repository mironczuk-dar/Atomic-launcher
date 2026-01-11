#!/bin/bash

# 1. PRZEJŚCIE DO KATALOGU LAUNCHERA
cd "/home/pi/Atomic-launcher"

# 2. FUNKCJA AUTO-INSTALACJI PAKIETÓW
install_missing() {
    PACKAGE=$1
    if ! command -v $PACKAGE &> /dev/null; then
        echo "[Installer] $PACKAGE nie znaleziony. Próba instalacji..."
        if ping -q -c 1 -W 1 8.8.8.8 >/dev/null; then
            sudo apt update
            sudo apt install $PACKAGE -y
        else
            echo "[Error] Brak internetu! Nie można zainstalować $PACKAGE."
            exit 1
        fi
    fi
}

# Sprawdzanie i instalacja podstawowych narzędzi
install_missing "python3"
install_missing "git"
install_missing "python3-pip"

# 3. AKTUALIZACJA KODU I BIBLIOTEK (TYLKO PRZY STARCIE)
if ping -q -c 1 -W 1 8.8.8.8 >/dev/null; then
    echo "[Update] Połączenie aktywne. Sprawdzanie aktualizacji..."
    
    # Aktualizacja kodu launchera
    git pull origin main --no-rebase
    
    # Aktualizacja wymaganych bibliotek Pythona
    echo "[Update] Aktualizacja bibliotek Pythona..."
    sudo pip install --upgrade pygame-ce pytmx --break-system-packages --quiet
    
    echo "[Update] Gotowe."
else
    echo "[Update] Brak internetu. Pomijanie aktualizacji."
fi

echo "Starting DonutPi OS..."

# 4. GŁÓWNA PĘTLA KIOSKU (Launcher <-> Gry)
while true; do
    echo "[System] Uruchamianie Launchera..."
    
    # Uruchomienie launchera
    python3 code/main.py

    # Sprawdzenie czy launcher wygenerował polecenie uruchomienia gry
    if [ -f "/tmp/run_game.sh" ]; then
        echo "[System] Uruchamianie gry..."
        
        # Uruchomienie skryptu gry
        bash /tmp/run_game.sh
        
        # Usunięcie śladu po grze
        rm /tmp/run_game.sh
        
        echo "[System] Gra zakończona. Powrót do menu..."
    else
        # Jeśli nie ma pliku gry, oznacza to wyjście z programu
        echo "[System] Zamykanie launchera. Wyjście do terminala."
        break
    fi
done