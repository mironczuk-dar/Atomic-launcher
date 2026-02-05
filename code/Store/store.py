import pygame
import json
from os.path import join

from settings import BASE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.store_ui.store_entry import StoreEntry, GameStatus
from UI.searchbar import SearchBar
from States.generic_state import BaseState
from Tools.data_loading_tools import load_data


class Store(BaseState):
    def __init__(s, launcher):
        super().__init__(launcher)

        # INTERNET
        s.online = launcher.checking_internet_connection()

        # SEARCHBAR
        s.searchbar = SearchBar(
            launcher,
            on_change = s.apply_search_filter
        )

        # DATA ATTRIBUTES
        s.manifest = {}
        s.all_games = []
        s.filtered_games = []
        s.entries = []

        s.selected_index = 0
        s.entry_height = 300
        s.spacing = 10

        s.scroll = 0
        s.scroll_speed = 400

        # LOADING IN GAMES MANIFEST
        s.manifest_path = join(BASE_DIR, 'code', 'Store', 'games_manifest.json')
        s.manifest = load_data(s.manifest_path, {})

    def load_store_entries(s):
        s.entries.clear()

        if not s.online:
            return

        fixed_sidebar_w = s.launcher.sidebar.base_w
        y = 150

        for game_id in s.filtered_games:
            data = s.manifest[game_id]
            manifest_version = data.get('version')

            # --- NOWA LOGIKA STATUSÓW (Z UWZGLĘDNIENIEM POBIERANIA) ---
            if s.launcher.installer.is_downloading and s.launcher.installer.current_game_id == game_id:
                status = GameStatus.DOWNLOADING
            elif not s.launcher.installer.is_installed(game_id):
                status = GameStatus.NOT_INSTALLED
            elif s.launcher.installer.has_update(game_id, manifest_version):
                status = GameStatus.UPDATE_AVAILABLE
            else:
                status = GameStatus.INSTALLED

            entry = StoreEntry(
                launcher = s.launcher,
                game_id = game_id,
                game_data = data,
                status = status,
                size=(
                    WINDOW_WIDTH - fixed_sidebar_w - 100,
                    s.entry_height
                ),
                position=(
                    fixed_sidebar_w + 50,
                    y
                )
            )

            s.entries.append(entry)
            y += s.entry_height + s.spacing

    def handling_events(s, events):
        keys = pygame.key.get_just_pressed()
        state_manager = s.launcher.state_manager
        controlls = s.launcher.controlls_data

        if not s.online:
            if keys[controlls['options']] or keys[controlls['left']]:
                state_manager.ui_focus = "sidebar"
            return

        if state_manager.ui_focus == "searchbar":
            exited = s.searchbar.handle_events(events) 
            if exited:
                state_manager.ui_focus = "content"
                s.searchbar.active = False
            return

        if state_manager.ui_focus == "content":
            if keys[s.launcher.controlls_data['up']]: 
                if s.selected_index == 0:
                    state_manager.ui_focus = "searchbar"
                    s.searchbar.active = True
                else:
                    s.selected_index = max(0, s.selected_index - 1)

            elif keys[s.launcher.controlls_data['down']]:
                if s.entries:
                    s.selected_index = min(len(s.entries) - 1, s.selected_index + 1)

            elif keys[s.launcher.controlls_data['left']]:
                state_manager.ui_focus = "sidebar"

            elif keys[pygame.K_RETURN] or keys[controlls['action_a']]:
                # Blokujemy wejście w podgląd, jeśli ta konkretna gra się pobiera (opcjonalnie)
                s.enter_game_preview()

    def update(s, delta_time):
        super().update(delta_time)

        if not s.online or not s.entries:
            return

        # --- AUTO-REFRESH STATUSÓW ---
        # Jeśli instalator skończył pracę, a na liście nadal wisi status DOWNLOADING, odświeżamy listę.
        # To pozwala na płynne przejście z "Downloading" do "Installed" bez wychodzenia ze sklepu.
        is_any_entry_downloading = any(e.status == GameStatus.DOWNLOADING for e in s.entries)
        if is_any_entry_downloading and not s.launcher.installer.is_downloading:
            s.load_store_entries()

        # Logika scrollowania
        current_entry_y = 150 + s.selected_index * (s.entry_height + s.spacing)
        padding_top = 160
        padding_bottom = 50 

        if current_entry_y + s.entry_height > s.scroll + WINDOW_HEIGHT - padding_bottom:
            s.scroll = current_entry_y + s.entry_height - WINDOW_HEIGHT + padding_bottom
        if current_entry_y < s.scroll + padding_top:
            s.scroll = current_entry_y - padding_top

        s.scroll = max(0, s.scroll)

    def draw(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])

        if not s.online:
            font = pygame.font.SysFont(None, 48)
            text = font.render("OFFLINE", True, theme['colour_4'])
            rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            window.blit(text, rect)
            super().draw(window)
            return

        # DRAWING STORE ENTRIES
        for i, entry in enumerate(s.entries):
            selected = i == s.selected_index and s.launcher.state_manager.ui_focus == "content"
            entry.icon.set_selected(selected)
            entry.rect.top = 180 + i * (s.entry_height + s.spacing) - s.scroll
            entry.draw(window)

        # DRAWING SEARCHBAR
        s.searchbar.draw(window, focused=s.launcher.state_manager.ui_focus in ("searchbar", "topbar"))

        super().draw(window)

    def apply_search_filter(s, query):
        if not s.online:
            return
        query = query.lower()
        s.filtered_games = (
            [g for g in s.all_games if query in g.lower()]
            if query else s.all_games.copy()
        )
        s.selected_index = 0
        s.scroll = 0
        s.load_store_entries()

    def enter_game_preview(s):
        if not s.entries:
            return
        entry = s.entries[s.selected_index]
        preview_state = s.launcher.state_manager.states.get('Game preview')
        if preview_state:
            preview_state.setup(entry.game_id, entry.game_data)
            s.launcher.state_manager.set_state('Game preview')

    def on_enter(s):
        s.online = s.launcher.checking_internet_connection()
        s.manifest = load_data(s.manifest_path, {})
        if s.online:
            s._load_online_data()

    def _load_online_data(s):
        s.all_games = list(s.manifest.keys())
        s.filtered_games = s.all_games.copy()
        # Zdejmujemy resetowanie indexu/scrolla przy każdym on_enter, 
        # żeby powrót z GamePreview nie przewijał listy na samą górę.
        s.load_store_entries()