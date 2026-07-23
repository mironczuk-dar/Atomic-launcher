"""Performance options tab.

This tab exposes launcher performance settings such as the background FPS
and whether the launcher should shut down when a game starts.
"""

import pygame

from settings import get_contrast_text_color
from Tools.data_loading_tools import save_data
from settings import PERFORMANCE_SETTINGS_DATA_PATH, THEME_LIBRARY, WINDOW_WIDTH
from UI.options_ui.generic_options_tab import GenericOptionsTab


class PerformanceOptionsTab(GenericOptionsTab):
    """Options tab for launcher performance tuning."""

    def __init__(s, launcher):
        super().__init__(launcher)
        s.update_visuals()
        
        s.initial_pos = (WINDOW_WIDTH * 0.15, 250)
        s.col_width = 350
        s.fps_button_height = 80
        s.shutdown_button_size = (400, 200)
        s.spacing = 15
        
        s.font = pygame.font.SysFont(None, 45, False)
        s.header_font = pygame.font.SysFont(None, 55, True)

        # FPS options available for launcher background mode
        s.fps_levels = [60, 40, 30, 20, 15, 10, 5]
        
        # Navigation state between the FPS options column and the shutdown toggle
        s.active_col = 'fps'  # 'fps' or 'shutdown'
        s.fps_index = 0

    def update_visuals(s):
        s.current_theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]

    def handling_events(s, events, ctrl):
        if s.launcher.state_manager.ui_focus != 'content':
            return

        input_manager = getattr(s.launcher, 'input_manager', None)
        if input_manager is None:
            return

        if input_manager.just_pressed('left') or input_manager.just_pressed('right'):
            s.active_col = 'shutdown' if s.active_col == 'fps' else 'fps'

        if s.active_col == 'fps':
            if input_manager.just_pressed('up'):
                s.fps_index = (s.fps_index - 1) % len(s.fps_levels)
            elif input_manager.just_pressed('down'):
                s.fps_index = (s.fps_index + 1) % len(s.fps_levels)

        if input_manager.just_pressed('action_a'):
            if s.active_col == 'fps':
                s.launcher.performance_settings_data['decrease_launcher_fps_when_game_active'] = s.fps_levels[s.fps_index]
            else:
                current_val = s.launcher.performance_settings_data['turn_off_launcher_when_game_active']
                s.launcher.performance_settings_data['turn_off_launcher_when_game_active'] = not current_val
            save_data(s.launcher.performance_settings_data, PERFORMANCE_SETTINGS_DATA_PATH)

    def draw(s, window):
        has_focus = (s.launcher.state_manager.ui_focus == 'content')
        
        s.draw_fps_column(window, has_focus)
        s.draw_shutdown_column(window, has_focus)

    def draw_fps_column(s, window, has_focus):
        # Nagłówek
        header = s.header_font.render("Background FPS", True, s.current_theme['colour_2'])
        window.blit(header, (s.initial_pos[0], s.initial_pos[1] - 60))

        current_saved_fps = s.launcher.performance_settings_data['decrease_launcher_fps_when_game_active']

        for i, fps in enumerate(s.fps_levels):
            is_selected = (s.active_col == 'fps' and i == s.fps_index and has_focus)
            is_active = (fps == current_saved_fps)

            bg_col = s.current_theme['colour_2'] if is_selected else s.current_theme['colour_4']
            text_col = get_contrast_text_color(bg_col)

            rect = pygame.Rect(
                s.initial_pos[0], 
                s.initial_pos[1] + i * (s.fps_button_height + s.spacing),
                s.col_width, 
                s.fps_button_height
            )

            pygame.draw.rect(window, bg_col, rect, border_radius=5)
            
            # Ramka dla aktualnie wybranej wartości w danych
            if is_active:
                pygame.draw.rect(window, (0, 255, 0), rect, 3, border_radius=5)

            # 🔹 FOCUS INDICATOR = AKTUALNIE ZAZNACZONY ELEMENT
            if is_selected:
                pygame.draw.rect(window, (255, 200, 0), rect, 4, border_radius=5)

            text_surf = s.font.render(f"{fps} FPS", True, text_col)
            text_rect = text_surf.get_rect(center=rect.center)
            window.blit(text_surf, text_rect)

    def draw_shutdown_column(s, window, has_focus):
        # Pozycja prawej kolumny
        x_pos = s.initial_pos[0] + s.col_width + 100
        
        # Nagłówek
        header = s.header_font.render("Launcher Behavior", True, s.current_theme['colour_2'])
        window.blit(header, (x_pos, s.initial_pos[1] - 60))

        is_selected = (s.active_col == 'shutdown' and has_focus)
        is_on = s.launcher.performance_settings_data['turn_off_launcher_when_game_active']

        bg_col = s.current_theme['colour_2'] if is_selected else s.current_theme['colour_4']
        text_col = get_contrast_text_color(bg_col)

        rect = pygame.Rect(x_pos, s.initial_pos[1], s.shutdown_button_size[0], s.shutdown_button_size[1])
        pygame.draw.rect(window, bg_col, rect, border_radius=10)

        # 🔹 FOCUS INDICATOR = AKTUALNIE ZAZNACZONY ELEMENT
        if is_selected:
            pygame.draw.rect(window, (255, 200, 0), rect, 4, border_radius=10)

        # Tekst przycisku
        main_text = "Shutdown Launcher"
        status_text = "STATUS: ON" if is_on else "STATUS: OFF"
        status_col = (100, 255, 100) if is_on else (255, 100, 100)

        t1 = s.font.render(main_text, True, text_col)
        t2 = s.font.render(status_text, True, status_col if not is_selected else text_col)

        window.blit(t1, (rect.centerx - t1.get_width()//2, rect.y + 40))
        window.blit(t2, (rect.centerx - t2.get_width()//2, rect.y + 110))

        # Podpowiedź na dole
        desc = "Close app when game starts"
        desc_surf = s.font.render(desc, True, s.current_theme['colour_4'])
        window.blit(desc_surf, (x_pos, rect.bottom + 20))