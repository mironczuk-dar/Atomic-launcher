#IMPORTING LIBRARIES
import pygame
from os.path import join, exists
import shutil

#IMPORTING FILES
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY, GAMES_DIR

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
            color = theme['colour_3'] if selected else theme['colour_4']
            label = f">> {s.options[i]['label']}" if selected else s.options[i]['label']

            text = s.font.render(label, True, color)
            rect = text.get_rect(topright = (pos_x, pos_y + i * s.font_size*3/4))
            window.blit(text, rect)

    def handling_events(s):

        if not s.visible:
            return

        keys = pygame.key.get_just_pressed()
        controlls = s.launcher.controlls_data

        if keys[controlls['action_b']]:
            s.close_bottombar()

        if keys[controlls['up']]:
            s.index = max(0, s.index - 1)

        elif keys[controlls['down']]:
            s.index = min(len(s.options) - 1, s.index + 1)

        elif keys[controlls['action_a']] or keys[pygame.K_RETURN]:
            s.options[s.index]["callback"]()
            s.close_bottombar()

    def export_save_files(s):
        print("Feature coming soon: Favorites")

    def add_to_favorites(s):
        print("Feature coming soon: Favorites")

    def delete_save_files(s):
        pass

    def uninstall_game(s):
        game = s.library.filtered_games[s.library.selected_index]
        game_path = join(GAMES_DIR, game)

        try:
            if exists(game_path):
                shutil.rmtree(game_path)
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

    def close_bottombar(s):
        s.visible = not s.visible
        s.launcher.state_manager.ui_focus = 'content'