import pygame
from States.generic_state import BaseState
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.store_ui.store_entry import GameStatus
from UI.store_ui.progress_bar import Bar  # Upewnij się, że ścieżka jest poprawna
from os import listdir
import threading
from os.path import join, isdir

class GamePreview(BaseState):
    def __init__(s, launcher):
        super().__init__(launcher)
        s.game_id = None
        s.data = {}
        s.screenshots = []
        s.status = GameStatus.NOT_INSTALLED
        
        # Inicjalizacja paska (pozycja x, y, szerokość, wysokość)
        # Ustawiamy go w prawym dolnym rogu, tam gdzie komunikat "Downloading"
        s.progress_bar = Bar(0, 0, 300, 20) 

    def setup(s, game_id, game_data):
        """Metoda przygotowująca dane przed wyświetleniem podstrony."""
        s.game_id = game_id
        s.data = game_data
        s.check_status()
        s.load_screenshots()

    def check_status(s):
        """Sprawdza aktualny stan gry na dysku i aktualizuje status."""
        manifest_version = s.data.get('version')
        if not s.launcher.installer.is_installed(s.game_id):
            s.status = GameStatus.NOT_INSTALLED
        elif s.launcher.installer.has_update(s.game_id, manifest_version):
            s.status = GameStatus.UPDATE_AVAILABLE
        else:
            s.status = GameStatus.INSTALLED

    def load_screenshots(s):
        """Ładuje screenshoty i dopasowuje je do 16:9 zachowując proporcje."""
        s.screenshots.clear()
        path = join('assets', 'store_assets', s.game_id, 'screenshots')
        
        target_w, target_h = 640, 360
        target_ratio = target_w / target_h

        if isdir(path):
            files = [f for f in listdir(path) if f.endswith(('.png', '.jpg', '.jpeg'))]
            for file in files:
                try:
                    img = pygame.image.load(join(path, file)).convert_alpha()
                    img_w, img_h = img.get_size()
                    img_ratio = img_w / img_h

                    surface = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
                    
                    if abs(img_ratio - target_ratio) < 0.01:
                        final_img = pygame.transform.smoothscale(img, (target_w, target_h))
                        surface.blit(final_img, (0, 0))
                    else:
                        if img_ratio > target_ratio:
                            new_w = target_w
                            new_h = int(target_w / img_ratio)
                        else:
                            new_h = target_h
                            new_w = int(target_h * img_ratio)
                        
                        scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
                        rect = scaled_img.get_rect(center=(target_w // 2, target_h // 2))
                        surface.blit(scaled_img, rect)

                    s.screenshots.append(surface)
                except Exception as e:
                    print(f"Błąd ładowania obrazu {file}: {e}")
        
        if not s.screenshots:
            placeholder = pygame.Surface((target_w, target_h))
            placeholder.fill((40, 40, 40))
            s.screenshots.append(placeholder)

    def handling_events(s, events):
        keys = pygame.key.get_just_pressed()
        controlls = s.launcher.controlls_data
        
        if keys[controlls['action_b']] or keys[pygame.K_ESCAPE]:
            s.launcher.state_manager.set_state('Store')
            return

        if keys[pygame.K_RETURN] or keys[controlls['action_a']]:
            if s.status != GameStatus.INSTALLED:
                s.install_logic()

    def install_logic(s):
        if s.launcher.installer.is_downloading:
            return

        manifest_version = s.data.get("version")
        
        def run_in_background():
            if s.status == GameStatus.NOT_INSTALLED:
                s.launcher.installer.install(s.game_id, s.data["repo"], manifest_version)
            elif s.status == GameStatus.UPDATE_AVAILABLE:
                s.launcher.installer.update(s.game_id, manifest_version)
            s.check_status()

        download_thread = threading.Thread(target=run_in_background, daemon=True)
        download_thread.start()

    def draw_wrapped_text(s, window, text, font, color, rect):
        words = text.split(' ')
        space_w, _ = font.size(' ')
        max_width, max_height = rect.size
        x, y = rect.topleft
        
        line = ""
        for word in words:
            word_surface = font.render(word, True, color)
            word_w, word_h = word_surface.get_size()
            if x + word_w >= rect.left + max_width:
                window.blit(font.render(line, True, color), (rect.left, y))
                line = word + " "
                x = rect.left + word_w + space_w
                y += word_h
            else:
                line += word + " "
                x += word_w + space_w
        window.blit(font.render(line, True, color), (rect.left, y))

    def get_status_surface(s):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        font_mid = pygame.font.SysFont(None, 45)

        status_map = {
            GameStatus.NOT_INSTALLED: ("DOWNLOAD FOR FREE", (220, 60, 60)),
            GameStatus.UPDATE_AVAILABLE: ("UPDATE AVAILABLE", (220, 160, 40)),
            GameStatus.INSTALLED: ("INSTALLED", (60, 220, 60))
        }
        
        text, color = status_map.get(s.status, ("STATUS NIEZNANY", theme['colour_4']))
        return font_mid.render(text, True, color)

    def draw(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])
        
        x_offset = s.launcher.sidebar.base_w + 50
        is_busy = s.launcher.installer.is_downloading
        
        font_big = pygame.font.SysFont(None, 110)
        font_mid = pygame.font.SysFont(None, 45)
        font_small = pygame.font.SysFont(None, 28)
        
        # --- 1. Nagłówek ---
        title_surf = font_big.render(s.data.get('name', 'Gra'), True, theme['colour_2'])
        window.blit(title_surf, (x_offset, 40))
        
        author_surf = font_mid.render(f"Autor: {s.data.get('author')}", True, theme['colour_3'])
        window.blit(author_surf, (x_offset, 125))

        # --- 2. Status i Bar Pobierania ---
        if is_busy:
            # Pobieramy aktualny procent z instalatora
            progress_val = s.launcher.installer.download_progress
            
            # Napis DOWNLOADING z dynamicznym procentem
            loading_text = f"DOWNLOADING... {progress_val}%"
            loading_surf = font_mid.render(loading_text, True, (255, 255, 0))
            
            text_x = WINDOW_WIDTH - loading_surf.get_width() - 50
            text_y = WINDOW_HEIGHT - 130
            window.blit(loading_surf, (text_x, text_y))
            
            # Konfiguracja i rysowanie PASKA
            # Szerokość paska ustawiamy na stałą (np. 300px), żeby nie skakała przy zmianie cyfr
            bar_width = 300
            s.progress_bar.rect.width = bar_width
            s.progress_bar.rect.topright = (WINDOW_WIDTH - 50, text_y + 45) # Wyrównanie do prawej
            s.progress_bar.bar_color = (255, 255, 0) 
            
            s.progress_bar.set_progress(progress_val) 
            s.progress_bar.draw(window)
        else:
            status_surf = s.get_status_surface()
            window.blit(status_surf, (WINDOW_WIDTH - status_surf.get_width() - 50, WINDOW_HEIGHT - 130))

        # --- 3. Screenshoty ---
        for i, img in enumerate(s.screenshots[:2]):
            window.blit(img, (x_offset + i * 660, 200))

        # --- 4. Szczegóły techniczne ---
        details_y = 590
        info_list = [
            f"VERSION: {s.data.get('version', '1.0.0')}",
            f"TYPE: {s.data.get('game_type', 'N/A')}",
            f"TAGS: {', '.join(s.data.get('tags', []))}"
        ]
        for i, text in enumerate(info_list):
            surf = font_small.render(text, True, theme['colour_3'])
            window.blit(surf, (x_offset, details_y + i * 28))

        # --- 5. Opis ---
        desc_rect = pygame.Rect(x_offset, 720, WINDOW_WIDTH - x_offset - 100, 200)
        s.draw_wrapped_text(window, s.data.get('description', ''), font_mid, theme['colour_4'], desc_rect)
        
        # --- 6. Stopka ---
        if is_busy:
            action_hint = "Downloading in progress... | [B] Back"
        else:
            if s.status == GameStatus.INSTALLED:
                action_text = "Gra gotowa do uruchomienia"
            elif s.status == GameStatus.UPDATE_AVAILABLE:
                action_text = "[ENTER] Update"
            else:
                action_text = "[ENTER] Download"
            action_hint = f"{action_text} | [B] Back"
            
        hint_surf = font_mid.render(action_hint, True, theme['colour_2'])
        window.blit(hint_surf, (x_offset, WINDOW_HEIGHT - 60))