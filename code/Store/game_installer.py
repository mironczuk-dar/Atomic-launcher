from pathlib import Path
import subprocess
import shutil
import json
from typing import Optional


class GameInstaller:
    """
    GameInstaller
    ----------------
    - Git służy WYŁĄCZNIE do pobierania plików
    - Manifest jest jedynym źródłem prawdy o wersji
    - version.json jest synchronizowany po install/update
    """

    def __init__(self, games_dir: str):
        self.games_dir = Path(games_dir)
        self.games_dir.mkdir(parents=True, exist_ok=True)

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
    def install(
        self,
        game_id: str,
        repo_url: str,
        manifest_version: str,
        branch: str = "main"
    ) -> bool:
        target = self.games_dir / game_id

        if self.is_installed(game_id):
            print(f"[Installer] {game_id} już jest zainstalowany.")
            return True

        try:
            print(f"[Installer] Instalowanie {game_id}...")
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "-b",
                    branch,
                    repo_url,
                    str(target)
                ],
                check=True
            )

            # 🔥 KLUCZOWE: synchronizacja wersji z manifestu
            self.write_local_version(game_id, manifest_version)

            print(f"[Installer] {game_id} zainstalowany pomyślnie.")
            return True

        except subprocess.CalledProcessError as e:
            print(f"[Installer] BŁĄD instalacji {game_id}: {e}")
            if target.exists():
                shutil.rmtree(target)
            return False

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

        try:
            print(f"[Installer] Aktualizowanie {game_id}...")

            subprocess.run(
                ["git", "fetch", "origin", branch],
                cwd=target,
                check=True
            )
            subprocess.run(
                ["git", "reset", "--hard", f"origin/{branch}"],
                cwd=target,
                check=True
            )
            subprocess.run(
                ["git", "clean", "-fd"],
                cwd=target,
                check=True
            )

            # 🔥 KLUCZOWE: zapis wersji z manifestu
            self.write_local_version(game_id, manifest_version)

            print(f"[Installer] {game_id} zaktualizowany.")
            return True

        except subprocess.CalledProcessError as e:
            print(f"[Installer] BŁĄD aktualizacji {game_id}: {e}")
            return False

    # ==================================================
    # REMOVE
    # ==================================================
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
