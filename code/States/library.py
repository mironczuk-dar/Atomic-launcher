#IMPORTING LIBRARIES
import pygame
import os
import subprocess
import sys
import json
import shutil

#IMPORTING FILES
from States.generic_state import BaseState
from settings import GAMES_DIR, BASE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.searchbar import SearchBar
from UI.game_icon import GameIcon
from UI.library_ui.bottombar import BottomBar

#IMPORTING TOOLS
from Tools.data_loading_tools import load_data


class Library(BaseState):
    def __init__(s, launcher):
        super().__init__(launcher)

        #LOADING IN GAMES MANIFEST
        s.manifest_path = os.path.join(BASE_DIR, 'code', 'Store', 'games_manifest.json')
        s.manifest = load_data(s.manifest_path, {})

        #LOGIC ATTRIBUTES FOR GAMES SHOWN
        s.game_library = []
        s.game_icons = {}
        s.filtered_games = []
        s.selected_index = 0

        #LIBRARY UI ELEMENTS
        s.searchbar = SearchBar(
            launcher,
            on_change = s.apply_search_filter
        )
        s.bottombar = BottomBar(launcher, s)

        #FONTS
        s.icon_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.05), bold = False)

        #LAYOUT ATTRIBUTES
        s.topbar_h = int(WINDOW_HEIGHT * 0.1)
        s.icon_w = int(WINDOW_WIDTH * 0.2)
        s.spacing = 60
        s.scroll_speed = 8
        s.current_scroll = 0

        #ICON GROUPS
        s.icon_group = pygame.sprite.Group()

    #METHOD FOR HANDLING INPUT
    def handling_events(s, events):
        controlls = s.launcher.controlls_data
        keys = pygame.key.get_just_pressed()

        #BOTTOMBAR NAVIGATION
        if s.bottombar.visible:
            s.bottombar.handling_events()
            return
        
        if keys[controlls['action_b']]:
            s.bottombar.open_bottombar()
            return
        

        if s.launcher.state_manager.ui_focus != 'content':
            return
        

        #GETTING ALL KEYS PRESSED BY PLAYER
        keys = pygame.key.get_just_pressed()

        #INPUT FOR THE SEARCHBAR
        if s.searchbar.active:
            if s.searchbar.handle_events(events):
                s.searchbar.active = False
            return


        #CONTENT NAVIGATION
        if keys[s.launcher.controlls_data['left']]:
            if s.selected_index == 0:
                s.launcher.state_manager.ui_focus = "sidebar"
            else:
                s.selected_index -= 1

        elif keys[controlls['right']]:
            s.selected_index = min(len(s.filtered_games) - 1, s.selected_index + 1)
        
        elif keys[pygame.K_RETURN] or keys[controlls['action_a']]:
            s.launch_game()
        
        elif keys[controlls['up']]:
            s.searchbar.active = True

    #METHOD FOR UPDATING THE LIBRARY
    def update(s, delta_time):
        super().update(delta_time)
        s.current_scroll += (s.selected_index - s.current_scroll) * s.scroll_speed * delta_time

    #METHOD FOR DRAWING THE CLASS
    def draw(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])

        s.draw_game_icons_titles(window)

        s.bottombar.draw(window)
        s.searchbar.draw(window, focused=s.searchbar.active)

        super().draw(window)

    #METHOD FOR DRAWING GAMES ICON TITLES
    def draw_game_icons_titles(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]

        if not s.filtered_games:
            msg = s.icon_font.render("NO GAMES INSTALLED", True, theme['colour_2'])
            rect = msg.get_rect(center=((WINDOW_WIDTH + s.launcher.sidebar.base_w) // 2, WINDOW_HEIGHT // 2))
            window.blit(msg, rect)
            return

        sidebar_w = s.launcher.sidebar.base_w
        workspace_center_x = sidebar_w + (WINDOW_WIDTH - sidebar_w) // 2
        center_y = WINDOW_HEIGHT // 2

        for i, folder_name in enumerate(s.filtered_games):
            icon = s.game_icons.get(folder_name)
            if not icon: continue

            offset = (i - s.current_scroll) * (s.icon_w + s.spacing)
            x = workspace_center_x + offset
            y = center_y

            icon.set_position(x, y)
            icon.set_selected(i == s.selected_index)
            icon.draw(window)

            if i == s.selected_index:
                display_name = s.get_game_display_name(folder_name)
                text = s.icon_font.render(display_name.upper(), True, theme['colour_3'])
                text_rect = text.get_rect(center=(x, y - s.icon_w // 2 - 60))
                window.blit(text, text_rect)

    def get_game_display_name(self, folder_name):
        game_data = self.manifest.get(folder_name)
        if game_data and "name" in game_data:
            return game_data["name"]
        return folder_name.replace("_", " ").title()

    #METHOD FOR GETTING GAMES LIBRARY DATA
    def get_game_library(s):
        s.manifest = load_data(s.manifest_path, {})
        
        #CREATING A GAMES FOLDER IF FILES CORUPTED
        if not os.path.exists(GAMES_DIR):
            os.makedirs(GAMES_DIR)
            s.game_library = []

        #PLAYERS GAME LIBRARY
        else:
            s.game_library = [
                name for name in os.listdir(GAMES_DIR)
                if os.path.isdir(os.path.join(GAMES_DIR, name))
            ]

        #GETTING THE GAME ICONS
        for game in s.game_library:
            s.game_icons[game] = GameIcon(
                launcher = s.launcher,
                groups = s.icon_group,
                game_id = game,
                size = s.icon_w,
                path = os.path.join(GAMES_DIR, game, 'assets', 'icon')
            )
            print(os.path.join(GAMES_DIR, game, 'icon'))

        s.apply_search_filter(s.searchbar.text)

    def apply_search_filter(s, query):
        query = query.lower()
        
        s.filtered_games = []
        for game_name in s.game_library:
            display_name = s.get_game_display_name(game_name)
            if not query or query in display_name.lower():
                s.filtered_games.append(game_name)
        
        s.selected_index = 0

    def on_enter(self):
        self.get_game_library()

    def launch_game(self):
        """Uruchamia wybraną grę w nowym procesie."""
        if not self.filtered_games:
            return

        folder_name = self.filtered_games[self.selected_index]
        game_path = os.path.join(GAMES_DIR, folder_name, 'code')
        
        game_data = self.manifest.get(folder_name, {})
        main_file = game_data.get("mian.py", "main.py")
        
        full_path = os.path.join(game_path, main_file)

        if os.path.exists(full_path):
            try:
                print(f"Launching {folder_name} via {full_path}...")

                subprocess.Popen(
                    [sys.executable, full_path],
                    cwd=game_path,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                )
                
            except Exception as e:
                print(f"Error launching game: {e}")
        else:
            print(f"Error: Could not find startup file at {full_path}")