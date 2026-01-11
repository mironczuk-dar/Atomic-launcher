#IMPORTING LIBRARIES
import pygame
from settings import WINDOW_WIDTH, THEME_LIBRARY

class SearchBar:
    def __init__(self, launcher, on_change):
        self.launcher = launcher
        self.on_change = on_change  # callback

        self.active = False
        self.text = ""

        self.h = int(WINDOW_WIDTH * 0.1)
        self.font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.035))

    # =========================
    # INPUT
    # =========================

    def handle_events(self, events):
        if not self.active:
            return False

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_TAB:
                    self.active = False
                    return True  # ← sygnał "wyszedłem"
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                    self.on_change(self.text)
                else:
                    if event.unicode and len(event.unicode) == 1:
                        self.text += event.unicode
                        self.on_change(self.text)

        return False


    # =========================
    # DRAW
    # =========================

    def draw(self, window, focused):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]

        bar_w = int(WINDOW_WIDTH * 0.5)
        bar_h = int(self.h * 0.55)
        bar_x = WINDOW_WIDTH // 2 - bar_w // 2
        bar_y = self.h // 2 - bar_h // 2

        if focused and self.active:
            border = theme['colour_3']
        elif focused:
            border = theme['colour_4']
        else:
            border = theme['colour_2']

        pygame.draw.rect(
            window,
            border,
            (bar_x, bar_y, bar_w, bar_h),
            3,
            border_radius=8
        )

        display = self.text
        if self.active and pygame.time.get_ticks() % 1000 < 500:
            display += "|"

        text = display if display else "Search game..."
        color = (255, 255, 255) if self.active else (140, 140, 140)

        surf = self.font.render(text, True, color)
        window.blit(
            surf,
            (bar_x + 12, bar_y + bar_h // 2 - surf.get_height() // 2)
        )
