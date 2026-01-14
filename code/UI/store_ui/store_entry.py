# ==========================
# store_entry.py
# ==========================
import pygame
from enum import Enum
from os.path import join

from settings import THEME_LIBRARY, BASE_DIR
from UI.game_icon import GameIcon


class GameStatus(str, Enum):
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    UPDATE_AVAILABLE = "update"


class StoreEntry(pygame.sprite.Sprite):
    def __init__(self, launcher, game_id, game_data, status, size, position):
        super().__init__()

        self.launcher = launcher
        self.game_id = game_id
        self.game_data = game_data
        self.status = status

        self.width, self.height = size
        self.rect = pygame.Rect(position, size)

        # ---------- ICON ----------
        self.icon_size = self.height - 20
        icon_path = join(BASE_DIR, 'assets', 'store_assets', 'game_icons', f'{game_id}')

        self.icon = GameIcon(
            launcher=self.launcher,
            groups=[],
            game_id=game_id,
            size=self.icon_size,
            source="store",
            path=icon_path
        )

        # ---------- FONTS ----------
        self.title_font = pygame.font.Font(None, 32)
        self.meta_font = pygame.font.Font(None, 22)
        self.desc_font = pygame.font.Font(None, 20)

    # =========================
    def _layout(self):
        padding = 10
        self.icon.set_position(
            self.rect.left + padding + self.icon_size // 2,
            self.rect.centery
        )
        self.text_x = self.rect.left + padding * 2 + self.icon_size
        self.text_y = self.rect.top + padding

    # =========================
    def draw(self, surface):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        self._layout()

        pygame.draw.rect(surface, theme['colour_1'], self.rect, border_radius=12)
        pygame.draw.rect(surface, theme['colour_4'], self.rect, 2, border_radius=12)

        self.icon.draw(surface)

        y = self.text_y
        title = self.title_font.render(self.game_data['name'], True, theme['colour_3'])
        surface.blit(title, (self.text_x, y))
        y += title.get_height() + 4

        meta = f"{self.game_data['author']}  |  v{self.game_data['version']}"
        surface.blit(self.meta_font.render(meta, True, theme['colour_2']), (self.text_x, y))
        y += 30

        for line in self._wrap(self.game_data['description'], theme['colour_2']):
            surface.blit(line, (self.text_x, y))
            y += line.get_height() + 2

        self._draw_status_badge(surface, theme)

    # =========================
    def _draw_status_badge(self, surface, theme):
        mapping = {
            GameStatus.NOT_INSTALLED: ("DOWNLOAD", theme['colour_3']),
            GameStatus.INSTALLED: ("INSTALLED", (0, 200, 0)),
            GameStatus.UPDATE_AVAILABLE: ("UPDATE", (255, 170, 0))
        }

        label, color = mapping[self.status]
        badge = self.meta_font.render(label, True, color)

        surface.blit(
            badge,
            (self.rect.right - badge.get_width() - 15,
            self.rect.top + 15)
        )

    # =========================
    def _wrap(self, text, colour):
        max_width = self.rect.right - self.text_x - 10
        words = text.split(" ")
        lines, current = [], ""

        for word in words:
            test = current + word + " "
            if self.desc_font.size(test)[0] <= max_width:
                current = test
            else:
                lines.append(self.desc_font.render(current, True, colour))
                current = word + " "

        if current:
            lines.append(self.desc_font.render(current, True, colour))

        return lines
