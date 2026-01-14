import pygame
from States.generic_state import BaseState
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.store_ui.store_entry import GameStatus # Importujemy statusy
from os import listdir
from os.path import join, isdir

class GamePreview(BaseState):
    def __init__(s, launcher):
        super().__init__(launcher)
        s.game_id = None
        s.data = {}
        s.screenshots = []
        s.status = GameStatus.NOT_INSTALLED # Domyślny status

    def setup(s, game_id, game_data):
        s.game_id = game_id
        s.data = game_data
        
        # LOGIKA STATUSU (analogiczna do tej ze Store)
        manifest_version = s.data.get('version')
        if not s.launcher.installer.is_installed(game_id):
            s.status = GameStatus.NOT_INSTALLED
        elif s.launcher.installer.has_update(game_id, manifest_version):
            s.status = GameStatus.UPDATE_AVAILABLE
        else:
            s.status = GameStatus.INSTALLED

        s.load_screenshots()

    def load_screenshots(s):
        s.screenshots.clear()
        path = join('assets', 'store_assets', s.game_id, 'screenshots')
        if isdir(path):
            files = [f for f in listdir(path) if f.endswith(('.png', '.jpg'))]
            for file in files:
                img = pygame.image.load(join(path, file)).convert_alpha()
                # Skalowanie zachowując proporcje (np. szerokość 640px)
                s.screenshots.append(pygame.transform.smoothscale(img, (640, 360)))
        
        if not s.screenshots:
            # Placeholder jeśli brak zdjęć
            placeholder = pygame.Surface((640, 360))
            placeholder.fill((50, 50, 50))
            s.screenshots.append(placeholder)

    def handling_events(s, events):
        keys = pygame.key.get_just_pressed()
        controlls = s.launcher.controlls_data # Skrót dla czytelności
        
        # Sprawdzaj akcje POZA jakimkolwiek 'if ui_focus', żeby zawsze reagowały
        if keys[controlls['action_b']] or keys[pygame.K_ESCAPE]:
            s.launcher.state_manager.set_state('Store')
            return # Przerywamy, żeby nie wykonać innych akcji naraz

        if keys[pygame.K_RETURN] or keys[controlls['action_a']]:
            if s.status != GameStatus.INSTALLED:
                s.install_logic()

    def install_logic(s):
        manifest_version = s.data.get("version")
        if s.status == GameStatus.NOT_INSTALLED:
            s.launcher.installer.install(s.game_id, s.data["repo"], manifest_version)
        elif s.status == GameStatus.UPDATE_AVAILABLE:
            s.launcher.installer.update(s.game_id, manifest_version)
    

    def draw(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])
        
        x_offset = s.launcher.sidebar.base_w + 50
        
        # 1. Nagłówek (Tytuł i Autor)
        font_big = pygame.font.SysFont(None, 120)
        font_mid = pygame.font.SysFont(None, 50)
        font_small = pygame.font.SysFont(None, 30)
        
        title_surf = font_big.render(s.data.get('name', 'Unknown'), True, theme['colour_2'])
        window.blit(title_surf, (x_offset, 50))
        
        author_surf = font_mid.render(f"By: {s.data.get('author')}", True, theme['colour_3'])
        window.blit(author_surf, (x_offset, 130))

        # 2. STATUS GRY (Tag graficzny)
        status_colors = {
            GameStatus.NOT_INSTALLED: (200, 50, 50),     # Czerwony
            GameStatus.UPDATE_AVAILABLE: (200, 150, 0), # Pomarańczowy
            GameStatus.INSTALLED: (50, 200, 50)          # Zielony
        }
        status_texts = {
            GameStatus.NOT_INSTALLED: "DOSTĘPNA DO POBRANIA",
            GameStatus.UPDATE_AVAILABLE: "DOSTĘPNA AKTUALIZACJA",
            GameStatus.INSTALLED: "GRA ZAINSTALOWANA"
        }
        
        status_color = status_colors.get(s.status, theme['colour_4'])
        status_text = status_texts.get(s.status, "")
        
        status_surf = font_mid.render(status_text, True, status_color)
        window.blit(status_surf, (WINDOW_WIDTH - status_surf.get_width() - 50, WINDOW_HEIGHT - 120))

        # 3. Screenshoty
        for i, img in enumerate(s.screenshots[:2]): # Wyświetlamy 2 obok siebie
            window.blit(img, (x_offset + i * 660, 220))

        # 4. Szczegóły (Rok, Wersja itd.)
        details_y = 620
        details = [
            f"Wersja: {s.data.get('version')}",
            f"Gatunek: {s.data.get('game_type')}",
            f"Tagi: {', '.join(s.data.get('tags', []))}"
        ]
        
        for i, text in enumerate(details):
            d_surf = font_small.render(text, True, theme['colour_3'])
            window.blit(d_surf, (x_offset, details_y + i * 30))

        # 5. Opis
        desc_surf = font_mid.render(s.data.get('description', ''), True, theme['colour_4'])
        window.blit(desc_surf, (x_offset, 750))
        
        # 6. Stopka z dynamicznym napisem akcji
        action_hint = "[ENTER] - Pobierz" if s.status == GameStatus.NOT_INSTALLED else "[ENTER] - Aktualizuj"
        if s.status == GameStatus.INSTALLED: action_hint = "Gra jest gotowa!"
        
        hint = font_mid.render(f"{action_hint} | [B] - Powrót", True, theme['colour_2'])
        window.blit(hint, (x_offset, WINDOW_HEIGHT - 60))