# ==========================
# store.py (POPRAWIONY POD SEARCHBAR)
# ==========================
import pygame
import json
from os.path import join

from settings import BASE_DIR, GAMES_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.store_entry import StoreEntry, GameStatus
from UI.searchbar import SearchBar
from States.generic_state import BaseState


class Store(BaseState):
    def __init__(self, launcher):
        super().__init__(launcher)

        # ---------- INTERNET ----------
        self.online = launcher.checking_internet_connection()
        self.reconnect_cooldown = 0.0

        # ---------- UI FOCUS ----------
        self.ui_focus = "content"  # content | sidebar | topbar | searchbar

        # ---------- SEARCHBAR ----------
        self.searchbar = SearchBar(
            launcher,
            on_change=self.apply_search_filter
        )

        # ---------- GAME DATA ----------
        self.manifest = self.load_manifest()

        self.all_games = list(self.manifest.keys())
        self.filtered_games = self.all_games.copy()
        self.selected_index = 0

        # ---------- STORE ENTRIES ----------
        self.entry_height = 300
        self.spacing = 10
        self.entries = []

        self.scroll = 0
        self.scroll_speed = 400

        self.load_store_entries()

    # ==================================================
    # DATA
    # ==================================================
    def load_manifest(self):
        path = join(BASE_DIR, 'code', 'Store', 'games_manifest.json')
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_store_entries(self):
        self.entries.clear()
        y = 150

        for game_id in self.filtered_games:
            data = self.manifest[game_id]
            manifest_version = data.get('version')

            if not self.launcher.installer.is_installed(game_id):
                status = GameStatus.NOT_INSTALLED
            elif self.launcher.installer.has_update(game_id, manifest_version):
                status = GameStatus.UPDATE_AVAILABLE
            else:
                status = GameStatus.INSTALLED

            entry = StoreEntry(
                launcher=self.launcher,
                game_id=game_id,
                game_data=data,
                status=status,
                size=(WINDOW_WIDTH - 100 - self.sidebar.base_w, self.entry_height),
                position=(50 + self.sidebar.base_w, y)
            )
            self.entries.append(entry)
            y += self.entry_height + self.spacing

    # ==================================================
    # INPUT
    # ==================================================
    def handling_events(self, events):
        keys = pygame.key.get_just_pressed()

        # 1. SIDEBAR LOGIC
        if self.ui_focus == "sidebar":
            self.sidebar.handle_input(keys, self.ui_focus)
            if keys[pygame.K_RIGHT] or keys[pygame.K_TAB]:
                self.ui_focus = "content"
                return # Kończymy przetwarzanie w tej klatce, żeby nie "odbiło" z powrotem

        # 2. SEARCHBAR LOGIC
        elif self.ui_focus == "searchbar" and self.online:
            if not self.searchbar.active:
                self.searchbar.active = True

            exited_search = self.searchbar.handle_events(events)
            if exited_search:
                self.ui_focus = "content"
                self.searchbar.active = False
            return

        # 3. CONTENT NAVIGATION
        elif self.ui_focus == "content":
            if keys[pygame.K_UP]:
                if self.selected_index == 0 and self.online:
                    self.ui_focus = 'searchbar'
                    self.searchbar.active = True
                else:
                    self.selected_index = max(0, self.selected_index - 1)
            elif keys[pygame.K_DOWN]:
                self.selected_index = min(len(self.entries) - 1, self.selected_index + 1)
            elif keys[pygame.K_LEFT] or keys[pygame.K_TAB]:
                self.ui_focus = "sidebar"
            elif keys[pygame.K_RETURN]:
                self.install_or_update_selected()

    # ==================================================
    # UPDATE
    # ==================================================
    def update(self, delta_time):
        super().update(delta_time)

        if not self.entries:
            return

        target_y = self.entries[self.selected_index].rect.top
        if target_y < self.scroll + 150:
            self.scroll -= self.scroll_speed * delta_time
        elif target_y + self.entry_height > self.scroll + WINDOW_HEIGHT - 50:
            self.scroll += self.scroll_speed * delta_time

        self.scroll = max(0, self.scroll)

    # ==================================================
    # DRAW
    # ==================================================
    def draw(self, window):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])

        # DRAW STORE ENTRIES
        for i, entry in enumerate(self.entries):
            selected = i == self.selected_index and self.ui_focus == "content"
            entry.icon.set_selected(selected)
            entry.rect.top = 150 + i * (self.entry_height + self.spacing) - self.scroll
            entry.draw(window)

        # DRAW SEARCHBAR only when online
        if self.online:
            self.searchbar.draw(window, focused=self.ui_focus in ["topbar", "searchbar"])

        # always draw sidebar on top
        super().draw(window)

    # ==================================================
    # LOGIC
    # ==================================================
    def apply_search_filter(self, query):
        query = query.lower()
        self.filtered_games = [
            g for g in self.all_games if query in g.lower()
        ] if query else self.all_games.copy()
        self.selected_index = 0
        self.load_store_entries()

    def install_or_update_selected(self):
        if not self.entries:
            return

        entry = self.entries[self.selected_index]
        game_id = entry.game_id
        data = entry.game_data
        manifest_version = data.get('version')

        if entry.status == GameStatus.NOT_INSTALLED:
            self.launcher.installer.install(
                game_id,
                data['repo'],
                manifest_version
            )
        elif entry.status == GameStatus.UPDATE_AVAILABLE:
            self.launcher.installer.update(
                game_id,
                manifest_version
            )

        # 🔹 reload entries to update statuses
        self.load_store_entries()

    def on_enter(self):
        """
        Wywoływane gdy wchodzimy do Store.
        Odświeżamy listę gier i statusy instalacji.
        """
        # Sprawdź ponownie połączenie z internetem
        self.online = self.launcher.checking_internet_connection()

        # Odśwież wpisy w sklepie, aby statusy instalacji były aktualne
        self.load_store_entries()
