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

        #INTERNET
        s.online = launcher.checking_internet_connection()

        #SEARCHBAR
        s.searchbar = SearchBar(
            launcher,
            on_change = s.apply_search_filter
        )

        #DATA ATTRIBUES
        s.manifest = {}
        s.all_games = []
        s.filtered_games = []
        s.entries = []

        s.selected_index = 0
        s.entry_height = 300
        s.spacing = 10

        s.scroll = 0
        s.scroll_speed = 400

        #LOADING IN GAMES MANIFEST
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

            #CHECKING GAME STATUS: DOWNLOAD | UPDATE | INSATALLED
            if not s.launcher.installer.is_installed(game_id):
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

        #IF YOU'RE OFFLINE YOU CAN ONLY LEAVE THE STORE
        if not s.online:
            if keys[s.launcher.controlls_data['options']] or keys[s.launcher.controlls_data['left']]:
                state_manager.ui_focus = "sidebar"
            return

        #SEARCHBAR
        if state_manager.ui_focus == "searchbar":
            exited = s.searchbar.handle_events(events) 
            if exited:
                state_manager.ui_focus = "content"
                s.searchbar.active = False
            return

        #CONTENT NAVIGATION
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

            elif keys[pygame.K_RETURN] or keys[s.launcher.controlls_data['action_a']]:
                s.install_or_update_selected()

    def update(s, delta_time):
        super().update(delta_time)

        if not s.online or not s.entries:
            return

        target_y = s.entries[s.selected_index].rect.top

        if target_y < s.scroll + 150:
            s.scroll -= s.scroll_speed * delta_time
        elif target_y + s.entry_height > s.scroll + WINDOW_HEIGHT - 50:
            s.scroll += s.scroll_speed * delta_time

        s.scroll = max(0, s.scroll)

    def draw(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])

        #WHEN OFFLINE ONLY DRAW A MESSAGE ABOUT BEING OFFLINE
        if not s.online:
            font = pygame.font.SysFont(None, 48)
            text = font.render("OFFLINE", True, theme['colour_4'])
            rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            window.blit(text, rect)
            super().draw(window)
            return

        #DRAWING STORE ENTRIES
        for i, entry in enumerate(s.entries):
            selected = i == s.selected_index and s.launcher.state_manager.ui_focus == "content"
            entry.icon.set_selected(selected)
            entry.rect.top = 150 + i * (s.entry_height + s.spacing) - s.scroll
            entry.draw(window)

        #DRAWING SEARCHBAR
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

    def install_or_update_selected(s):
        if not s.entries:
            return

        entry = s.entries[s.selected_index]
        game_id = entry.game_id
        data = entry.game_data
        manifest_version = data.get("version")

        if entry.status == GameStatus.NOT_INSTALLED:
            s.launcher.installer.install(game_id, data["repo"], manifest_version)

        elif entry.status == GameStatus.UPDATE_AVAILABLE:
            s.launcher.installer.update(game_id, manifest_version)

        s.load_store_entries()

    def on_enter(s):
        s.online = s.launcher.checking_internet_connection()

        s.entries.clear()
        s.manifest.clear()
        s.all_games.clear()
        s.filtered_games.clear()
        s.scroll = 0
        s.selected_index = 0

        #LOADING IN MANIFEST AGAIN IN CASE OF AN UPDATE WHILE LAUNCHER IS ON
        s.manifest = load_data(s.manifest_path, {})

        if s.online:
            s._load_online_data()


    def _load_online_data(s):
        s.all_games = list(s.manifest.keys())
        s.filtered_games = s.all_games.copy()
        s.selected_index = 0
        s.scroll = 0
        s.load_store_entries()