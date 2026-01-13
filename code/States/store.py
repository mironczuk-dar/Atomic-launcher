# ==========================
# store.py (FULL – ONLINE/OFFLINE SAFE)
# ==========================
import pygame
import json
from os.path import join

from settings import BASE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.store_entry import StoreEntry, GameStatus
from UI.searchbar import SearchBar
from States.generic_state import BaseState


class Store(BaseState):
    def __init__(self, launcher):
        super().__init__(launcher)

        # ---------- INTERNET ----------
        self.online = launcher.checking_internet_connection()

        # ---------- UI FOCUS ----------
        self.ui_focus = "content"  # content | sidebar | searchbar

        # ---------- SEARCHBAR ----------
        self.searchbar = SearchBar(
            launcher,
            on_change=self.apply_search_filter
        )

        # ---------- DATA ----------
        self.manifest = {}
        self.all_games = []
        self.filtered_games = []
        self.entries = []

        self.selected_index = 0
        self.entry_height = 300
        self.spacing = 10

        self.scroll = 0
        self.scroll_speed = 400

    # ==================================================
    # DATA
    # ==================================================
    def load_manifest(self):
        path = join(BASE_DIR, 'code', 'Store', 'games_manifest.json')
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Store] Failed to load manifest: {e}")
            return {}

    def _load_online_data(self):
        self.manifest = self.load_manifest()
        self.all_games = list(self.manifest.keys())
        self.filtered_games = self.all_games.copy()
        self.selected_index = 0
        self.scroll = 0
        self.load_store_entries()

    def load_store_entries(self):
        self.entries.clear()

        if not self.online:
            return

        # Używamy base_w dla stabilnego layoutu zgodnie z poprzednim ustaleniem
        fixed_sidebar_w = self.launcher.sidebar.base_w
        y = 150

        for game_id in self.filtered_games:
            data = self.manifest[game_id]
            manifest_version = data.get("version")

            # --- POPRAWKA: Definiowanie statusu ---
            if not self.launcher.installer.is_installed(game_id):
                status = GameStatus.NOT_INSTALLED
            elif self.launcher.installer.has_update(game_id, manifest_version):
                status = GameStatus.UPDATE_AVAILABLE
            else:
                # Ważne: Musi być else, aby status zawsze istniał
                status = GameStatus.INSTALLED

            entry = StoreEntry(
                launcher=self.launcher,
                game_id=game_id,
                game_data=data,
                status=status, # Teraz status zawsze jest zdefiniowany
                size=(
                    WINDOW_WIDTH - fixed_sidebar_w - 100,
                    self.entry_height
                ),
                position=(
                    fixed_sidebar_w + 50,
                    y
                )
            )

            self.entries.append(entry)
            y += self.entry_height + self.spacing

    # ==================================================
    # INPUT
    # ==================================================
    def handling_events(self, events):
        keys = pygame.key.get_just_pressed()
        sm = self.launcher.state_manager # Skrót dla czytelności

        # ---------- OFFLINE MODE ----------
        if not self.online:
            if keys[self.launcher.controlls_data['options']] or keys[self.launcher.controlls_data['left']]:
                sm.ui_focus = "sidebar"
            return

        # ---------- SEARCHBAR LOGIC ----------
        if sm.ui_focus == "searchbar":
            # Searchbar potrzebuje surowych eventów (tekst), nie tylko keys
            exited = self.searchbar.handle_events(events) 
            if exited:
                sm.ui_focus = "content"
                self.searchbar.active = False
            return

        # ---------- CONTENT (GAMES) ----------
        if sm.ui_focus == "content":
            if keys[self.launcher.controlls_data['up']]:
                if self.selected_index == 0:
                    sm.ui_focus = "searchbar"
                    self.searchbar.active = True
                else:
                    self.selected_index = max(0, self.selected_index - 1)

            elif keys[self.launcher.controlls_data['down']]:
                if self.entries:
                    self.selected_index = min(len(self.entries) - 1, self.selected_index + 1)

            elif keys[self.launcher.controlls_data['left']]:
                sm.ui_focus = "sidebar"

            elif keys[pygame.K_RETURN] or keys[self.launcher.controlls_data['action_a']]:
                self.install_or_update_selected()

    # ==================================================
    # UPDATE
    # ==================================================
    def update(self, delta_time):
        super().update(delta_time)

        if not self.online or not self.entries:
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

        # ---------- OFFLINE SCREEN ----------
        if not self.online:
            font = pygame.font.SysFont(None, 48)
            text = font.render("OFFLINE", True, theme['colour_4'])
            rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            window.blit(text, rect)
            super().draw(window)
            return

        # ---------- STORE ENTRIES ----------
        for i, entry in enumerate(self.entries):
            selected = i == self.selected_index and self.ui_focus == "content"
            entry.icon.set_selected(selected)
            entry.rect.top = 150 + i * (self.entry_height + self.spacing) - self.scroll
            entry.draw(window)

        # ---------- SEARCHBAR ----------
        self.searchbar.draw(window, focused=self.ui_focus in ("searchbar", "topbar"))

        super().draw(window)

    # ==================================================
    # LOGIC
    # ==================================================
    def apply_search_filter(self, query):
        if not self.online:
            return

        query = query.lower()
        self.filtered_games = (
            [g for g in self.all_games if query in g.lower()]
            if query else self.all_games.copy()
        )
        self.selected_index = 0
        self.scroll = 0
        self.load_store_entries()

    def install_or_update_selected(self):
        if not self.entries:
            return

        entry = self.entries[self.selected_index]
        game_id = entry.game_id
        data = entry.game_data
        manifest_version = data.get("version")

        if entry.status == GameStatus.NOT_INSTALLED:
            self.launcher.installer.install(game_id, data["repo"], manifest_version)

        elif entry.status == GameStatus.UPDATE_AVAILABLE:
            self.launcher.installer.update(game_id, manifest_version)

        self.load_store_entries()

    # ==================================================
    # STATE LIFECYCLE
    # ==================================================
    def on_enter(self):
        self.online = self.launcher.checking_internet_connection()

        self.entries.clear()
        self.manifest.clear()
        self.all_games.clear()
        self.filtered_games.clear()
        self.scroll = 0
        self.selected_index = 0

        if self.online:
            self._load_online_data()
