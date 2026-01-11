#IMPORTING LIBRARIES
import pygame
import json
from os.path import join, exists

#IMPORTING FILES
from settings import BASE_DIR, GAMES_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from Store.game_installer import GameInstaller
from UI.store_entry import StoreEntry
from UI.searchbar import SearchBar
from States.generic_state import BaseState


class Store(BaseState):
    def __init__(self, launcher):
        super().__init__(launcher)

        # ---------- INTERNET ----------
        self.online = launcher.checking_internet_connection()
        self.reconnect_cooldown = 0.0

        # ---------- FILTERS ----------
        self.show_downloaded = True       # pokaż pobrane gry
        self.show_not_downloaded = True   # pokaż niepobrane gry

        # ---------- UI FOCUS ----------
        # content | sidebar | topbar | status
        self.ui_focus = "content"

        # ---------- SEARCHBAR ----------
        self.searchbar = SearchBar(
            launcher,
            on_change=self.apply_search_filter
        )

        # ---------- GAME DATA ----------
        self.manifest = self.load_manifest()
        self.installer = GameInstaller(GAMES_DIR)

        # list of game IDs (order in manifest)
        self.all_games = list(self.manifest.keys())
        self.filtered_games = self.all_games.copy()
        self.selected_index = 0

        # ---------- STORE ENTRIES ----------
        self.entry_height = 300
        self.spacing = 10
        self.entries = []

        self.load_store_entries()

        # ---------- SCROLL ----------
        self.scroll = 0
        self.scroll_speed = 400  # pixels per second

    # ==================================================
    # DATA LOADING
    # ==================================================
    def load_manifest(self):
        path = join(BASE_DIR, 'code', 'Store', 'games_manifest.json')
        with open(path, "r") as f:
            return json.load(f)

    def load_store_entries(self):
        self.entries.clear()
        y = 150  # start below topbar

        for game_id in self.filtered_games:
            data = self.manifest[game_id]

            # filter by downloaded / not downloaded
            installed = self.installer.is_installed(game_id)
            if (installed and not self.show_downloaded) or (not installed and not self.show_not_downloaded):
                continue

            entry = StoreEntry(
                launcher=self.launcher,
                game_id=game_id,
                game_data=data,
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

    # ------------------------------
    # Sidebar i topbar zawsze działają
    # ------------------------------
    # FIRST TIME ENTER SIDEBAR
        if self.ui_focus == "sidebar" and not getattr(self, "_sidebar_initialized", False):
            # ustaw highlight na aktywnym stanie
            current_state_name = None
            for name, state in self.launcher.state_manager.states.items():
                if state is self.launcher.state_manager.active_state:
                    current_state_name = name
                    break
            if current_state_name and current_state_name in self.sidebar.options:
                self.sidebar.index = self.sidebar.options.index(current_state_name)
            self._sidebar_initialized = True

        self.sidebar.handle_input(keys, self.ui_focus)

        # reset flagi jeśli wychodzimy z sidebaru
        if self.ui_focus != "sidebar":
            self._sidebar_initialized = False

        # przejście z sidebaru
        if self.ui_focus == "sidebar" and keys[pygame.K_RIGHT]:
            self.ui_focus = "content"

        # ------------------------------
        # Searchbar tylko jeśli online
        # ------------------------------
        if self.online:
            exited_search = self.searchbar.handle_events(events)
            if exited_search:
                self.ui_focus = "content"
                return
            if self.searchbar.active:
                return

        # ------------------------------
        # CONTENT focus
        # ------------------------------
        if self.ui_focus == "content":
            if not self.online:
                # Pozwól wyjść do sidebaru nawet offline!
                if keys[pygame.K_LEFT]:
                    self.ui_focus = "sidebar"
                if keys[pygame.K_RETURN]:
                    self.try_reconnect()
                # Nie robimy pełnego return, żeby reszta stanów (sidebar) mogła działać
            else:
                # ONLINE content logic
                if keys[pygame.K_UP]:
                    self.selected_index = max(0, self.selected_index - 1)
                elif keys[pygame.K_DOWN]:
                    self.selected_index = min(len(self.entries) - 1, self.selected_index + 1)
                elif keys[pygame.K_LEFT]:
                    self.ui_focus = "sidebar"
                elif keys[pygame.K_RETURN]:
                    self.launch_or_install_selected()


    # ==================================================
    # UPDATE
    # ==================================================
    def update(self, delta_time):
        super().update(delta_time)

        if not self.online:
            self.reconnect_cooldown = max(0, self.reconnect_cooldown - delta_time)
            return

        # scroll to selected entry
        if self.entries:
            target_y = self.entries[self.selected_index].rect.top
            if target_y < self.scroll + 150:
                self.scroll -= self.scroll_speed * delta_time
            elif target_y + self.entry_height > self.scroll + WINDOW_HEIGHT - 50:
                self.scroll += self.scroll_speed * delta_time

        self.scroll = max(0, self.scroll)
        self.reconnect_cooldown = max(0, self.reconnect_cooldown - delta_time)

    # ==================================================
    # DRAW
    # ==================================================
    def draw(self, window):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])

        if not self.online:
            # Rysuj tylko komunikat zamiast list gier
            offline_font = pygame.font.SysFont(None, 50, bold=True)
            text = offline_font.render("Currently offline", True, theme['colour_2'])
            window.blit(
                text,
                (WINDOW_WIDTH // 2 - text.get_width() // 2 + self.sidebar.base_w // 2,
                WINDOW_HEIGHT // 2 - 30)
            )

            hint_font = pygame.font.SysFont(None, 30)
            hint = hint_font.render("Press ENTER to retry or use Sidebar to go back", True, theme['colour_2'])
            window.blit(
                hint,
                (WINDOW_WIDTH // 2 - hint.get_width() // 2 + self.sidebar.base_w // 2,
                WINDOW_HEIGHT // 2 + 30)
            )
        else:
            # Rysuj wpisy sklepu tylko gdy online
            for i, entry in enumerate(self.entries):
                selected = i == self.selected_index and self.ui_focus == "content"
                entry.icon.set_selected(selected)
                entry.rect.top = 150 + i * (self.entry_height + self.spacing) - self.scroll
                entry.draw(window)

            # searchbar tylko gdy online
            self.searchbar.draw(window, focused=self.ui_focus == "topbar")

        # Sidebar rysuje się ZAWSZE na samym końcu (nad resztą treści)
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

    def try_reconnect(self):
        if self.reconnect_cooldown > 0:
            return
        self.online = self.launcher.checking_internet_connection()
        self.reconnect_cooldown = 2.0

    def launch_or_install_selected(self):
        if not self.entries:
            return
        entry = self.entries[self.selected_index]
        game_id = entry.game_id
        data = entry.game_data

        if not self.installer.is_installed(game_id):
            self.installer.install(game_id, data["repo"])
            self.load_store_entries()  # reload after install
        else:
            self.installer.update(game_id)

    def on_enter(self):
        """Odświeża stan połączenia i wpisy przy każdym wejściu do sklepu."""
        self.online = self.launcher.checking_internet_connection()
        self.manifest = self.load_manifest()
        self.all_games = list(self.manifest.keys())
        self.load_store_entries()
