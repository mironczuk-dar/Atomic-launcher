#IMPORTING LIBRARIES
import pygame

#IMPORTING FILES
from settings import WINDOW_WIDTH, THEME_LIBRARY, WINDOW_HEIGHT, get_contrast_text_color

#IMPORTING UI ELEMENTS
from UI.ui_elements.keyboard import Keyboard

class SearchBar:
    def __init__(self, launcher, on_change, width=int(WINDOW_WIDTH * 0.3), height=int(WINDOW_HEIGHT * 0.1), x=None, y=None):
        self.launcher = launcher
        self.on_change = on_change
        self.active = False
        self.text = ""
        
        # New: Internal Keyboard instance
        self.keyboard = Keyboard(
            launcher, 
            pos=(WINDOW_WIDTH // 2 - 600, WINDOW_HEIGHT *0.4), 
            size=(1200, 600)
        )
        
        self.w, self.h = width, height
        self.custom_x, self.custom_y = x, y
        self.font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.035))

    def handle_events(self, events):
        if self.active:
            self.keyboard.handling_events(events)
            
            # Sync text and trigger the search filter update
            if self.text != self.keyboard.text:
                self.text = self.keyboard.text
                self.on_change(self.text)

            if self.keyboard.finished:
                self.active = False
                self.keyboard.finished = False
                return True # Signal that we are done typing
        return False

    def open_keyboard(self):
        self.active = True
        self.keyboard.text = self.text # Sync current text to keyboard

    def draw(self, window, focused):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        bar_x = self.custom_x if self.custom_x is not None else WINDOW_WIDTH // 2 - self.w // 2
        bar_y = self.custom_y if self.custom_y is not None else self.h // 2 - self.h // 2

        # 2) Visual Indication of focus
        if self.active:
            border_color = theme['colour_3'] # Active typing color
            thickness = 8
        elif focused:
            border_color = (255, 255, 255) # Hovered color (White or highlight)
            thickness = 8
        else:
            border_color = theme['colour_4'] # Default color
            thickness = 2

        # Draw Bar Background and Border
        pygame.draw.rect(window, theme['colour_2'], (bar_x, bar_y, self.w, self.h), border_radius=8)
        pygame.draw.rect(window, border_color, (bar_x, bar_y, self.w, self.h), thickness, border_radius=8)

        # Draw Text/Cursor
        display = self.text + ("|" if self.active and pygame.time.get_ticks() % 1000 < 500 else "")
        color = get_contrast_text_color(theme['colour_2']) if (self.active or focused) else (80, 80, 80)
        surf = self.font.render(display if display else "Search...", True, color)
        window.blit(surf, (bar_x + 12, bar_y + self.h // 2 - surf.get_height() // 2))

        # Draw Keyboard Overlay if active
        if self.active:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            window.blit(overlay, (0, 0))
            self.keyboard.draw(window)
