# ==========================
# library.py (with bottom bar)
# ==========================
import pygame
import os
import subprocess
import sys
import json
from States.generic_state import BaseState
from settings import GAMES_DIR, BASE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.searchbar import SearchBar
from UI.game_icon import GameIcon


class Library(BaseState):
    def __init__(self, launcher):
        super().__init__(launcher)

        # ---------- UI FOCUS ----------
        # content | sidebar | topbar | bottombar | searchbar
        self.ui_focus = "content"
        self.bottombar_visible = False

        # ---------- LOAD MANIFEST ----------
        self.manifest_path = os.path.join(BASE_DIR, 'code', 'Store', 'games_manifest.json')
        self.manifest = self.load_manifest()

        # ---------- GAMES ----------
        self.games_list = [
            name for name in os.listdir(GAMES_DIR)
            if os.path.isdir(os.path.join(GAMES_DIR, name))
        ]
        self.filtered_games = self.games_list.copy()
        self.selected_index = 0

        # ---------- UI ----------
        self.searchbar = SearchBar(
            launcher,
            on_change=self.apply_search_filter
        )

        # ---------- FONTS ----------
        self.game_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.06))
        self.internet_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.02), bold=True)
        self.bottombar_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.025))

        # ---------- TOP BAR ----------
        self.topbar_h = int(WINDOW_HEIGHT * 0.1)

        # ---------- ICONS ----------
        self.icon_w = int(WINDOW_WIDTH * 0.2)
        self.spacing = 40
        self.scroll_speed = 6
        self.current_scroll = 0

        self.icon_group = pygame.sprite.Group()
        self.game_icons = {}
        self.refresh_library()

    # ==================================================
    # INPUT
    # ==================================================
    def handling_events(self, events):
        keys = pygame.key.get_just_pressed()

        # SEARCHBAR
        exited_search = self.searchbar.handle_events(events)
        if exited_search:
            self.ui_focus = "content"
            return
        if self.searchbar.active:
            return

        initial_focus = self.ui_focus
        super().handling_events(events)
        if initial_focus != self.ui_focus:
            return

        # ---------- CONTENT NAVIGATION ----------
        if self.ui_focus == "content":
            if keys[pygame.K_UP]:
                self.ui_focus = "topbar"
            elif keys[pygame.K_DOWN]:
                if self.filtered_games:
                    self.selected_index = min(self.selected_index + 1, len(self.filtered_games) - 1)
            elif keys[pygame.K_LEFT]:
                if self.selected_index > 0:
                    self.selected_index -= 1
                else:
                    self.ui_focus = "sidebar"
            elif keys[pygame.K_RIGHT]:
                if self.filtered_games:
                    self.selected_index = min(self.selected_index + 1, len(self.filtered_games) - 1)
            elif keys[pygame.K_TAB]:
                self.bottombar_visible = not self.bottombar_visible
                if self.bottombar_visible:
                    self.ui_focus = "bottombar"
            elif keys[pygame.K_RETURN] or keys[pygame.K_r]:
                self.launch_game()

        # ---------- TOP BAR ----------
        elif self.ui_focus == "topbar":
            if keys[pygame.K_DOWN]:
                self.ui_focus = "content"
            elif keys[pygame.K_RETURN]:
                self.searchbar.active = True

        # ---------- BOTTOM BAR ----------
        elif self.ui_focus == "bottombar":
            if keys[pygame.K_TAB] or keys[pygame.K_ESCAPE]:
                self.ui_focus = "content"
                self.bottombar_visible = False
            elif keys[pygame.K_RETURN]:
                game = self.filtered_games[self.selected_index]
                success = self.launcher.installer.remove(game)
                if success:
                    self.refresh_library()
                    self.ui_focus = "content"
                    self.bottombar_visible = False

    # ==================================================
    # UPDATE
    # ==================================================
    def update(self, delta_time):
        super().update(delta_time)
        self.current_scroll += (self.selected_index - self.current_scroll) * self.scroll_speed * delta_time

    # ==================================================
    # DRAW
    # ==================================================
    def draw(self, window):
        self.draw_game_icons(window)
        self.draw_topbar(window)
        if self.bottombar_visible:
            self.draw_bottombar(window)

        self.searchbar.draw(window, focused=self.ui_focus in ["topbar", "searchbar"])
        super().draw(window)

    def draw_game_icons(self, window):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])

        if not self.filtered_games:
            msg = self.game_font.render("NO GAMES FOUND", True, theme['colour_2'])
            window.blit(msg, (WINDOW_WIDTH // 2 - msg.get_width() // 2, WINDOW_HEIGHT // 2))
            return

        center_x = self.sidebar.current_w + (WINDOW_WIDTH - self.sidebar.current_w) // 2 - 100
        center_y = WINDOW_HEIGHT // 2

        for i, game in enumerate(self.filtered_games):
            icon = self.game_icons.get(game)
            if not icon:
                continue

            offset = (i - self.current_scroll) * (self.icon_w + self.spacing)
            x = center_x + offset
            y = center_y

            icon.set_position(x, y)
            icon.set_selected(i == self.selected_index and self.ui_focus == "content")
            icon.draw(window)

            if i == self.selected_index and self.ui_focus == "content":
                name = game.replace("_", " ").upper()
                text = self.game_font.render(name, True, theme['colour_3'])
                window.blit(text, (x - text.get_width() // 2, y - self.icon_w // 2 - 80))

    def draw_topbar(self, window):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        pygame.draw.rect(window, theme['colour_1'], (0, 0, WINDOW_WIDTH, self.topbar_h))

    def draw_bottombar(self, window):
        if not self.filtered_games:
            return
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        game_id = self.filtered_games[self.selected_index]

        game_data = self.manifest.get(game_id, {})
        author = game_data.get("author", "Unknown")
        description = game_data.get("description", "")
        version = game_data.get("version", "unknown")

        panel_h = 120
        pygame.draw.rect(window, theme['colour_2'], (0, WINDOW_HEIGHT - panel_h, WINDOW_WIDTH, panel_h))
        pygame.draw.rect(window, theme['colour_4'], (0, WINDOW_HEIGHT - panel_h, WINDOW_WIDTH, panel_h), 3)

        author_text = self.bottombar_font.render(f"Author: {author}", True, theme['colour_3'])
        desc_text = self.bottombar_font.render(description, True, theme['colour_3'])
        version_text = self.bottombar_font.render(f"Version: {version}", True, theme['colour_3'])
        uninstall_text = self.bottombar_font.render("Press ENTER to Uninstall", True, (255, 80, 80))

        window.blit(author_text, (20, WINDOW_HEIGHT - panel_h + 10))
        window.blit(desc_text, (20, WINDOW_HEIGHT - panel_h + 40))
        window.blit(version_text, (20, WINDOW_HEIGHT - panel_h + 70))
        window.blit(uninstall_text, (WINDOW_WIDTH - 300, WINDOW_HEIGHT - panel_h + 40))

    # ==================================================
    # LOGIC
    # ==================================================
    def load_manifest(self):
        if not os.path.exists(self.manifest_path):
            return {}
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Library] Failed to load manifest: {e}")
            return {}

    def apply_search_filter(self, query):
        query = query.lower()
        self.filtered_games = [g for g in self.games_list if query in g.lower()] if query else self.games_list.copy()
        self.selected_index = 0

    def launch_game(self):
        if not self.filtered_games or self.launcher.game_running:
            return

        game = self.filtered_games[self.selected_index]
        game_dir = os.path.join(GAMES_DIR, game)
        main_path = os.path.join(game_dir, "code", "main.py")
        if not os.path.exists(main_path):
            main_path = os.path.join(game_dir, "main.py")

        try:
            print(f"Launching {game}...")
            process = subprocess.Popen([sys.executable, main_path], cwd=game_dir)
            self.launcher.game_process = process
            self.launcher.game_running = True
            pygame.display.iconify()
        except Exception as e:
            print(f"Launch error: {e}")

    def on_enter(self):
        self.refresh_library()

    def refresh_library(self):
        current_folders = [name for name in os.listdir(GAMES_DIR) if os.path.isdir(os.path.join(GAMES_DIR, name))]

        # Add new icons
        for game in current_folders:
            if game not in self.game_icons:
                icon = GameIcon(
                    launcher=self.launcher,
                    groups=self.icon_group,
                    game_id=game,
                    size=self.icon_w,
                    source="library"
                )
                self.game_icons[game] = icon

        # Remove deleted icons
        removed_games = set(self.game_icons.keys()) - set(current_folders)
        for game in removed_games:
            self.game_icons[game].kill()
            del self.game_icons[game]

        self.games_list = current_folders
        self.apply_search_filter(self.searchbar.text)
        if self.selected_index >= len(self.filtered_games) and self.filtered_games:
            self.selected_index = len(self.filtered_games) - 1
