#IMPORTING LIBRARIES
import pygame

#IMPORTING FILES
from UI.options_ui.option_tabs import (
    VideoOptionsTab,
    ThemesOptionsTab,
    ControlsOptionsTab,
    PerformanceOptionsTab
)
from settings import THEME_LIBRARY, WINDOW_WIDTH, WINDOW_HEIGHT
from States.generic_state import BaseState


class Options(BaseState):

    def __init__(s, launcher):
        super().__init__(launcher)

        # ---------------- TABS ----------------
        s.tabs = [
            ('Video', VideoOptionsTab(launcher)),
            ('Controlls', ControlsOptionsTab(launcher)),
            ('Performance', PerformanceOptionsTab(launcher)),
            ('Themes', ThemesOptionsTab(launcher)),
        ]

        s.topbar_index = 0

        # ---------------- TOPBAR ----------------
        s.topbar_height = WINDOW_HEIGHT * 0.05
        s.topbar_font = pygame.font.SysFont(None, 30)

        s.topbar_pos = (WINDOW_WIDTH * 0.1 + 10, 10)
        s.topbar_button_size = (200, 80)

    # =====================================================

    def update(s, delta_time):
        _, active_tab = s.tabs[s.topbar_index]
        active_tab.update(delta_time)

    # =====================================================

    def draw(s, window):
        window.fill((0, 0, 0))

        if s.launcher.state_manager.ui_focus == 'topbar':
            pygame.draw.rect(
                window,
                (0, 200, 255),
                pygame.Rect(0, 0, WINDOW_WIDTH, 5)
            )
        else:
            pygame.draw.rect(
                window,
                (0, 200, 255),
                pygame.Rect(0, s.topbar_pos[1] + s.topbar_button_size[1] + 10, WINDOW_WIDTH-800, 5)
            )

        s.draw_topbar(window)

        _, active_tab = s.tabs[s.topbar_index]
        active_tab.draw(window)

    # =====================================================

    def handling_events(s, events):
        keys = pygame.key.get_just_pressed()
        ctrl = s.launcher.controlls_data

        # ---------- TOPBAR ----------
        if s.launcher.state_manager.ui_focus == 'topbar':

            if keys[ctrl['right']]:
                if s.topbar_index < len(s.tabs) - 1:
                    s.topbar_index += 1

            elif keys[ctrl['left']]:
                if s.topbar_index > 0:
                    s.topbar_index -= 1
                else:
                    s.launcher.state_manager.ui_focus = 'sidebar'

            if keys[ctrl['action_a']] or keys[pygame.K_RETURN]:
                s.launcher.state_manager.ui_focus = 'content'

        # ---------- CONTENT ----------
        elif s.launcher.state_manager.ui_focus == 'content':

            _, active_tab = s.tabs[s.topbar_index]
            active_tab.handling_events(events, ctrl)

            if keys[ctrl['action_b']]:
                s.launcher.state_manager.ui_focus = 'topbar'

    # =====================================================

    def draw_topbar(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        start_x, y = s.topbar_pos

        for i, (label, _) in enumerate(s.tabs):
            x = start_x + i * (s.topbar_button_size[0] + 10)
            tab_rect = pygame.Rect((x, y), s.topbar_button_size)

            is_selected = (i == s.topbar_index)

            bg_color = theme['colour_2'] if is_selected else theme['colour_4']
            text_color = theme['colour_1'] if is_selected else theme['colour_3']

            pygame.draw.rect(window, bg_color, tab_rect)

            text_surf = s.topbar_font.render(label, True, text_color)
            text_rect = text_surf.get_rect(center=tab_rect.center)
            window.blit(text_surf, text_rect)

            if is_selected:
                pygame.draw.rect(window, (0, 250, 0), tab_rect, 3)

    # =====================================================

    def on_enter(s):
        s.launcher.state_manager.ui_focus = 'topbar'

    def refresh_tabs(s):
        """Metoda wywoływana po zmianie motywu, aby odświeżyć kolory w zakładkach."""
        # Reinicjalizacja zakładek zaktualizuje s.current_theme w ich __init__
        s.tabs = [
            ('Video', VideoOptionsTab(s.launcher)),
            ('Controlls', ControlsOptionsTab(s.launcher)),
            ('Performance', PerformanceOptionsTab(s.launcher)),
            ('Themes', ThemesOptionsTab(s.launcher)),
        ]
