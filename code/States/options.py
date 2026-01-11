import pygame
from States.generic_state import BaseState
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.sidebar import Sidebar

class Options(BaseState):
    def __init__(self, launcher):
        super().__init__(launcher)

        # -------------------
        # SIDEBAR
        # -------------------
        self.sidebar = Sidebar(launcher)
        self.ui_focus = "content"  # content / sidebar

        # -------------------
        # TABS
        # -------------------
        self.tabs = ["Controls", "Video", "Themes"]
        self.tab_index = 0

        # Czcionki
        self.title_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.06), bold=True)
        self.text_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.04))

        # -------------------
        # DUMMY SETTINGS
        # -------------------
        self.settings = {
            "Controls": {"Move Up": "W", "Move Down": "S", "Jump": "Space"},
            "Video": {"Resolution": "1920x1080", "Fullscreen": True},
            "Themes": {"Current Theme": self.launcher.theme_data['current_theme']}
        }

    # ===============================
    # EVENTS / INPUT
    # ===============================
    def handling_events(self, events):
        keys = pygame.key.get_pressed()

        # ---- SIDEBAR FOCUS ----
        self.sidebar.handle_input(keys, self.ui_focus)

        if self.ui_focus == "content":
            if keys[pygame.K_LEFT]:
                self.tab_index = (self.tab_index - 1) % len(self.tabs)
            elif keys[pygame.K_RIGHT]:
                self.tab_index = (self.tab_index + 1) % len(self.tabs)

            elif keys[pygame.K_TAB]:
                self.ui_focus = "sidebar"  # przeniesienie focusu na sidebar

        elif self.ui_focus == "sidebar":
            if keys[pygame.K_TAB]:
                self.ui_focus = "content"  # powrót do contentu

    # ===============================
    # UPDATE
    # ===============================
    def update(self, delta):
        self.sidebar.update(delta, self.ui_focus)

    # ===============================
    # DRAW
    # ===============================
    def draw(self, window):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]

        window.fill(theme['colour_1'])  # tło

        # ---- SIDEBAR ----
        self.sidebar.draw(window)

        # ---- TABS ----
        tab_y = 20
        tab_x = int(self.sidebar.current_w) + 20
        for i, tab in enumerate(self.tabs):
            color = theme['colour_3'] if i == self.tab_index else (180, 180, 180)
            text_surf = self.text_font.render(tab, True, color)
            window.blit(text_surf, (tab_x + i * 160, tab_y))

        # ---- CONTENT ----
        content_y = 100
        content_x = int(self.sidebar.current_w) + 40
        active_tab = self.tabs[self.tab_index]
        tab_settings = self.settings.get(active_tab, {})

        for i, (key, value) in enumerate(tab_settings.items()):
            line = f"{key}: {value}"
            text_surf = self.text_font.render(line, True, theme['colour_3'])
            window.blit(text_surf, (content_x, content_y + i * 40))
