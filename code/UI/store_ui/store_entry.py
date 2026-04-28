import pygame
from enum import Enum, auto
from os.path import join

from settings import THEME_LIBRARY, BASE_DIR
from UI.game_icon import GameIcon


class GameStatus(Enum):
    NOT_INSTALLED = auto()
    UPDATE_AVAILABLE = auto()
    INSTALLED = auto()
    DOWNLOADING = auto()


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
        # Scaled down slightly to give text more horizontal breathing room
        self.icon_size = int(self.height * 0.65) 
        icon_path = join(BASE_DIR, 'assets', 'store_assets', f'{game_id}', 'icon')

        self.icon = GameIcon(
            launcher=self.launcher,
            groups=[],
            game_id=game_id,
            size=self.icon_size,
            source="store",
            path=icon_path
        )

        # ---------- FONTS ----------
        # Adjusted for 1280x720 screen space hierarchy
        self.title_font = pygame.font.SysFont(None, 32, bold=True)
        self.meta_font = pygame.font.SysFont(None, 18, italic=True)
        self.desc_font = pygame.font.SysFont(None, 26)
        self.tag_font = pygame.font.SysFont(None, 24)
        self.badge_font = pygame.font.SysFont(None, 16, bold=True)

    # =========================
    def _layout(self):
        padding = 20

        # Icon position (centered vertically)
        self.icon.set_position(
            self.rect.left + padding + self.icon_size // 2,
            self.rect.centery
        )

        # Text start
        self.text_x = self.rect.left + padding * 1.5 + self.icon_size
        self.text_y = self.rect.top + padding

        # Max width for text (accounting for right padding)
        self.text_width = self.rect.right - self.text_x - padding

    # =========================
    def draw(self, surface):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        self._layout()

        # ---------- CARD BACKGROUND ----------
        # Use the darkest colour_1 for the card itself to make it look "recessed" 
        # or use colour_4 to match the panel. Let's go with colour_1 for contrast.
        pygame.draw.rect(surface, theme['colour_1'], self.rect, border_radius=14)
        # Border using colour_3 (low opacity/muted)
        pygame.draw.rect(surface, theme['colour_3'], self.rect, 2, border_radius=14)

        self.icon.draw(surface)

        # ---------- TEXT ----------
        y = self.text_y

        # Title: Primary Accent (colour_2)
        title_text = self.game_data.get('name', 'Unknown Game')
        title = self.title_font.render(title_text, True, theme['colour_2'])
        surface.blit(title, (self.text_x, y))
        y += title.get_height() + 2

        # Meta & Description: Use colour_3 or white for readability
        meta = f"v{self.game_data.get('version', '1.0.0')}"
        meta_surf = self.meta_font.render(meta, True, theme['colour_3'])
        surface.blit(meta_surf, (self.text_x, y))
        y += meta_surf.get_height() + 10

        # Main description text should be very readable (White or soft grey)
        desc_color = (230, 230, 230) 
        desc_lines = self._wrap(self.game_data.get('description', ''), 3, desc_color)
        for line in desc_lines:
            surface.blit(line, (self.text_x, y))
            y += line.get_height() + 4

        self.draw_tags(surface, theme)
        self.draw_status(surface)

    # =========================
    def draw_status(self, surface):
        mapping = {
            GameStatus.NOT_INSTALLED: ("GET", (60, 120, 220)),       # Blueish
            GameStatus.INSTALLED: ("INSTALLED", (60, 180, 100)),     # Green
            GameStatus.UPDATE_AVAILABLE: ("UPDATE", (220, 140, 40)), # Orange
            GameStatus.DOWNLOADING: ("DOWNLOADING", (200, 200, 60))  # Yellow
        }

        label, bg_color = mapping[self.status]

        # White text for better contrast against vibrant badge backgrounds
        text = self.badge_font.render(label, True, (255, 255, 255))
        padding_x, padding_y = 12, 6

        rect = pygame.Rect(
            0, 0,
            text.get_width() + padding_x * 2,
            text.get_height() + padding_y * 2
        )

        # Align to top right
        rect.topright = (self.rect.right - 15, self.rect.top + 15)

        # Draw Badge Pill
        pygame.draw.rect(surface, bg_color, rect, border_radius=12)
        surface.blit(text, (rect.x + padding_x, rect.y + padding_y))

    # =========================
    def _wrap(self, text, max_lines, color):
        """Wraps text and adds '...' if it exceeds max_lines."""
        words = text.split(" ")
        lines = []
        current = ""

        for word in words:
            test = current + word + " "
            if self.desc_font.size(test)[0] <= self.text_width:
                current = test
            else:
                lines.append(current.strip())
                current = word + " "

                if len(lines) >= max_lines:
                    break

        if current and len(lines) < max_lines:
            lines.append(current.strip())

        # Render surfaces and handle ellipsis
        rendered_lines = []
        for i, line in enumerate(lines):
            # If we hit the max line limit and there are still words left, add ellipsis
            if i == max_lines - 1 and len(lines) == max_lines and len(text) > len(" ".join(lines)):
                # Carve out space for the '...'
                while self.desc_font.size(line + "...")[0] > self.text_width and len(line) > 0:
                    line = line[:-1]
                line += "..."
            
            rendered_lines.append(self.desc_font.render(line, True, color))
            
            if i == max_lines - 1:
                break

        return rendered_lines

    # =========================
    def draw_tags(self, surface, theme):
        x = self.text_x
        y = self.rect.bottom - 32 

        for tag in self.game_data.get('tags', [])[:3]:
            # Tags use colour_4 as a capsule background
            text = self.tag_font.render(tag.upper(), True, theme['colour_3'])
            rect = pygame.Rect(x, y, text.get_width() + 16, text.get_height() + 8)

            pygame.draw.rect(surface, theme['colour_4'], rect, border_radius=10)
            surface.blit(text, (rect.x + 8, rect.y + 4))
            x += rect.width + 10