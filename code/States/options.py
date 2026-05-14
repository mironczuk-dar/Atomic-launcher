#IMPORTING LIBRARIES
import pygame

#IMPORTING FILES
from UI.options_ui.option_tabs import (
    VideoOptionsTab,
    ThemesOptionsTab,
    ControlsOptionsTab,
    PerformanceOptionsTab
)
from settings import THEME_LIBRARY, WINDOW_WIDTH, WINDOW_HEIGHT, get_contrast_text_color
from States.generic_state import BaseState


class Options(BaseState):

    def __init__(s, launcher):
        super().__init__(launcher)

        # ---------------- TABS ----------------
        s.tabs = [
            ('Video', VideoOptionsTab(launcher)),
            ('Controls', ControlsOptionsTab(launcher)),
            ('Performance', PerformanceOptionsTab(launcher)),
            ('Themes', ThemesOptionsTab(launcher)),
        ]

        s.topbar_index = 0

        # ---------------- TOPBAR ----------------
        s.topbar_font = pygame.font.SysFont(None, 34)
        s.topbar_padding = (24, 12)  # horizontal, vertical padding
        s.topbar_spacing = 12
        s.topbar_y = int(WINDOW_HEIGHT * 0.06)
        s.topbar_button_height = s.topbar_font.get_height() + s.topbar_padding[1] * 2

        # Icons for tabs (generated from label initials if no assets available)
        s.topbar_icon_size = (28, 28)
        s.topbar_icon_spacing = 10
        s.topbar_icon_font = pygame.font.SysFont(None, 20)
        s.tab_icons = []
        s.generate_tab_icons()

    # =====================================================

    def update(s, delta_time):
        _, active_tab = s.tabs[s.topbar_index]
        active_tab.update(delta_time)

    # =====================================================

    def draw(s, window):
        window.fill((0, 0, 0))

        # Draw a subtle separator under the top tabs
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        separator_y = s.topbar_y + s.topbar_button_height + 12
        pygame.draw.rect(window, theme['colour_2'], pygame.Rect(0, separator_y, WINDOW_WIDTH, 4))

        s.draw_topbar(window)

        _, active_tab = s.tabs[s.topbar_index]
        active_tab.draw(window)

    # =====================================================

    def handling_events(s, events):
        keys = pygame.key.get_just_pressed()
        ctrl = s.launcher.controlls_data['keyboard']

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

        # Calculate widths for each tab based on icon + label size + padding
        label_sizes = [s.topbar_font.size(label) for (label, _) in s.tabs]
        icon_w = s.topbar_icon_size[0]
        tab_widths = [icon_w + s.topbar_icon_spacing + w + s.topbar_padding[0] * 2 for (w, h) in label_sizes]
        total_width = sum(tab_widths) + s.topbar_spacing * (len(tab_widths) - 1)
        start_x = int((WINDOW_WIDTH - total_width) // 2)
        y = s.topbar_y

        for i, (label, _) in enumerate(s.tabs):
            w = tab_widths[i]
            h = s.topbar_button_height
            x = start_x + sum(tab_widths[:i]) + s.topbar_spacing * i if i > 0 else start_x

            tab_rect = pygame.Rect(x, y, w, h)

            is_selected = (i == s.topbar_index)
            has_focus = (s.launcher.state_manager.ui_focus == 'topbar')

            # Use stronger color when tab is selected AND topbar has focus
            if is_selected and has_focus:
                bg_color = theme['colour_2']
                text_color = get_contrast_text_color(bg_color)
                outline_color = text_color
                outline_width = 3
            elif is_selected:
                bg_color = theme['colour_4']
                text_color = get_contrast_text_color(bg_color)
                outline_color = theme['colour_3']
                outline_width = 2
            else:
                bg_color = theme['colour_4']
                text_color = get_contrast_text_color(bg_color)
                outline_color = (0, 0, 0)
                outline_width = 1

            # Draw rounded tab background
            pygame.draw.rect(window, bg_color, tab_rect, border_radius=12)

            # Draw outline / accent
            pygame.draw.rect(window, outline_color, tab_rect, outline_width, border_radius=12)

            # Draw icon (if generated)
            if i < len(s.tab_icons):
                icon = s.tab_icons[i]
                icon_y = tab_rect.centery - icon.get_height() // 2
                icon_x = tab_rect.x + s.topbar_padding[0]
                window.blit(icon, (icon_x, icon_y))
                text_x_offset = s.topbar_padding[0] + icon.get_width() + s.topbar_icon_spacing
            else:
                text_x_offset = s.topbar_padding[0]

            # Render text
            text_surf = s.topbar_font.render(label, True, text_color)
            text_rect = text_surf.get_rect(center=(tab_rect.x + text_x_offset + (tab_rect.width - text_x_offset) // 2, tab_rect.centery))
            window.blit(text_surf, text_rect)

        # Draw focus underline when topbar has focus
        if s.launcher.state_manager.ui_focus == 'topbar':
            underline_rect = pygame.Rect(start_x, y + s.topbar_button_height + 8, total_width, 4)
            pygame.draw.rect(window, theme['colour_1'], underline_rect, border_radius=2)

    # =====================================================

    def generate_tab_icons(s):
        """Generate small circular icons for each tab using the current theme and the label initial."""
        s.tab_icons = []
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        for label, _ in s.tabs:
            icon_surf = pygame.Surface(s.topbar_icon_size, pygame.SRCALPHA)
            pygame.draw.circle(
                icon_surf,
                theme['colour_3'],
                (s.topbar_icon_size[0]//2, s.topbar_icon_size[1]//2),
                s.topbar_icon_size[0]//2
            )
            initial = label[0].upper()
            txt = s.topbar_icon_font.render(initial, True, theme['colour_4'])
            icon_surf.blit(txt, txt.get_rect(center=(s.topbar_icon_size[0]//2, s.topbar_icon_size[1]//2)))
            s.tab_icons.append(icon_surf)

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
        # Regenerate icons so they respect the newly selected theme
        s.generate_tab_icons()
