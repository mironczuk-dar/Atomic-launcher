# IMPORTING LIBRARIES
import subprocess
from os.path import join, exists
import os
import shutil

class GameInstaller:
    def __init__(self, games_dir):
        self.games_dir = games_dir

    # =========================
    # CHECK INSTALLATION
    # =========================
    def is_installed(self, game_id: str) -> bool:
        return exists(join(self.games_dir, game_id))

    # =========================
    # INSTALL
    # =========================
    def install(self, game_id: str, repo_url: str, branch: str = "main") -> bool:
        """
        Clones the repository. Returns True if successful, False if error occurs.
        """
        target = join(self.games_dir, game_id)
        if self.is_installed(game_id):
            print(f"[Installer] {game_id} already installed.")
            return True

        try:
            print(f"[Installer] Installing {game_id} from {repo_url}...")
            subprocess.run(
                ["git", "clone", "-b", branch, repo_url, target],
                check=True
            )
            print(f"[Installer] {game_id} installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[Installer] Failed to install {game_id}: {e}")
            if exists(target):
                shutil.rmtree(target)
            return False

    # =========================
    # UPDATE
    # =========================
    def update(self, game_id: str, branch: str = "main") -> bool:
        """
        Pulls the latest changes. Returns True if successful, False if error occurs.
        """
        target = join(self.games_dir, game_id)
        if not self.is_installed(game_id):
            print(f"[Installer] {game_id} is not installed, cannot update.")
            return False

        try:
            print(f"[Installer] Updating {game_id}...")
            subprocess.run(
                ["git", "fetch", "--all"],
                cwd=target,
                check=True
            )
            subprocess.run(
                ["git", "reset", "--hard", f"origin/{branch}"],
                cwd=target,
                check=True
            )
            print(f"[Installer] {game_id} updated successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[Installer] Failed to update {game_id}: {e}")
            return False

    # =========================
    # REMOVE
    # =========================
    def remove(self, game_id: str) -> bool:
        """
        Deletes the installed game folder.
        """
        target = join(self.games_dir, game_id)
        if not self.is_installed(game_id):
            return False
        try:
            shutil.rmtree(target)
            print(f"[Installer] {game_id} removed successfully.")
            return True
        except Exception as e:
            print(f"[Installer] Failed to remove {game_id}: {e}")
            return False
