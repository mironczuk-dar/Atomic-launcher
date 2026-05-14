import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY


class NavigationTutorial:
    def __init__(self, launcher):
        self.launcher = launcher
        self.theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        self.width = int(WINDOW_WIDTH * 0.32)
        self.height = 198
        self.target_x = WINDOW_WIDTH - self.width - 40
        self.target_y = WINDOW_HEIGHT - self.height - 40
        self.x = self.target_x
        self.y = WINDOW_HEIGHT
        self.speed = 800
        self.state = 'entering' if not self.launcher.game_library_data.get('navigation_tutorial_shown', False) else 'hidden'

        self.title_font = pygame.font.SysFont(None, 45, bold=True)
        self.body_font = pygame.font.SysFont(None, 32)
        self.action_font = pygame.font.SysFont(None, 28, bold=True)

    def is_active(self):
        return self.state in ('entering', 'visible')

    def handle_input(self, keys):
        if self.state != 'visible':
            return False

        controls = self.launcher.controlls_data
        if keys[pygame.K_RETURN] or keys[controls['keyboard']['action_a']]:
            self.dismiss()
            return True

        return False

    def dismiss(self):
        if self.state != 'exiting':
            self.state = 'exiting'
            self.launcher.game_library_data['navigation_tutorial_shown'] = True
            self.launcher.save()

    def update(self, delta_time):
        if self.state == 'entering':
            self.y = max(self.target_y, self.y - self.speed * delta_time)
            if self.y <= self.target_y:
                self.y = self.target_y
                self.state = 'visible'
        elif self.state == 'exiting':
            self.y += self.speed * delta_time
            if self.y >= WINDOW_HEIGHT:
                self.y = WINDOW_HEIGHT
                self.state = 'hidden'

    def draw(self, window):
        if self.state == 'hidden':
            return

        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        x = int(self.x)
        y = int(self.y)
        w = self.width
        h = self.height
        padding = 22

        shadow = pygame.Surface((w, h), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 110))
        window.blit(shadow, (x + 10, y + 10))

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((24, 26, 40, 230))
        pygame.draw.rect(overlay, (255, 255, 255, 20), overlay.get_rect(), border_radius=20)
        pygame.draw.rect(overlay, pygame.Color(theme['colour_2']), overlay.get_rect(), border_radius=20, width=2)

        title = self.title_font.render('Navigation Help', True, pygame.Color(theme['colour_3']))
        overlay.blit(title, (padding, padding))

        controls = self.launcher.controlls_data
        lines = [
            f"Move: {pygame.key.name(controls['up']).upper()}, {pygame.key.name(controls['down']).upper()}, {pygame.key.name(controls['left']).upper()}, {pygame.key.name(controls['right']).upper()}",
            f"Select: {pygame.key.name(controls['action_a']).upper()}",
            f"Back: {pygame.key.name(controls['action_b']).upper()}",
            f"Sidebar: {pygame.key.name(controls['options']).upper()}",
        ]

        for index, text_line in enumerate(lines):
            rendered = self.body_font.render(text_line, True, pygame.Color('#D7D7E0'))
            overlay.blit(rendered, (padding, padding + 48 + index * 28))

        button_size = 52
        button_rect = pygame.Rect(w - padding - button_size, h - padding - button_size, button_size, button_size)
        pygame.draw.rect(overlay, pygame.Color(theme['colour_3']), button_rect, border_radius=14)
        r_text = self.action_font.render('R', True, pygame.Color(theme['colour_1']))
        r_rect = r_text.get_rect(center=button_rect.center)
        overlay.blit(r_text, r_rect)

        window.blit(overlay, (x, y))
