#IMPORTING LIBRARIES
import pygame
import os

#IMPORTING FILES
from States.generic_state import BaseState
from settings import BASE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY

#POINTING TO THE GAMES FOLDER
GAMES_DIR = os.path.join(BASE_DIR, 'games')

#MAIN LIBRARY WHERE ALL THE PLAYERS GAMES ARE
class Library(BaseState):
    def __init__(s, launcher):
        super().__init__(launcher)
        s.games_list = [name for name in os.listdir(GAMES_DIR) if os.path.isdir(os.path.join(GAMES_DIR, name))]
        s.selected_index = 0
        s.icons = {}
        s.load_game_assets()

        #ICON ATTRIBUTES
        s.icon_w = int(WINDOW_WIDTH * 0.2)
        s.icon_size = (s.icon_w, s.icon_w)
        s.spacing = 40
        s.scroll_speed = 2

        #ICON TEXT ATTRIBUTES
        s.font_size = int(WINDOW_WIDTH * 0.06)
        s.font = pygame.font.SysFont(None, s.font_size, bold=True)
        
        #SCROLLING THROUGH ICONS
        s.current_scroll = 0

    def load_game_assets(s):
        icon_size = (WINDOW_WIDTH*0.2, WINDOW_WIDTH*0.2)
        default_surface = pygame.Surface(icon_size)
        default_surface.fill(THEME_LIBRARY[s.launcher.theme_data['current_theme']]['colour_2'])

        for game in s.games_list:
            icon_path = os.path.join(GAMES_DIR, game, 'icon.png')
            
            if os.path.exists(icon_path):
                img = pygame.image.load(icon_path).convert_alpha()
                s.icons[game] = pygame.transform.scale(img, icon_size)
            else:
                s.icons[game] = default_surface

    def handling_events(s):
        if not s.games_list:
            return 

        keys_j = pygame.key.get_just_pressed()

        if keys_j[pygame.K_RIGHT] or keys_j[pygame.K_d]:
            s.selected_index = (s.selected_index + 1) % len(s.games_list)
        elif keys_j[pygame.K_LEFT] or keys_j[pygame.K_a]:
            s.selected_index = (s.selected_index - 1) % len(s.games_list)
        
        if keys_j[pygame.K_RETURN]:
            s.launcher.launch_game()

    def update(s, delta_time):
        target_scroll = s.selected_index
        s.current_scroll += (target_scroll - s.current_scroll) * s.scroll_speed * delta_time

    def draw(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])
        
        display_w, display_h = window.get_size()
        center_x = display_w // 2
        center_y = display_h // 2
        
        for i, game in enumerate(s.games_list):
            offset = (i - s.current_scroll) * (s.icon_w + s.spacing)
            x_pos = center_x - (s.icon_w // 2) + offset
            y_pos = center_y - (s.icon_w // 2)

            #DRAWING BORDER
            if i == s.selected_index:
                border_size = 8
                rect_bg = (x_pos - border_size, y_pos - border_size, 
                           s.icon_w + border_size*2, s.icon_w + border_size*2)
                pygame.draw.rect(window, theme['colour_3'], rect_bg, border_radius=10)
            
            #DRAWING THE ICON
            window.blit(s.icons[game], (x_pos, y_pos))
            
            #DRAWING TEXT
            if i == s.selected_index:
                #GETTING RID OF UNDERSCORES
                display_name = game.replace('_', ' ').upper()
                
                #RENDERING TEXT
                text_surf = s.font.render(display_name, True, theme['colour_3'])
                
                #SETTING TEXT POSITION
                text_x = x_pos + (s.icon_w // 2) - (text_surf.get_width() // 2)
                text_y = y_pos - 50 
                
                # Opcjonalnie: Cień pod tekstem dla lepszej widoczności
                shadow_surf = s.font.render(display_name, True, (20, 20, 20))
                window.blit(shadow_surf, (text_x + 2, text_y + 2)) # Przesunięcie o 2px
                
                # Właściwy tekst
                window.blit(text_surf, (text_x, text_y))