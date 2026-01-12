import pygame
from States.generic_state import BaseState
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY

class Options(BaseState):
    def __init__(self, launcher):
        super().__init__(launcher)

        # -------------------
        # TABS
        # -------------------
        self.tabs = ["Controls", "Video", "Themes"]
        self.tab_index = 0

        # Czcionki
        self.title_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.06), bold=True)
        self.text_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.04))

        # -------------------
        # DUMMY SETTINGS
        # -------------------
        self.settings = {
            "Controls": {"Move Up": "W", "Move Down": "S", "Jump": "Space"},
            "Video": {"Resolution": "1920x1080", "Fullscreen": True},
            "Themes": {"Current Theme": self.launcher.theme_data['current_theme']}
        }

    # ===============================
    # EVENTS / INPUT
    # ===============================
    def handling_events(self, events):
        # Pobieramy skrót do managera, żeby kod był czytelniejszy
        sm = self.launcher.state_manager
        
        # Jeśli manager ma ustawiony focus na sidebar, ignorujemy klawisze w tym stanie
        if sm.ui_focus != "content":
            return

        keys = pygame.key.get_just_pressed()

        # ---- TABS NAVIGATION ----
        if keys[pygame.K_LEFT]:
            self.tab_index = (self.tab_index - 1) % len(self.tabs)
        elif keys[pygame.K_RIGHT]:
            self.tab_index = (self.tab_index + 1) % len(self.tabs)
        
        # Szybkie przejście do sidebaru strzałką (opcjonalnie, skoro TAB już działa globalnie)
        elif keys[pygame.K_ESCAPE]:
            sm.ui_focus = "sidebar"

    # ===============================
    # UPDATE
    # ===============================
    def update(self, delta):
        # Sidebar aktualizuje się sam w StateManagerze, tutaj tylko logika opcji
        # Możemy tu np. aktualizować dane motywów na bieżąco
        self.settings["Themes"]["Current Theme"] = self.launcher.theme_data['current_theme']

    # ===============================
    # DRAW
    # ===============================
    def draw(self, window):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        
        # Pobieramy stały base_w dla stabilnego layoutu
        sidebar_base_w = self.launcher.sidebar.base_w
        
        # Tło (rysowane pod sidebarem, bo StateManager rysuje sidebar na końcu)
        window.fill(theme['colour_1'])

        # ---- TABS ----
        tab_y = 40
        # Layout zaczyna się za "bazową" szerokością sidebaru
        tab_start_x = sidebar_base_w + 50
        
        for i, tab in enumerate(self.tabs):
            selected = i == self.tab_index
            color = theme['colour_3'] if selected else (120, 120, 120)
            
            # Dodajemy podkreślenie dla wybranego tabu
            text_surf = self.text_font.render(tab.upper(), True, color)
            x_pos = tab_start_x + i * 180
            window.blit(text_surf, (x_pos, tab_y))
            
            if selected:
                pygame.draw.rect(window, theme['colour_3'], (x_pos, tab_y + 35, text_surf.get_width(), 4))

        # ---- CONTENT ----
        content_y = 150
        content_x = sidebar_base_w + 70
        active_tab = self.tabs[self.tab_index]
        tab_settings = self.settings.get(active_tab, {})

        for i, (key, value) in enumerate(tab_settings.items()):
            line = f"{key}: {value}"
            text_surf = self.text_font.render(line, True, theme['colour_3'])
            window.blit(text_surf, (content_x, content_y + i * 50))
            
    def on_enter(self):
        # Resetujemy focus przy wejściu w opcje
        self.launcher.state_manager.ui_focus = "content"