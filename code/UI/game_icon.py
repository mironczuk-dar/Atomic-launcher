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

        # 1. Tworzymy domyślny wygląd (fallback)
        default = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(default, theme['colour_2'], (0, 0, *size), border_radius=15)

        # 2. Ustalamy skąd brać obrazek
        final_path = None
        
        if self.source == "store" and icon_path:
            # Jeśli jesteśmy w sklepie, używamy ścieżki przekazanej w __init__
            final_path = icon_path
        else:
            # Jeśli jesteśmy w bibliotece, szukamy w folderze zainstalowanej gry
            final_path = os.path.join(GAMES_DIR, self.game_id, "assets", "icon.png")

        # 3. Próbujemy załadować plik
        try:
            if final_path and os.path.exists(final_path):
                img = pygame.image.load(final_path).convert_alpha()
                return pygame.transform.smoothscale(img, size)
        except Exception as e:
            print(f"[GameIcon] Błąd ładowania ikony {self.game_id}: {e}")

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
