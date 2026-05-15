# IMPORTING LIBRARIES
import pygame
import os
import subprocess
import sys

# IMPORTING FILES
from States.generic_state import BaseState
from settings import GAMES_DIR, BASE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.searchbar import SearchBar
from UI.game_icon import GameIcon
from UI.library_ui.bottombar import BottomBar
from UI.buttons import GenericToggleButton
from UI.library_ui.navigation_tutorial import NavigationTutorial

# IMPORTING TOOLS
from Tools.data_loading_tools import load_data


class Library(BaseState):
    def __init__(s, launcher):
        super().__init__(launcher)

        # LOADING IN GAMES MANIFEST
        s.manifest_path = os.path.join(BASE_DIR, 'code', 'Store', 'games_manifest.json')
        s.manifest = load_data(s.manifest_path, {})

        # LOGIC ATTRIBUTES
        s.game_library = []
        s.game_icons = {}
        s.filtered_games = []
        s.selected_index = 0
        s.show_favorites_only = False
        s.topbar_focus = False 
        s.topbar_index = 0  # 0 = Searchbar, 1 = Favorites Button
        s.navigation_tutorial = NavigationTutorial(launcher)

        # LIBRARY UI ELEMENTS
        # SearchBar handles its own internal Keyboard instance
        s.searchbar = SearchBar(
            launcher,
            on_change=s.apply_search_filter,
            width=int(WINDOW_WIDTH * 0.4),
            height=int(WINDOW_HEIGHT * 0.1),
            y=int(WINDOW_HEIGHT * 0.03),
            x=int(WINDOW_WIDTH * 0.5) - int((WINDOW_WIDTH * 0.4) // 2)
        )

        # FAVORITES TOGGLE BUTTON
        btn_w = int(WINDOW_WIDTH * 0.10)
        # Positioned to the right of the searchbar
        btn_x = s.searchbar.custom_x + s.searchbar.w + 200
        btn_y = s.searchbar.custom_y + s.searchbar.h // 2

        s.fav_toggle = GenericToggleButton(
            launcher,
            size=(btn_w, s.searchbar.h/2),
            pos=(btn_x, btn_y),
            text="Favorites",
            text_size=30,
            active_colour=(0,255,0),  # Fallback colors (not used when theme is enabled)
            inactive_colour=(255,0,0),
            action=s.toggle_favorites_filter
        )
        s.fav_toggle.set_theme_colours(use_theme=True)

        s.bottombar = BottomBar(launcher, s)
        s.icon_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.05), bold=False)

        # LAYOUT ATTRIBUTES
        s.icon_w = int(WINDOW_WIDTH * 0.2)
        s.spacing = 60
        s.scroll_speed = 8
        s.current_scroll = 0
        s.icon_group = pygame.sprite.Group()

    def toggle_favorites_filter(s):
        """Callback for the fav_toggle button."""
        s.show_favorites_only = s.fav_toggle.is_on
        s.apply_search_filter(s.searchbar.text)

    def handling_events(s, events):
        controlls = s.launcher.controlls_data
        
        # --- NEW EVENT-BASED LOGIC ---
        for event in events:
            if event.type == pygame.KEYDOWN:
                key = event.key

                if s.navigation_tutorial.is_active():
                    if s.navigation_tutorial.handle_input(events):
                        return

                if s.searchbar.active:
                    s.searchbar.handle_events(events)
                    return

                if s.bottombar.visible:
                    s.bottombar.handling_events(events)
                    return

                if s.launcher.state_manager.ui_focus != 'content':
                    return

                # 3. TOPBAR NAVIGATION
                if s.topbar_focus:
                    s.fav_toggle.is_selected = (s.topbar_index == 1)

                    if key == controlls['keyboard']['down']:
                        s.topbar_focus = False
                        s.fav_toggle.is_selected = False
                    
                    elif key == controlls['keyboard']['left'] or key == controlls['keyboard']['right']:
                        s.topbar_index = 1 - s.topbar_index
                        
                    if key == pygame.K_RETURN or key == controlls['keyboard']['action_a']:
                        if s.topbar_index == 0:
                            s.searchbar.open_keyboard()
                        else:
                            s.fav_toggle.toggle()
                    return

                # 4. CONTENT NAVIGATION
                if key == controlls['keyboard']['action_b'] and len(s.game_library) != 0:
                    s.bottombar.open_bottombar()
                    return

                if key == controlls['keyboard']['left']:
                    if s.selected_index == 0:
                        s.launcher.state_manager.ui_focus = "sidebar"
                    else:
                        s.selected_index -= 1
                elif key == controlls['keyboard']['right']:
                    s.selected_index = min(len(s.filtered_games) - 1, s.selected_index + 1)
                elif key == pygame.K_RETURN or key == controlls['keyboard']['action_a']:
                    s.launch_game()
                elif key == controlls['keyboard']['up']:
                    s.topbar_focus = True

    def update(s, delta_time):
        super().update(delta_time)
        s.current_scroll += (s.selected_index - s.current_scroll) * s.scroll_speed * delta_time
        s.fav_toggle.update(delta_time)
        s.navigation_tutorial.update(delta_time)

    def draw(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])

        s.draw_game_icons_titles(window)
        s.bottombar.draw(window)
        
        # Draw Searchbar (focused if topbar_index is 0)
        search_focused = (s.topbar_focus and s.topbar_index == 0)
        s.searchbar.draw(window, focused=search_focused)

        # Draw the Favorites Toggle Button
        s.fav_toggle.draw(window)

        s.navigation_tutorial.draw(window)

        super().draw(window)

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
        favorites = s.launcher.game_library_data.get('favorites', [])

        for i, folder_name in enumerate(s.filtered_games):
            icon = s.game_icons.get(folder_name)
            if not icon: continue

            offset = (i - s.current_scroll) * (s.icon_w + s.spacing)
            x = workspace_center_x + offset
            y = center_y

            icon.set_position(x, y)
            icon.set_selected(i == s.selected_index)
            icon.draw(window)

            if folder_name in favorites:
                heart = s.icon_font.render("<3", True, (255, 60, 60)) 
                heart_rect = heart.get_rect(topright=(x + s.icon_w // 2 - 10, y - s.icon_w // 2 + 10))
                pygame.draw.rect(window, (30, 30, 30), heart_rect.inflate(4, 4), border_radius=4)
                window.blit(heart, heart_rect)

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


    def get_game_library(s):
        s.manifest = load_data(s.manifest_path, {})
        if not os.path.exists(GAMES_DIR):
            os.makedirs(GAMES_DIR)
            s.game_library = []
        else:
            s.game_library = [
                name for name in os.listdir(GAMES_DIR)
                if os.path.isdir(os.path.join(GAMES_DIR, name))
            ]

        for game in s.game_library:
            s.game_icons[game] = GameIcon(
                launcher=s.launcher,
                groups=s.icon_group,
                game_id=game,
                size=s.icon_w,
                path=os.path.join(BASE_DIR, 'assets', 'store_assets', game, 'icon')
            )
        s.apply_search_filter(s.searchbar.text)

    def apply_search_filter(s, query):
        query = query.lower()
        s.filtered_games = []
        favorites = s.launcher.game_library_data.get('favorites', [])
        
        for game_name in s.game_library:
            if s.show_favorites_only and game_name not in favorites:
                continue
                
            display_name = s.get_game_display_name(game_name)
            if not query or query in display_name.lower():
                s.filtered_games.append(game_name)
        s.selected_index = 0

    def on_enter(self):
        self.get_game_library()

    def launch_game(self):
        if not self.filtered_games: return
        folder_name = self.filtered_games[self.selected_index]
        game_path = os.path.join(GAMES_DIR, folder_name, 'code')
        game_data = self.manifest.get(folder_name, {})
        main_file = game_data.get("main.py", "main.py") 
        full_path = os.path.join(game_path, main_file)

        if not os.path.exists(full_path): return

        try:
            self.launcher.game_process = subprocess.Popen(
                [sys.executable, full_path],
                cwd=game_path,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
            )            
            self.launcher.game_running = True 
            
        except Exception as e:
            print(f"Failed to start: {e}")
            return

        perf_data = self.launcher.performance_settings_data
        if perf_data.get('turn_off_launcher_when_game_active'):
            pygame.quit()
            sys.exit()