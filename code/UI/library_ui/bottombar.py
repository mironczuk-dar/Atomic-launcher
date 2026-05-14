#IMPORTING LIBRARIES
import pygame
from os.path import join, exists
import shutil
import os
import stat

#IMPORTING FILES
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY, GAMES_DIR, GAME_LIBRARY_DATA_PATH, get_contrast_text_color

#IMPORTING TOOLS
from Tools.data_loading_tools import save_data

def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

#BOTTOM BAR WITH EXTRA OPTIONS IN THE LIBRARY
class BottomBar:

    def __init__(s, launcher, library):
        s.launcher = launcher
        s.library = library

        s.visible = False
        s.index = 0

        #APPERENCE
        s.bar_height = WINDOW_HEIGHT * 0.25 
        s.sidebar_w = int(WINDOW_WIDTH * 0.1)
        s.bar_width = WINDOW_WIDTH - s.sidebar_w
        s.font_size = int(WINDOW_WIDTH * 0.04)
        s.font = pygame.font.SysFont(None, s.font_size, bold = False)

        #BUTTONS
        s.options = {
            0 : {'label' : 'Add to favorites',
                 'callback' : s.add_to_favorites},
            1 : {'label' : 'Export save files',
                 'callback' : s.export_save_files},
            2 : {'label' : 'Delete save files',
                 'callback' : s.delete_save_files},
            3 : {'label' : 'Uninstall',
                 'callback' : s.uninstall_game},
        }

    def update(s, delta_time):
        pass

    def draw(s, window):
        if not s.visible:
            return
        
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        
        pygame.draw.rect(
            window,
            theme['colour_2'],
            (
                s.sidebar_w,
                WINDOW_HEIGHT - s.bar_height,
                WINDOW_WIDTH - s.sidebar_w,
                s.bar_height
            )
        )

        pos_x = WINDOW_WIDTH * 0.98
        pos_y = WINDOW_HEIGHT - s.bar_height + 20

        for i, option in enumerate(s.options):
            selected = i == s.index
            bg = theme['colour_2'] if selected else theme['colour_4']
            color = get_contrast_text_color(bg)
            label = f">> {s.options[i]['label']}" if selected else s.options[i]['label']

            text = s.font.render(label, True, color)
            rect = text.get_rect(topright = (pos_x, pos_y + i * s.font_size*3/4))
            window.blit(text, rect)

    def handling_events(s):

        if not s.visible:
            return

        keys = pygame.key.get_just_pressed()
        controlls = s.launcher.controlls_data

        if keys[controlls['keyboard']['action_b']]:
            s.close_bottombar()

        if keys[controlls['keyboard']['up']]:
            s.index = max(0, s.index - 1)

        elif keys[controlls['keyboard']['down']]:
            s.index = min(len(s.options) - 1, s.index + 1)

        elif keys[controlls['keyboard']['action_a']] or keys[pygame.K_RETURN]:
            s.options[s.index]["callback"]()
            s.close_bottombar()

    def export_save_files(s):
        print("Feature coming soon: Favorites")

    def add_to_favorites(s):
        # Get the currently selected game folder name
        game = s.library.filtered_games[s.library.selected_index]
        favorites = s.launcher.game_library_data['favorites']

        # Toggle favorite status
        if game in favorites:
            favorites.remove(game)
            s.options[0]['label'] = 'Add to favorites' # Update label for next time
            print(f"Removed {game} from favorites")
        else:
            favorites.append(game)
            s.options[0]['label'] = 'Remove from favorites'
            print(f"Added {game} to favorites")

        # Save to disk
        save_data(s.launcher.game_library_data, GAME_LIBRARY_DATA_PATH)

        # Refresh the library view in case the favorites filter is currently active
        s.library.apply_search_filter(s.library.searchbar.text)

    def delete_save_files(s):
        pass

    def uninstall_game(s):
        game = s.library.filtered_games[s.library.selected_index]
        game_path = join(GAMES_DIR, game)

        try:
            if exists(game_path):
                shutil.rmtree(game_path, onerror=remove_readonly)
                print(f"Uninstalled: {game}")
                s.library.get_game_library()
                s.visible = False
                s.library.selected_index = max(0, s.library.selected_index - 1)
        
        except Exception as e:
            print(f"Uninstall failed: {e}")

        s.close_bottombar()

    def open_bottombar(s):
        s.visible = not s.visible
        s.index = 0
        s.launcher.state_manager.ui_focus = 'bottombar'
        
        # --- NEW CODE: Dynamic Label ---
        if s.library.filtered_games:
            current_game = s.library.filtered_games[s.library.selected_index]
            favorites = s.launcher.game_library_data.get('favorites', [])
            
            if current_game in favorites:
                s.options[0]['label'] = 'Remove from favorites'
            else:
                s.options[0]['label'] = 'Add to favorites'

    def close_bottombar(s):
        s.visible = not s.visible
        s.launcher.state_manager.ui_focus = 'content'