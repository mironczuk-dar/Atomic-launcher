import pygame
import os
import shutil
import subprocess
import sys
import threading
from os import listdir
from os.path import join, isdir

from States.generic_state import BaseState
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY, BASE_DIR, GAMES_DIR
from UI.store_ui.store_entry import GameStatus
from UI.store_ui.progress_bar import Bar

class GamePreview(BaseState):
    def __init__(s, launcher):
        super().__init__(launcher)
        s.game_id = None
        s.data = {}
        s.screenshots = []
        s.fullscreen_screenshots = []
        s.status = GameStatus.NOT_INSTALLED
        s.progress_bar = Bar(0, 0, 300, 20) 
        
        s.current_img_index = 0
        s.is_fullscreen = False
        s.selection_index = 0
        s.actions = [] 

    def setup(s, game_id, game_data):
        s.game_id = game_id
        s.data = game_data
        s.current_img_index = 0
        s.is_fullscreen = False
        s.selection_index = 0
        s.check_status()
        s.load_screenshots()

    def check_status(s):
        """Checks if the game folder exists to determine installation status."""
        manifest_version = s.data.get('version')
        if not s.launcher.installer.is_installed(s.game_id):
            s.status = GameStatus.NOT_INSTALLED
        elif s.launcher.installer.has_update(s.game_id, manifest_version):
            s.status = GameStatus.UPDATE_AVAILABLE
        else:
            s.status = GameStatus.INSTALLED

    def load_screenshots(s):
        s.screenshots.clear()
        s.fullscreen_screenshots.clear()
        path = join(BASE_DIR, 'assets', 'store_assets', s.game_id, 'screenshots')
        
        prev_w, prev_h = 760, 428 
        fs_w, fs_h = WINDOW_WIDTH - 100, WINDOW_HEIGHT - 150

        if isdir(path):
            files = [f for f in sorted(listdir(path)) if f.endswith(('.png', '.jpg', '.jpeg'))]
            for file in files:
                try:
                    img = pygame.image.load(join(path, file)).convert_alpha()
                    s.screenshots.append(s._scale_image(img, prev_w, prev_h))
                    s.fullscreen_screenshots.append(s._scale_image(img, fs_w, fs_h))
                except Exception as e:
                    print(f"Error loading {file}: {e}")
        
        if not s.screenshots:
            placeholder = pygame.Surface((prev_w, prev_h))
            placeholder.fill((30, 30, 30))
            s.screenshots.append(placeholder)
            s.fullscreen_screenshots.append(s._scale_image(placeholder, fs_w, fs_h))

    def _scale_image(s, img, target_w, target_h):
        img_w, img_h = img.get_size()
        img_ratio = img_w / img_h
        target_ratio = target_w / target_h
        surface = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
        
        if img_ratio > target_ratio:
            new_w = target_w
            new_h = int(target_w / img_ratio)
        else:
            new_h = target_h
            new_w = int(target_h * img_ratio)
            
        scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
        rect = scaled_img.get_rect(center=(target_w // 2, target_h // 2))
        surface.blit(scaled_img, rect)
        return surface

    def handling_events(s, events):
        keys = pygame.key.get_just_pressed()
        controlls = s.launcher.controlls_data
        
        if s.is_fullscreen:
            if keys[controlls['action_b']] or keys[pygame.K_ESCAPE] or keys[pygame.K_SPACE]:
                s.is_fullscreen = False
            elif keys[controlls['left']]:
                s.current_img_index = (s.current_img_index - 1) % len(s.screenshots)
            elif keys[controlls['right']]:
                s.current_img_index = (s.current_img_index + 1) % len(s.screenshots)
            return

        if keys[controlls['up']]:
            s.selection_index = (s.selection_index - 1) % len(s.actions)
        elif keys[controlls['down']]:
            s.selection_index = (s.selection_index + 1) % len(s.actions)
        
        if keys[controlls['left']]:
            s.current_img_index = (s.current_img_index - 1) % len(s.screenshots)
        elif keys[controlls['right']]:
            s.current_img_index = (s.current_img_index + 1) % len(s.screenshots)

        if keys[pygame.K_RETURN] or keys[controlls['action_a']]:
            s.execute_action()

        if keys[controlls['action_b']] or keys[pygame.K_ESCAPE]:
            s.launcher.state_manager.set_state('Store')

    def execute_action(s):
        action_label = s.actions[s.selection_index]
        
        if action_label == "INSTALL" or action_label == "UPDATE":
            s.install_logic()
        elif action_label == "LAUNCH GAME":
            s.launch_game()
        elif action_label == "UNINSTALL":
            s.uninstall_game()
        elif action_label == "VIEW GALLERY":
            s.is_fullscreen = True
        elif action_label == "BACK TO STORE":
            s.launcher.state_manager.set_state('Store')

    def launch_game(s):
        game_path = join(GAMES_DIR, s.game_id, 'code')
        main_file = s.data.get("main.py", "main.py") 
        full_path = join(game_path, main_file)

        if not os.path.exists(full_path):
            return

        try:
            subprocess.Popen(
                [sys.executable, full_path],
                cwd=game_path,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
            )
            
            perf = s.launcher.performance_settings_data
            if perf.get('turn_off_launcher_when_game_active'):
                pygame.quit()
                sys.exit()
        except Exception as e:
            print(f"Failed to launch: {e}")

    def uninstall_game(s):
        target_dir = join(GAMES_DIR, s.game_id)
        if isdir(target_dir):
            try:
                shutil.rmtree(target_dir)
                s.check_status()
                s.selection_index = 0 
            except Exception as e:
                print(f"Uninstall failed: {e}")

    def install_logic(s):
        if s.launcher.installer.is_downloading: return
        manifest_version = s.data.get("version")
        
        def run_in_background():
            if s.status == GameStatus.NOT_INSTALLED:
                s.launcher.installer.install(s.game_id, s.data["repo"], manifest_version)
            elif s.status == GameStatus.UPDATE_AVAILABLE:
                s.launcher.installer.update(s.game_id, manifest_version)
            s.check_status()

        threading.Thread(target=run_in_background, daemon=True).start()

    def draw_button(s, window, text, rect, theme, is_selected):
        is_danger = text == "UNINSTALL"
        
        if is_selected:
            # Selected buttons pop with the Primary Accent (colour_2)
            bg_color = (200, 50, 50) if is_danger else theme['colour_2']
            txt_color = (255, 255, 255)
        else:
            # Inactive buttons blend with the Panel Background (colour_4)
            bg_color = theme['colour_4']
            txt_color = (200, 100, 100) if is_danger else theme['colour_3']
        
        pygame.draw.rect(window, bg_color, rect, border_radius=10)
        # Border uses Secondary Accent (colour_3) for subtle definition
        pygame.draw.rect(window, theme['colour_3'], rect, 2, border_radius=10)
            
        font = pygame.font.SysFont(None, 28, bold=is_selected)
        surf = font.render(text, True, txt_color)
        window.blit(surf, surf.get_rect(center=rect.center))

    def draw(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1']) # Primary Background
        
        x_start = s.launcher.sidebar.base_w + 40
        is_busy = s.launcher.installer.is_downloading
        
        # Dynamic Menu Logic
        if s.status == GameStatus.INSTALLED:
            s.actions = ["LAUNCH GAME", "VIEW GALLERY", "UNINSTALL", "BACK TO STORE"]
        elif s.status == GameStatus.UPDATE_AVAILABLE:
            s.actions = ["UPDATE", "LAUNCH GAME", "VIEW GALLERY", "UNINSTALL", "BACK TO STORE"]
        else:
            s.actions = ["INSTALL", "VIEW GALLERY", "BACK TO STORE"]

        if s.is_fullscreen:
            s._draw_fullscreen(window, theme, x_start)
            return

        # 1. HEADER
        # Title uses Primary Accent (colour_2) for hierarchy
        title_font = pygame.font.SysFont(None, 64, bold=True)
        title_surf = title_font.render(s.data.get('name', 'Game'), True, theme['colour_2'])
        window.blit(title_surf, (x_start, 30))
        
        # Meta Info uses Secondary Accent (colour_3)
        meta_font = pygame.font.SysFont(None, 24)
        meta_text = f"{s.data.get('author')}  |  {s.data.get('game_type')}  |  v{s.data.get('version')}"
        meta_surf = meta_font.render(meta_text, True, theme['colour_3'])
        window.blit(meta_surf, (x_start, 90))

        # 2. SCREENSHOT PANEL
        panel_y = 140
        # Screenshot area uses the Secondary Background (colour_4)
        pygame.draw.rect(window, theme['colour_4'], (x_start, panel_y, 760, 428), border_radius=14)
        window.blit(s.screenshots[s.current_img_index], (x_start, panel_y))
        
        # Navigation Dots
        dot_x = x_start + 380 - (len(s.screenshots) * 15) // 2
        for i in range(len(s.screenshots)):
            # Active indicator uses Accent 2, Inactive uses Accent 3
            color = theme['colour_2'] if i == s.current_img_index else theme['colour_3']
            pygame.draw.circle(window, color, (dot_x + i * 20, panel_y + 445), 4)

        # 3. ACTION MENU
        menu_x = x_start + 790
        btn_w, btn_h = 240, 50
        for i, action in enumerate(s.actions):
            rect = pygame.Rect(menu_x, panel_y + i * (btn_h + 12), btn_w, btn_h)
            s.draw_button(window, action, rect, theme, s.selection_index == i)

        # 4. DESCRIPTION
        desc_font = pygame.font.SysFont(None, 24)
        desc_rect = pygame.Rect(x_start, 600, 760, 100)
        # Description text uses high-contrast colour_4 or standard white
        s.draw_wrapped_text(window, s.data.get('description', ''), desc_font, (240, 240, 240), desc_rect)

        # 5. PROGRESS BAR
        if is_busy:
            prog = s.launcher.installer.download_progress
            s.progress_bar.rect = pygame.Rect(menu_x, 600, btn_w, 20)
            s.progress_bar.set_progress(prog)
            s.progress_bar.draw(window)

    def _draw_fullscreen(s, window, theme, x_offset):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 240))
        window.blit(overlay, (0, 0))
        fs_img = s.fullscreen_screenshots[s.current_img_index]
        img_rect = fs_img.get_rect(center=((WINDOW_WIDTH + x_offset)//2, WINDOW_HEIGHT // 2))
        window.blit(fs_img, img_rect)

    def draw_wrapped_text(s, window, text, font, color, rect):
        words = text.split(' ')
        space_w, _ = font.size(' ')
        x, y = rect.topleft
        line = ""
        for word in words:
            word_surf = font.render(word, True, color)
            if x + word_surf.get_width() >= rect.right:
                window.blit(font.render(line, True, color), (rect.left, y))
                line = word + " "
                x = rect.left + word_surf.get_width() + space_w
                y += word_surf.get_height() + 4
            else:
                line += word + " "
                x += word_surf.get_width() + space_w
        if line: window.blit(font.render(line, True, color), (rect.left, y))