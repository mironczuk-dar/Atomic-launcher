import pygame

class Bar:
    def __init__(self, x, y, w, h, bg_color=(40, 40, 40), bar_color=(0, 200, 100), border_color=(200, 200, 200), border_width=2):
        self.rect = pygame.Rect(x, y, w, h)
        self.bg_color = bg_color
        self.bar_color = bar_color
        self.border_color = border_color
        self.border_width = border_width
        
        # Procent od 0 do 100
        self.progress = 0

    def set_progress(self, value):
        """Ustawia postęp, dbając o zakres 0-100."""
        self.progress = max(0, min(100, value))

    def draw(self, surface):
        # 1. Rysujemy tło belki
        pygame.draw.rect(surface, self.bg_color, self.rect)

        # 2. Obliczamy szerokość wypełnienia
        fill_width = (self.progress / 100) * self.rect.width
        if fill_width > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(surface, self.bar_color, fill_rect)

        # 3. Rysujemy obramowanie (opcjonalnie)
        if self.border_width > 0:
            pygame.draw.rect(surface, self.border_color, self.rect, self.border_width)

    def draw_with_text(self, surface, font, text_color=(255, 255, 255)):
        """Rysuje belkę oraz procentowy tekst na środku."""
        self.draw(surface)
        
        percentage_text = f"{int(self.progress)}%"
        text_surf = font.render(percentage_text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)