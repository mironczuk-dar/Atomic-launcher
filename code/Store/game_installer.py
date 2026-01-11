import subprocess
import shutil
from pathlib import Path

class GameInstaller:
    def __init__(self, games_dir: str):
        # Path automatycznie dba o poprawne ukośniki (Windows vs Linux)
        self.games_dir = Path(games_dir)
        # Tworzy folder gier, jeśli go nie ma
        self.games_dir.mkdir(parents=True, exist_ok=True)

    def is_installed(self, game_id: str) -> bool:
        return (self.games_dir / game_id).exists()

    def install(self, game_id: str, repo_url: str, branch: str = "main") -> bool:
        target = self.games_dir / game_id
        
        if self.is_installed(game_id):
            print(f"[Installer] {game_id} już jest zainstalowany.")
            return True

        try:
            print(f"[Installer] Instalowanie {game_id}...")
            # --depth 1: pobiera tylko najnowsze pliki (oszczędza czas i miejsce)
            subprocess.run(
                ["git", "clone", "--depth", "1", "-b", branch, repo_url, str(target)],
                check=True
            )
            print(f"[Installer] {game_id} zainstalowany pomyślnie.")
            return True
        except subprocess.CalledProcessError:
            print(f"[Installer] BŁĄD: Nie udało się zainstalować {game_id}.")
            if target.exists():
                shutil.rmtree(target)
            return False

    def update(self, game_id: str, branch: str = "main") -> bool:
        target = self.games_dir / game_id
        
        if not self.is_installed(game_id):
            print(f"[Installer] {game_id} nie jest zainstalowany.")
            return False

        try:
            print(f"[Installer] Aktualizowanie {game_id}...")
            # Fetch pobiera info o zmianach, reset --hard wymusza stan z serwera
            # git clean usuwa pliki, których nie ma w repozytorium (np. śmieci)
            subprocess.run(["git", "fetch", "origin", branch], cwd=target, check=True)
            subprocess.run(["git", "reset", "--hard", f"origin/{branch}"], cwd=target, check=True)
            subprocess.run(["git", "clean", "-fd"], cwd=target, check=True)
            
            print(f"[Installer] {game_id} zaktualizowany.")
            return True
        except subprocess.CalledProcessError:
            print(f"[Installer] BŁĄD: Aktualizacja {game_id} nie powiodła się.")
            return False

    def remove(self, game_id: str) -> bool:
        target = self.games_dir / game_id
        if not self.is_installed(game_id):
            return False
        try:
            shutil.rmtree(target)
            print(f"[Installer] {game_id} usunięty.")
            return True
        except Exception as e:
            print(f"[Installer] BŁĄD przy usuwaniu {game_id}: {e}")
            return False