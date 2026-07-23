"""Theme selection options tab.

This tab displays a list of available launcher themes and allows the user
to switch the current theme. It persists the selected theme to disk and
notifies the parent options state to refresh its tab visuals.
"""

import pygame

from settings import get_contrast_text_color
from Tools.data_loading_tools import save_data
from settings import THEME_LIBRARY, THEMES_DATA_PATH, WINDOW_WIDTH
from UI.options_ui.generic_options_tab import GenericOptionsTab



class ThemesOptionsTab(GenericOptionsTab):
    """Options tab that lists available themes and allows selection."""

    def __init__(s, launcher):
        super().__init__(launcher)
        
        # UI Layout
        s.initial_pos = (WINDOW_WIDTH * 0.3, 175)
        s.button_size = (500, 100)
        s.spacing = 20
        
        s.font = pygame.font.SysFont(None, 70, False)
        
        # Logic
        s.theme_names = list(THEME_LIBRARY.keys())
        s.selected_index = 0
        
        # Sync index with current theme
        current = s.launcher.theme_data['current_theme']
        if current in s.theme_names:
            s.selected_index = s.theme_names.index(current)

    def handling_events(s, events, ctrl):
        if s.launcher.state_manager.ui_focus != 'content':
            return

        input_manager = getattr(s.launcher, 'input_manager', None)
        if input_manager is None:
            return

        if input_manager.just_pressed('up'):
            s.selected_index = (s.selected_index - 1) % len(s.theme_names)
        elif input_manager.just_pressed('down'):
            s.selected_index = (s.selected_index + 1) % len(s.theme_names)

        if input_manager.just_pressed('action_a'):
            new_theme = s.theme_names[s.selected_index]
            s.apply_theme(new_theme)

    def apply_theme(s, theme_name):
        s.launcher.theme_data['current_theme'] = theme_name
        save_data(s.launcher.theme_data, THEMES_DATA_PATH)
        
        # WYWOŁANIE REODŚWIEŻENIA:
        # Zakładając, że s.launcher.state_manager.current_state to instancja Options
        current_state = s.launcher.state_manager.active_state
        if hasattr(current_state, 'refresh_tabs'):
            current_state.refresh_tabs()

    def draw(s, window):
        has_focus = (s.launcher.state_manager.ui_focus == 'content')
        
        # We fetch the theme dynamically so the preview updates immediately 
        # if the user changes it
        current_visuals = THEME_LIBRARY[s.launcher.theme_data['current_theme']]

        for i, name in enumerate(s.theme_names):
            is_hovered = (i == s.selected_index and has_focus)
            is_active = (name == s.launcher.theme_data['current_theme'])
            
            # Button Colors
            bg_col = current_visuals['colour_2'] if is_hovered else current_visuals['colour_4']
            text_col = get_contrast_text_color(bg_col)
            
            x = s.initial_pos[0]
            y = s.initial_pos[1] + i * (s.button_size[1] + s.spacing)
            
            rect = pygame.Rect(x, y, s.button_size[0], s.button_size[1])
            
            # Draw Button
            pygame.draw.rect(window, bg_col, rect, border_radius=10)
            
            # Active indicator (Border)
            if is_active:
                pygame.draw.rect(window, (255, 255, 255), rect, 4, border_radius=10)

                # Focus indicator for the currently selected theme button
            if is_hovered:
                pygame.draw.rect(window, (255, 200, 0), rect, 4, border_radius=10)

            # Theme Name
            text_surf = s.font.render(name, True, text_col)
            text_rect = text_surf.get_rect(center=rect.center)
            window.blit(text_surf, text_rect)
            
            # Small Color Preview Swatches
            s.draw_color_previews(window, name, x + s.button_size[0] + 20, y)

    def draw_color_previews(s, window, theme_name, x, y):
        colors = THEME_LIBRARY[theme_name]
        swatch_size = 80
        for j, col_key in enumerate(['colour_1', 'colour_2', 'colour_3', 'colour_4']):
            swatch_rect = pygame.Rect(x + (j * (swatch_size + 5)), y + 15, swatch_size, swatch_size)
            pygame.draw.rect(window, colors[col_key], swatch_rect)
            pygame.draw.rect(window, (200, 200, 200), swatch_rect, 2) # Outline
