import pygame
import os
import shutil
import subprocess
import sys
import threading
import urllib.request
import json
import stat
from os import listdir
from os.path import join, isdir

from States.generic_state import BaseState
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY, BASE_DIR, GAMES_DIR, get_contrast_text_color
from UI.store_ui.store_entry import GameStatus
from UI.store_ui.progress_bar import Bar

def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

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
        if s.launcher.checking_internet_connection():
            threading.Thread(target=s.fetch_size, daemon=True).start()

    def fetch_size(s):
        try:
            repo_url = s.data['repo']
            # Extract owner/repo from https://github.com/owner/repo.git
            parts = repo_url.replace('https://github.com/', '').replace('.git', '').split('/')
            owner, repo = parts[0], parts[1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            with urllib.request.urlopen(api_url) as response:
                data = json.loads(response.read().decode())
                size_kb = data.get('size', 0)
                size_mb = size_kb / 1024
                s.data['size'] = f"{size_mb:.1f}"
        except Exception as e:
            print(f"Failed to fetch size for {s.game_id}: {e}")
            s.data['size'] = None

    def check_status(s):
        """Checks the current install/download state for the preview."""
        manifest_version = s.data.get('version')
        if s.launcher.installer.is_downloading and s.launcher.installer.current_game_id == s.game_id:
            s.status = GameStatus.DOWNLOADING
        elif any(q[0] == s.game_id for q in s.launcher.installer.download_queue):
            s.status = GameStatus.QUEUED
        elif not s.launcher.installer.is_installed(s.game_id):
            s.status = GameStatus.NOT_INSTALLED
        elif s.launcher.installer.has_update(s.game_id, manifest_version):
            s.status = GameStatus.UPDATE_AVAILABLE
        else:
            s.status = GameStatus.INSTALLED

    def load_screenshots(s):
        s.screenshots.clear()
        s.fullscreen_screenshots.clear()
        path = join(BASE_DIR, 'assets', 'store_assets', s.game_id, 'screenshots')
        
        # Calculate responsive dimensions
        # Sidebar is 10% of window width
        sidebar_w = int(WINDOW_WIDTH * 0.1)
        available_w = WINDOW_WIDTH - sidebar_w - 80  # 40px margins on each side
        
        # Screenshot panel takes 70% of available width, maintains 16:9 aspect ratio
        prev_w = int(available_w * 0.7)
        prev_h = int(prev_w * 9 / 16)
        
        fs_w = WINDOW_WIDTH - 100
        fs_h = WINDOW_HEIGHT - 150

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
        # 1. Get the control map once before the loop
        ctrl = s.launcher.controlls_data['keyboard']
        
        # 2. Iterate through ALL events to prevent dropping injected GPIO events
        for event in events:
            if event.type == pygame.KEYDOWN:
                current_key = event.key
                
                # 3. Map keys to logical actions
                is_up = current_key == ctrl['up']
                is_down = current_key == ctrl['down']
                is_left = current_key == ctrl['left']
                is_right = current_key == ctrl['right']
                is_confirm = current_key in [ctrl['action_a'], pygame.K_RETURN]
                is_back = current_key in [ctrl['action_b'], pygame.K_ESCAPE]

                # --- FULLSCREEN MODE LOGIC ---
                if s.is_fullscreen:
                    # Exit fullscreen with Back, Escape, or Space
                    if is_back or current_key == pygame.K_SPACE:
                        s.is_fullscreen = False
                    # Navigate screenshots while in fullscreen
                    elif is_left:
                        s.current_img_index = (s.current_img_index - 1) % len(s.screenshots)
                    elif is_right:
                        s.current_img_index = (s.current_img_index + 1) % len(s.screenshots)
                    
                    # Continue to the next event, bypassing standard preview logic
                    continue

                # --- STANDARD PREVIEW LOGIC ---
                
                # Vertical navigation (Actions list like "Play", "Uninstall", etc.)
                if is_up:
                    s.selection_index = (s.selection_index - 1) % len(s.actions)
                elif is_down:
                    s.selection_index = (s.selection_index + 1) % len(s.actions)
                
                # Horizontal navigation (Screenshot gallery)
                elif is_left:
                    s.current_img_index = (s.current_img_index - 1) % len(s.screenshots)
                elif is_right:
                    s.current_img_index = (s.current_img_index + 1) % len(s.screenshots)

                # Execution (Confirm action)
                elif is_confirm:
                    s.execute_action()

                # Back to Store/Library
                elif is_back:
                    s.launcher.state_manager.set_state('Store')

    def execute_action(s):
        action_label = s.actions[s.selection_index]
        
        if action_label == "INSTALL" or action_label == "UPDATE":
            s.install_logic()
        elif action_label == "CANCEL QUEUE":
            s.cancel_queue()
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
                shutil.rmtree(target_dir, onerror=remove_readonly)
                s.check_status()
                s.selection_index = 0 
            except Exception as e:
                print(f"Uninstall failed: {e}")

    def install_logic(s):
        # Check if already in queue or downloading
        if any(q[0] == s.game_id for q in s.launcher.installer.download_queue) or s.launcher.installer.is_downloading and s.launcher.installer.current_game_id == s.game_id:
            return
        s.launcher.installer.download_queue.append((s.game_id, s.data["repo"], s.data.get("version")))
        if not s.launcher.installer.is_downloading:
            s.launcher.installer.process_queue()

    def cancel_queue(s):
        s.launcher.installer.download_queue = [q for q in s.launcher.installer.download_queue if q[0] != s.game_id]
        s.selection_index = 0
        s.check_status()

    def draw_button(s, window, text, rect, theme, is_selected):
        is_danger = text == "UNINSTALL"
        
        if is_selected:
            # Selected buttons pop with the Primary Accent (colour_2)
            bg_color = (200, 50, 50) if is_danger else theme['colour_2']
            txt_color = get_contrast_text_color(bg_color)
        else:
            # Inactive buttons blend with the Panel Background (colour_4)
            bg_color = theme['colour_4']
            txt_color = get_contrast_text_color(bg_color)
        
        pygame.draw.rect(window, bg_color, rect, border_radius=10)
        # Border uses Secondary Accent (colour_3) for subtle definition
        pygame.draw.rect(window, theme['colour_3'], rect, 2, border_radius=10)
            
        font = pygame.font.SysFont(None, 28, bold=is_selected)
        surf = font.render(text, True, txt_color)
        window.blit(surf, surf.get_rect(center=rect.center))

    def draw(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        s.check_status()
        window.fill(theme['colour_1']) # Primary Background
        
        x_start = s.launcher.sidebar.base_w + 40
        is_busy = s.launcher.installer.is_downloading and s.launcher.installer.current_game_id == s.game_id
        
        # Calculate responsive dimensions
        sidebar_w = int(WINDOW_WIDTH * 0.1)
        available_w = WINDOW_WIDTH - sidebar_w - 80  # 40px margins on each side
        screenshot_w = int(available_w * 0.7)
        screenshot_h = int(screenshot_w * 9 / 16)
        
        # Dynamic Menu Logic
        if s.status == GameStatus.INSTALLED:
            s.actions = ["LAUNCH GAME", "VIEW GALLERY", "UNINSTALL", "BACK TO STORE"]
        elif s.status == GameStatus.UPDATE_AVAILABLE:
            s.actions = ["UPDATE", "LAUNCH GAME", "VIEW GALLERY", "UNINSTALL", "BACK TO STORE"]
        elif s.status == GameStatus.QUEUED:
            s.actions = ["CANCEL QUEUE", "VIEW GALLERY", "BACK TO STORE"]
        else:
            s.actions = ["INSTALL", "VIEW GALLERY", "BACK TO STORE"]

        if s.is_fullscreen:
            s._draw_fullscreen(window, theme, x_start)
            return

        # Queued state indicator
        if s.status == GameStatus.QUEUED:
            queued_font = pygame.font.SysFont(None, 30, bold=True)
            queued_surf = queued_font.render("QUEUED FOR DOWNLOAD", True, theme['colour_3'])
            window.blit(queued_surf, (x_start, 130))

        # 1. HEADER
        # Title uses Primary Accent (colour_2) for hierarchy
        title_font = pygame.font.SysFont(None, 70, bold=True)
        title_surf = title_font.render(s.data.get('name', 'Game'), True, theme['colour_2'])
        window.blit(title_surf, (x_start, 30))
        
        # Meta Info uses Secondary Accent (colour_3)
        meta_font = pygame.font.SysFont(None, 32)
        meta_text = f"AUTHOR: {s.data.get('author')}"
        meta_surf = meta_font.render(meta_text, True, theme['colour_3'])
        window.blit(meta_surf, (x_start, 90))

        # 2. SCREENSHOT PANEL
        panel_y = 140
        # Screenshot area uses the Secondary Background (colour_4)
        pygame.draw.rect(window, theme['colour_4'], (x_start, panel_y, screenshot_w, screenshot_h), border_radius=14)
        window.blit(s.screenshots[s.current_img_index], (x_start, panel_y))
        
        # Navigation Dots
        dot_x = x_start + screenshot_w // 2 - (len(s.screenshots) * 15) // 2
        for i in range(len(s.screenshots)):
            # Active indicator uses Accent 2, Inactive uses Accent 3
            color = theme['colour_2'] if i == s.current_img_index else theme['colour_3']
            pygame.draw.circle(window, color, (dot_x + i * 20, panel_y + screenshot_h + 17), 4)

        # 3. ACTION MENU
        menu_x = x_start + screenshot_w + 40
        btn_w = int(available_w * 0.25)
        btn_h = 50
        for i, action in enumerate(s.actions):
            rect = pygame.Rect(menu_x, panel_y + i * (btn_h + 12), btn_w, btn_h)
            s.draw_button(window, action, rect, theme, s.selection_index == i)

        # 6. DATA WINDOW
        data_y = panel_y + len(s.actions) * (btn_h + 12) + 50
        data_font = pygame.font.SysFont(None, 50)
        lines = [
            f"Game Type: {s.data.get('game_type', 'Unknown')}",
            f"Version: v{s.data.get('version', '1.0.0')}",
            f"Size: {s.data.get('size', 'Unknown')} MB" if s.data.get('size') else "Size: Unknown"
        ]
        for i, line in enumerate(lines):
            surf = data_font.render(line, True, theme['colour_3'])
            window.blit(surf, (menu_x, data_y + i * 45))

        # 4. DESCRIPTION
        desc_font = pygame.font.SysFont(None, 44)
        desc_rect = pygame.Rect(x_start, panel_y + screenshot_h + 60, screenshot_w, 100)
        # Description text uses high-contrast colour_4 or standard white
        s.draw_wrapped_text(window, s.data.get('description', ''), desc_font, (240, 240, 240), desc_rect)

        # 5. PROGRESS BAR
        if is_busy:
            prog = s.launcher.installer.download_progress
            s.progress_bar.rect = pygame.Rect(menu_x, panel_y + screenshot_h + 60, btn_w, 20)
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