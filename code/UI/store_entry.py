import pygame
from os.path import join

from settings import THEME_LIBRARY
from UI.game_icon import GameIcon
from settings import BASE_DIR


class StoreEntry(pygame.sprite.Sprite):

    def __init__(
        self,
        launcher,
        game_id: str,
        game_data: dict,
        size: tuple,          # (width, height)
        position: tuple,      # topleft
        *groups
    ):
        super().__init__(*groups)

        self.launcher = launcher
        self.game_id = game_id
        self.game_data = game_data
        self.width, self.height = size

        self.rect = pygame.Rect(position, size)

        # ---------- ICON ----------
        self.icon_size = self.height - 20
        
        # Poprawna ścieżka: każdy folder i plik jako osobny argument w join
        full_icon_path = join(BASE_DIR, "assets", "store_assets", "game_icons", f"{game_id}.png")

        self.icon = GameIcon(
            launcher=self.launcher,
            groups=[],
            game_id=game_id,
            size=self.icon_size,
            source="store",
            icon_path=full_icon_path
        )

        # ---------- FONTS ----------
        self.title_font = pygame.font.Font(None, 32)
        self.meta_font = pygame.font.Font(None, 22)
        self.desc_font = pygame.font.Font(None, 20)

    # =========================
    # LAYOUT
    # =========================

    def _layout(self):
        padding = 10
        icon_x = self.rect.left + padding + self.icon_size // 2
        icon_y = self.rect.centery

        self.icon.set_position(icon_x, icon_y)

        self.text_x = self.rect.left + padding * 2 + self.icon_size
        self.text_y = self.rect.top + padding

    # =========================
    # DRAW
    # =========================

    def draw(self, surface):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        self._layout()

        # --- background ---
        pygame.draw.rect(
            surface,
            theme['colour_1'],
            self.rect,
            border_radius=12
        )

        # --- border ---
        pygame.draw.rect(
            surface,
            theme['colour_4'],
            self.rect,
            width=2,
            border_radius=12
        )

        # --- icon ---
        self.icon.draw(surface)

        # --- texts ---
        y = self.text_y

        title = self.title_font.render(
            self.game_data['name'],
            True,
            theme['colour_3']
        )
        surface.blit(title, (self.text_x, y))
        y += title.get_height() + 4

        meta = f"{self.game_data['author']}  |  v{self.game_data['version']}"
        meta_text = self.meta_font.render(meta, True, theme['colour_2'])
        surface.blit(meta_text, (self.text_x, y))
        y += meta_text.get_height() + 8

        desc = self._render_description(
            self.game_data['description'],
            theme['colour_2'],
            max_width=self.rect.right - self.text_x - 10
        )

        for line in desc:
            surface.blit(line, (self.text_x, y))
            y += line.get_height() + 2

    # =========================
    # TEXT WRAPPING
    # =========================

    def _render_description(self, text, colour, max_width):
        words = text.split(" ")
        lines = []
        current = ""

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
