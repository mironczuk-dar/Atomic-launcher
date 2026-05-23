from pathlib import Path
import subprocess
import shutil
import json
import os
import stat
from typing import Optional
import threading

class GameInstaller:

    def __init__(self, games_dir: str):
        self.games_dir = Path(games_dir)
        self.games_dir.mkdir(parents=True, exist_ok=True)
        self.is_downloading = False
        self.current_game_id = None
        self.download_progress = 0
        self.download_queue = []
        self.current_process = None

    def remove_readonly(self, func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def _get_git_executable(self) -> str:
        """
        Zwraca pełną ścieżkę do pliku wykonywalnego git lub 'git', 
        jeśli uda się go znaleźć tylko w PATH.
        """
        # Znajdź główny folder projektu (Atomic-launcher)
        # Przechodzimy w górę: Machines -> src (lub code) -> Atomic-launcher
        root_dir = Path(__file__).resolve().parent.parent.parent
        portable_git_path = root_dir / "PortableGit" / "cmd" / "git.exe"

        # 1. Najpierw sprawdzamy naszą przenośną wersję
        if portable_git_path.exists():
            return str(portable_git_path)

        # 2. Sprawdzamy systemowy PATH
        git_path = shutil.which("git")
        if git_path:
            return git_path
        
        # 3. Awaryjne ścieżki dla systemu Windows
        possible_paths = [
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files\Git\cmd\git.exe"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        # Ostateczny fallback - próbujemy wywołać po nazwie
        return "git"

    # ==================================================
    # BASIC STATE
    # ==================================================
    def is_installed(self, game_id: str) -> bool:
        return (self.games_dir / game_id).exists()

    # ==================================================
    # VERSION HANDLING (MANIFEST-BASED)
    # ==================================================
    def get_local_version(self, game_id: str) -> Optional[str]:
        path = self.games_dir / game_id / "version.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("version")
        except Exception as e:
            print(f"[Installer] Błąd odczytu version.json ({game_id}): {e}")
            return None

    def write_local_version(self, game_id: str, version: str) -> None:
        path = self.games_dir / game_id / "version.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"version": version}, f, indent=2)
        except Exception as e:
            print(f"[Installer] Błąd zapisu version.json ({game_id}): {e}")

    def has_update(self, game_id: str, manifest_version: str) -> bool:
        local = self.get_local_version(game_id)
        if local is None:
            return False
        return local != manifest_version

    # ==================================================
    # INSTALL
    # ==================================================
    def install(self, game_id, repo_url, manifest_version, branch="main") -> bool:
        target = self.games_dir / game_id
        self.current_game_id = game_id
        self.download_progress = 0
        
        git_cmd = self._get_git_executable()

        try:
            # Używamy --progress, aby Git wysyłał dane o procentach
            process = subprocess.Popen(
                [git_cmd, "clone", "--progress", "--depth", "1", "-b", branch, repo_url, str(target)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Przekierowujemy błędy do stdout, by czytać wszystko razem
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.current_process = process

            # Czytamy strumień danych linijka po linijce
            for line in process.stdout:
                # Szukamy wzorca procentów, np. "Receiving objects:  55%"
                if "%" in line:
                    parts = line.split("%")[0].split()
                    if parts:
                        try:
                            # Wyciągamy ostatnią liczbę przed znakiem %
                            val = int(parts[-1])
                            self.download_progress = val
                        except ValueError:
                            pass

            process.wait() # Czekamy na zakończenie procesu

            if process.returncode == 0:
                self.write_local_version(game_id, manifest_version)
                return True
            else:
                if target.exists(): shutil.rmtree(target, onerror=self.remove_readonly)
                return False

        finally:
            self.current_game_id = None
            self.download_progress = 0
            self.current_process = None

    # ==================================================
    # UPDATE
    # ==================================================
    def update(
        self,
        game_id: str,
        manifest_version: str,
        branch: str = "main"
    ) -> bool:
        target = self.games_dir / game_id

        if not self.is_installed(game_id):
            print(f"[Installer] {game_id} nie jest zainstalowany.")
            return False
        
        # Ustawiamy stan pobierania przed rozpoczęciem procesów
        self.current_game_id = game_id
        
        git_cmd = self._get_git_executable()

        try:
            print(f"[Installer] Aktualizowanie {game_id}...")

            # Wykonujemy operacje Gita. 
            # capture_output=True sprawia, że logi są przechwytywane pod maską.
            subprocess.run(
                [git_cmd, "fetch", "origin", branch],
                cwd=target,
                check=True,
                capture_output=True,
                text=True
            )
            subprocess.run(
                [git_cmd, "reset", "--hard", f"origin/{branch}"],
                cwd=target,
                check=True,
                capture_output=True,
                text=True
            )
            subprocess.run(
                [git_cmd, "clean", "-fd"],
                cwd=target,
                check=True,
                capture_output=True,
                text=True
            )

            # Synchronizacja wersji z manifestem
            self.write_local_version(game_id, manifest_version)

            print(f"[Installer] {game_id} zaktualizowany pomyślnie.")
            return True

        except subprocess.CalledProcessError as e:
            # Wypisujemy błąd z e.stderr, jeśli Git coś zgłosił
            error_msg = e.stderr if e.stderr else str(e)
            print(f"[Installer] BŁĄD aktualizacji {game_id}: {error_msg}")
            return False
        
        except Exception as e:
            print(f"[Installer] Nieoczekiwany błąd podczas aktualizacji: {e}")
            return False

        finally:
            # TO JEST KLUCZOWE: 
            # Niezależnie od tego czy się udało, czy wywaliło błąd, 
            # musimy "odblokować" launcher dla użytkownika.
            self.current_game_id = None
            self.process_queue()

    def process_queue(self):
        if self.download_queue and not self.is_downloading:
            game_id, repo, version = self.download_queue.pop(0)
            self._start_download(game_id, repo, version)

    def _start_download(self, game_id, repo, version):
        self.is_downloading = True
        self.current_game_id = game_id
        self.download_progress = 0
        threading.Thread(target=self._download_game, args=(game_id, repo, version), daemon=True).start()

    def _download_game(self, game_id, repo, version):
        try:
            self.install(game_id, repo, version)
        finally:
            self.is_downloading = False
            self.current_game_id = None
            self.process_queue()

    def cancel_download(self):
        self.download_queue = []
        self.is_downloading = False
        self.current_game_id = None
        if self.current_process:
            self.current_process.terminate()
            self.current_process = None

    # ==================================================
    # REMOVE
    # ==================================================
    def remove(self, game_id: str) -> bool:
        target = self.games_dir / game_id
        if not self.is_installed(game_id):
            return False
        try:
            shutil.rmtree(target, onerror=self.remove_readonly)
            print(f"[Installer] {game_id} usunięty.")
            return True
        except Exception as e:
            print(f"[Installer] BŁĄD przy usuwaniu {game_id}: {e}")
            return False