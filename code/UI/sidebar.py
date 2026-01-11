# IMPORTING FILES
import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY

class Sidebar:
    def __init__(self, launcher):
        self.launcher = launcher
        self.index = 0

        self.base_w = int(WINDOW_WIDTH * 0.1)
        self.expanded_w = int(WINDOW_WIDTH * 0.4)
        self.current_w = self.base_w

        self.font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.045), bold=False)

        # ---- ICONS ----
        self.icon_size = int(WINDOW_WIDTH * 0.035)
        self.icons = {}  # state_name -> Surface

        # ---- OPTIONS ----
        self.options = list(self.launcher.state_manager.states.keys())

    # ===============================
    # ICON LOADING
    # ===============================

    def load_icons(self):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        default = pygame.Surface((self.icon_size, self.icon_size))
        default.fill(theme['colour_2'])

        for state in self.options:
            self.icons[state] = default

    # ===============================
    # INPUT
    # ===============================

    def handle_input(self, keys, ui_focus):
        if ui_focus != "sidebar" or not self.options:
            return

        if keys[pygame.K_DOWN]:
            self.index = (self.index + 1) % len(self.options)
        elif keys[pygame.K_UP]:
            self.index = (self.index - 1) % len(self.options)
        elif keys[pygame.K_RETURN]:
            self.launcher.state_manager.set_state(self.options[self.index])

    # ===============================
    # UPDATE
    # ===============================

    def update(self, delta, ui_focus):
        target = self.expanded_w if ui_focus == "sidebar" else self.base_w
        self.current_w += (target - self.current_w) * 12 * delta

    # ===============================
    # DRAW
    # ===============================

    def draw(self, window):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]

        # aktualizujemy opcje tylko jeśli się zmieniły
        self.options = list(self.launcher.state_manager.states.keys())

        # ---- BACKGROUND ----
        pygame.draw.rect(
            window,
            theme['colour_4'],
            (0, 0, int(self.current_w), WINDOW_HEIGHT)
        )

        if not self.options:
            return

        # ---- EXPAND PROGRESS ----
        width_diff = self.expanded_w - self.base_w
        progress = (self.current_w - self.base_w) / max(1, width_diff)
        progress = max(0.0, min(1.0, progress))

        section_h = WINDOW_HEIGHT / len(self.options)

        for i, name in enumerate(self.options):
            selected = i == self.index
            color = theme['colour_3'] if selected else (220, 220, 220)

            y = section_h * i + section_h / 2

            # ---- ICON ----
            icon = self.icons.get(name)
            if icon:
                icon_y = y - icon.get_height() / 2
                window.blit(icon, (20, icon_y))

            # ---- TEXT (dopiero po rozwinięciu) ----
            if progress > 0.25:
                text = self.font.render(name.upper(), True, color).convert_alpha()
                text.set_alpha(int(progress * 255))

                text_x = 20 + self.icon_size + 16
                text_y = y - text.get_height() / 2
                window.blit(text, (text_x, text_y))
