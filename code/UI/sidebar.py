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
        self.options = [
            "Library",
            "Store",
            "Options",
            "Exit"
        ]


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

    def handle_input(self, keys):
        if not self.options:
            return

        if keys[pygame.K_DOWN]:
            self.index = (self.index + 1) % len(self.options)

        elif keys[pygame.K_UP]:
            self.index = (self.index - 1) % len(self.options)

        elif keys[pygame.K_RIGHT]:
            self.launcher.state_manager.ui_focus = 'content'

        elif keys[pygame.K_RETURN]:
            self.launcher.state_manager.set_state(
                self.options[self.index]
            )
            self.launcher.state_manager.ui_focus = 'content'

    # ===============================
    # UPDATE
    # ===============================

    def update(self, delta):
        ui_focus = self.launcher.state_manager.ui_focus
        target = self.expanded_w if ui_focus == "sidebar" else self.base_w
        self.current_w += (target - self.current_w) * 12 * delta


    # ===============================
    # DRAW
    # ===============================

    def draw(self, window):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]

        # ---- BACKGROUND ----
        pygame.draw.rect(window, theme['colour_4'], (0, 0, int(self.current_w), WINDOW_HEIGHT))

        if not self.options:
            return

        # ---- USTAWIENIA ODSTĘPÓW ----
        item_height = 60  # Stała wysokość jednego elementu
        start_y = 100     # Margines od górnej krawędzi paska
        spacing = 40      # Dodatkowy odstęp między ikonami

        width_diff = self.expanded_w - self.base_w
        progress = (self.current_w - self.base_w) / max(1, width_diff)
        progress = max(0.0, min(1.0, progress))

        for i, name in enumerate(self.options):
            selected = i == self.index
            color = theme['colour_3'] if selected else (220, 220, 220)

            # Obliczamy Y na podstawie stałej wysokości, a nie wysokości okna
            y_center = start_y + i * (item_height + spacing)

            # ---- ICON ----
            icon = self.icons.get(name)
            if icon:
                # Wyśrodkowanie ikony w pionie względem y_center
                icon_y = y_center - icon.get_height() / 2
                # Ikona zostaje na stałej pozycji X (np. 20px)
                window.blit(icon, (20, icon_y))

            # ---- TEXT ----
            if progress > 0.25:
                text_surf = self.font.render(name.upper(), True, color).convert_alpha()
                text_surf.set_alpha(int(progress * 255))

                text_x = 20 + self.icon_size + 16
                text_y = y_center - text_surf.get_height() / 2
                window.blit(text_surf, (text_x, text_y))