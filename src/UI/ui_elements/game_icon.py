import pygame
import os

from settings import GAMES_DIR, THEME_LIBRARY
from Tools.asset_importing_tool import import_image 

#GAME ICONS USED IN LIBARY AND STORE
class GameIcon(pygame.sprite.Sprite):
    def __init__(
        s,
        launcher,
        groups,
        game_id: str,
        size: int,
        position=(0, 0),
        source = "library",   # library | store
        path=None,
    ):
        super().__init__(*groups)
        s.launcher = launcher
        s.game_id = game_id
        s.source = source

        s.selected = False

        s.size = size
        s.image = s._load_icon(path)
        s.rect = s.image.get_rect(center=position)

    def _load_icon(s, path):
        if path and os.path.exists(os.path.join(path + '.png')):
            img = import_image(path)
            if img:
                return pygame.transform.smoothscale(img, (s.size, s.size))

        fallback = pygame.Surface((s.size, s.size))
        fallback.fill((50, 50, 50))
        return fallback

    def set_selected(self, value: bool):
        self.selected = value

    def set_position(self, x, y):
        self.rect.center = (x, y)

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

        if self.launcher.installer.is_downloading and self.launcher.installer.current_game_id == self.game_id:
            progress = self.launcher.installer.download_progress
            badge_rect = pygame.Rect(
                self.rect.left,
                self.rect.centery,
                self.rect.width,
                60
            )
            pygame.draw.rect(surface, theme['colour_3'], badge_rect)
            pygame.draw.rect(surface, theme['colour_1'], badge_rect, 2, border_radius=8)

            font = pygame.font.SysFont(None, 32, bold=True)
            status_text = f"DOWNLOADING {int(progress)}%"
            text_surf = font.render(status_text, True, theme['colour_2'])
            surface.blit(text_surf, text_surf.get_rect(center=badge_rect.center))
