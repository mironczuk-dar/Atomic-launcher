# ==========================
# library.py
# ==========================
import pygame
import os
import subprocess
import sys
import json
import shutil

from States.generic_state import BaseState
from settings import GAMES_DIR, BASE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.searchbar import SearchBar
from UI.game_icon import GameIcon


class Library(BaseState):
    def __init__(self, launcher):
        super().__init__(launcher)

        # ---------- LOCAL UI ----------
        self.bottombar_visible = False
        self.selected_bottombar_index = 0

        # ---------- LOAD MANIFEST ----------
        self.manifest_path = os.path.join(BASE_DIR, 'code', 'Store', 'games_manifest.json')
        self.manifest = self.load_manifest()

        # ---------- GAMES ----------
        self.games_list = []
        self.filtered_games = []
        self.selected_index = 0

        # ---------- SEARCHBAR ----------
        self.searchbar = SearchBar(
            launcher,
            on_change=self.apply_search_filter
        )

        # ---------- FONTS ----------
        self.game_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.05), bold=True)
        self.bottombar_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.025))

        # ---------- LAYOUT ----------
        self.topbar_h = int(WINDOW_HEIGHT * 0.1)
        self.icon_w = int(WINDOW_WIDTH * 0.2)
        self.spacing = 60
        self.scroll_speed = 8 # Nieco szybszy scroll dla responsywności
        self.current_scroll = 0

        self.icon_group = pygame.sprite.Group()
        self.game_icons = {}

        # ---------- BOTTOM BAR ACTIONS ----------
        self.bottombar_actions = [
            {"label": "Export Save", "callback": self.export_save_file},
            {"label": "Add to Favorites", "callback": self.add_to_favorites},
            {"label": "Uninstall", "callback": self.uninstall_game},
        ]

        self.refresh_library()

    # ==================================================
    # INPUT
    # ==================================================
    def handling_events(self, events):
        sm = self.launcher.state_manager
        
        # ⛔ NIE reagujemy, jeśli focus ≠ content (np. gdy sidebar ma focus)
        if sm.ui_focus != "content":
            return

        keys = pygame.key.get_just_pressed()

        # ---------- SEARCH ----------
        if self.searchbar.active:
            if self.searchbar.handle_events(events):
                self.searchbar.active = False
            return

        # ---------- BOTTOM BAR TOGGLE ----------
        if keys[pygame.K_e] and self.filtered_games:
            self.bottombar_visible = not self.bottombar_visible
            return

        # ---------- BOTTOM BAR NAV ----------
        if self.bottombar_visible:
            if keys[pygame.K_ESCAPE]:
                self.bottombar_visible = False
            elif keys[pygame.K_UP]:
                self.selected_bottombar_index = max(0, self.selected_bottombar_index - 1)
            elif keys[pygame.K_DOWN]:
                self.selected_bottombar_index = min(
                    len(self.bottombar_actions) - 1,
                    self.selected_bottombar_index + 1
                )
            elif keys[pygame.K_RETURN]:
                self.bottombar_actions[self.selected_bottombar_index]["callback"]()
            return

        # ---------- CONTENT NAV ----------
        if keys[pygame.K_LEFT]:
            if self.selected_index == 0:
                sm.ui_focus = "sidebar" # Przejście do sidebaru strzałką w lewo
            else:
                self.selected_index -= 1
        elif keys[pygame.K_RIGHT]:
            self.selected_index = min(len(self.filtered_games) - 1, self.selected_index + 1)
        elif keys[pygame.K_RETURN]:
            self.launch_game()
        elif keys[pygame.K_UP]:
            self.searchbar.active = True

    # ==================================================
    # UPDATE
    # ==================================================
    def update(self, delta_time):
        super().update(delta_time)
        # Płynny scroll do zaznaczonej gry
        self.current_scroll += (self.selected_index - self.current_scroll) * self.scroll_speed * delta_time

    # ==================================================
    # DRAW
    # ==================================================
    def draw(self, window):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])

        self.draw_game_icons(window)
        self.draw_topbar(window)

        if self.bottombar_visible:
            self.draw_bottombar(window)

        # Rysujemy searchbar (z przesunięciem o base_w sidebaru)
        self.searchbar.draw(window, focused=self.searchbar.active)

        super().draw(window)

    def draw_game_icons(self, window):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]

        if not self.filtered_games:
            msg = self.game_font.render("NO GAMES INSTALLED", True, theme['colour_2'])
            rect = msg.get_rect(center=((WINDOW_WIDTH + self.launcher.sidebar.base_w) // 2, WINDOW_HEIGHT // 2))
            window.blit(msg, rect)
            return

        sidebar_w = self.launcher.sidebar.base_w
        workspace_center_x = sidebar_w + (WINDOW_WIDTH - sidebar_w) // 2
        center_y = WINDOW_HEIGHT // 2

        for i, folder_name in enumerate(self.filtered_games):
            icon = self.game_icons.get(folder_name)
            if not icon: continue

            offset = (i - self.current_scroll) * (self.icon_w + self.spacing)
            x = workspace_center_x + offset
            y = center_y

            icon.set_position(x, y)
            icon.set_selected(i == self.selected_index)
            icon.draw(window)

            if i == self.selected_index:
                # TUTAJ POBIERAMY NAZWĘ Z MANIFESTU
                display_name = self.get_game_display_name(folder_name)
                text = self.game_font.render(display_name.upper(), True, theme['colour_3'])
                text_rect = text.get_rect(center=(x, y - self.icon_w // 2 - 60))
                window.blit(text, text_rect)

    def draw_topbar(self, window):
        # Topbar maskujący ikony wjeżdżające na górę (opcjonalnie)
        pass

    def draw_bottombar(self, window):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        panel_h = 140
        sidebar_w = self.launcher.sidebar.base_w

        # Tło dolnego panelu
        pygame.draw.rect(
            window,
            theme['colour_2'],
            (sidebar_w, WINDOW_HEIGHT - panel_h, WINDOW_WIDTH - sidebar_w, panel_h)
        )

        x = WINDOW_WIDTH - 250
        y = WINDOW_HEIGHT - panel_h + 20

        for i, action in enumerate(self.bottombar_actions):
            selected = i == self.selected_bottombar_index
            color = theme['colour_4'] if selected else theme['colour_3']
            label = f"> {action['label']}" if selected else action['label']
            text = self.bottombar_font.render(label, True, color)
            window.blit(text, (x, y + i * 35))

    # ==================================================
    # LOGIC
    # ==================================================
    def load_manifest(self):
        # Poprawiona ścieżka zgodnie z Twoją strukturą: Atomic-launcher/Store/games-manifest.json
        # Jeśli Store jest w folderze głównym obok code:
        path = os.path.join(BASE_DIR, 'Store', 'games-manifest.json')
        
        if not os.path.exists(path):
            print(f"Warning: Manifest not found at {path}")
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading manifest: {e}")
            return {}

    def get_game_display_name(self, folder_name):
        """Pobiera ładną nazwę z manifestu na podstawie nazwy folderu."""
        game_data = self.manifest.get(folder_name)
        if game_data and "name" in game_data:
            return game_data["name"]
        return folder_name.replace("_", " ").title() # Fallback: infinite_runner -> Infinite Runner

    def refresh_library(self):
        """Skanuje zainstalowane foldery i mapuje je na dane z manifestu."""
        self.manifest = self.load_manifest() # Odśwież manifest przy wjeździe
        
        if not os.path.exists(GAMES_DIR):
            os.makedirs(GAMES_DIR)
            self.games_list = []
        else:
            # Pobieramy foldery zainstalowanych gier
            self.games_list = [
                name for name in os.listdir(GAMES_DIR)
                if os.path.isdir(os.path.join(GAMES_DIR, name))
            ]

        # Aktualizacja ikon
        for folder_name in self.games_list:
            if folder_name not in self.game_icons:
                self.game_icons[folder_name] = GameIcon(
                    launcher=self.launcher,
                    groups=self.icon_group,
                    game_id=folder_name,
                    size=self.icon_w,
                    source="library"
                )

        # Usuwanie nieistniejących ikon
        current_icons = list(self.game_icons.keys())
        for folder_name in current_icons:
            if folder_name not in self.games_list:
                del self.game_icons[folder_name]

        self.apply_search_filter(self.searchbar.text)

    def apply_search_filter(self, query):
        query = query.lower()
        
        # Filtrujemy na podstawie ładnych nazw, a nie nazw folderów!
        self.filtered_games = []
        for folder_name in self.games_list:
            display_name = self.get_game_display_name(folder_name)
            if not query or query in display_name.lower():
                self.filtered_games.append(folder_name)
        
        self.selected_index = 0

    # ==================================================
    # BOTTOM BAR ACTIONS
    # ==================================================
    def uninstall_game(self):
        if not self.filtered_games: return
        
        game = self.filtered_games[self.selected_index]
        game_path = os.path.join(GAMES_DIR, game)
        
        try:
            if os.path.exists(game_path):
                shutil.rmtree(game_path)
                print(f"Uninstalled: {game}")
                self.refresh_library()
                self.bottombar_visible = False
                self.selected_index = max(0, self.selected_index - 1)
        except Exception as e:
            print(f"Uninstall failed: {e}")

    def add_to_favorites(self):
        print("Feature coming soon: Favorites")

    def export_save_file(self):
        print("Feature coming soon: Save export")

    def on_enter(self):
        self.refresh_library()

    def launch_game(self):
        """Uruchamia wybraną grę w nowym procesie."""
        if not self.filtered_games:
            return

        folder_name = self.filtered_games[self.selected_index]
        game_path = os.path.join(GAMES_DIR, folder_name, 'code')
        
        # Pobieramy informacje o pliku startowym z manifestu
        game_data = self.manifest.get(folder_name, {})
        main_file = game_data.get("mian.py", "main.py") # Domyślnie main.py
        
        full_path = os.path.join(game_path, main_file)

        if os.path.exists(full_path):
            try:
                print(f"Launching {folder_name} via {full_path}...")
                
                # Używamy sys.executable, aby gra uruchomiła się w tym samym środowisku Python
                # subprocess.Popen nie blokuje launchera (gra działa "obok")
                subprocess.Popen(
                    [sys.executable, full_path],
                    cwd=game_path, # Ustawienie katalogu roboczego na folder gry
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                )
                
            except Exception as e:
                print(f"Error launching game: {e}")
        else:
            print(f"Error: Could not find startup file at {full_path}")