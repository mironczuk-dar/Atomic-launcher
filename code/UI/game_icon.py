import pygame
import os

from settings import GAMES_DIR, THEME_LIBRARY


class GameIcon(pygame.sprite.Sprite):
    def __init__(
        self,
        launcher,
        groups,
        game_id: str,
        size: int,
        position=(0, 0),
        source="library",   # library | store
        icon_path=None,
    ):
        super().__init__(*groups)

        self.launcher = launcher
        self.game_id = game_id
        self.size = size
        self.source = source

        self.selected = False

        self.image = self._load_icon(icon_path)
        self.rect = self.image.get_rect(center=position)

    # =========================
    # LOADING
    # =========================

    def _load_icon(self, icon_path):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        size = (self.size, self.size)

        # default icon
        default = pygame.Surface(size, pygame.SRCALPHA)
        default.fill(theme['colour_2'])

        path = os.path.join(GAMES_DIR, self.game_id, "icon.png")

        if path and os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, size)

        return default

    # =========================
    # STATE
    # =========================

    def set_selected(self, value: bool):
        self.selected = value

    def set_position(self, x, y):
        self.rect.center = (x, y)

    # =========================
    # DRAW
    # =========================

    def draw(self, surface):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]

        if self.selected:
            pygame.draw.rect(
                surface,
                theme['colour_3'],
                self.rect.inflate(16, 16),
                border_radius=10
            )

        surface.blit(self.image, self.rect)
