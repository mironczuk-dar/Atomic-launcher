# IMPORTING LIBRARIES
import pygame
import math
import os
import subprocess
import sys

# IMPORTING FILES
from States.generic_state import BaseState
from settings import GAMES_DIR, BASE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.ui_elements.searchbar import SearchBar
from UI.ui_elements.game_icon import GameIcon
from UI.library_ui.bottombar import BottomBar
from UI.ui_elements.buttons import GenericToggleButton, ImageToggleButton
from UI.library_ui.navigation_tutorial import NavigationTutorial

# IMPORTING TOOLS
from Tools.data_loading_tools import load_data


class Library(BaseState):
    def __init__(s, launcher):
        super().__init__(launcher)

        # LOADING IN GAMES MANIFEST
        s.manifest_path = os.path.join(BASE_DIR, 'src', 'Manifests', 'games_manifest.json')
        s.manifest = load_data(s.manifest_path, {})

        # LOGIC ATTRIBUTES
        s.game_library = []
        s.game_icons = {}
        s.title_fonts = {}
        s.filtered_games = []
        s.selected_index = 0
        s.show_favorites_only = False
        s.control_filter = 'all'  # one of 'all', 'keyboard', 'mouse'
        s.topbar_focus = False 
        s.topbar_index = 0  # 0 = Searchbar, 1 = Favorites Button, 2 = Keyboard Filter, 3 = Mouse Filter
        s.navigation_tutorial = NavigationTutorial(launcher)

        # LIBRARY UI ELEMENTS
        # SearchBar handles its own internal Keyboard instance
        s.searchbar = SearchBar(
            launcher,
            on_change=s.apply_search_filter,
            width=int(WINDOW_WIDTH * 0.4),
            height=int(WINDOW_HEIGHT * 0.1),
            y=int(WINDOW_HEIGHT * 0.03),
            x=int(WINDOW_WIDTH * 0.5) - int((WINDOW_WIDTH * 0.4) // 2)
        )

        # FAVORITES + CONTROL FILTER BUTTONS
        btn_w = int(WINDOW_WIDTH * 0.10)
        # Positioned to the right of the searchbar
        btn_x = s.searchbar.custom_x + s.searchbar.w + 150
        btn_y = s.searchbar.custom_y + s.searchbar.h // 2
        btn_h = int(s.searchbar.h // 2)

        def scale_icon(raw_img):
            raw_w, raw_h = raw_img.get_size()
            scale = min(btn_w / raw_w, btn_h / raw_h)
            return pygame.transform.smoothscale(raw_img, (max(1, int(raw_w * scale)), max(1, int(raw_h * scale))))

        def make_icon_images(raw_img):
            idle = scale_icon(raw_img)
            hover = idle.copy()
            active = idle.copy()
            tint = pygame.Surface(idle.get_size(), pygame.SRCALPHA)
            tint.fill((255, 255, 255, 100))
            active.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            return idle, hover, active

        # Load favorites and control filter icons
        try:
            off_img_path = os.path.join(BASE_DIR, 'assets', 'favorites_filter_off_icon.png')
            on_img_path = os.path.join(BASE_DIR, 'assets', 'favorites_filter_on_icon.png')
            highlight_img_path = os.path.join(BASE_DIR, 'assets', 'favorites_filter_highlight_icon.png')
            keyboard_off_img_path = os.path.join(BASE_DIR, 'assets', 'keyboard_filter_off_icon.png')
            keyboard_on_img_path = os.path.join(BASE_DIR, 'assets', 'keyboard_icon.png')
            keyboard_highlight_img_path = os.path.join(BASE_DIR, 'assets', 'keyboard_filter_highlight_icon.png')
            mouse_off_img_path = os.path.join(BASE_DIR, 'assets', 'mouse_filter_off_icon.png')
            mouse_on_img_path = os.path.join(BASE_DIR, 'assets', 'mouse_icon.png')
            mouse_highlight_img_path = os.path.join(BASE_DIR, 'assets', 'mouse_filter_highlight_icon.png')

            raw_off = pygame.image.load(off_img_path).convert_alpha()
            raw_on = pygame.image.load(on_img_path).convert_alpha()
            raw_high = pygame.image.load(highlight_img_path).convert_alpha()
            raw_keyboard_off = pygame.image.load(keyboard_off_img_path).convert_alpha()
            raw_keyboard_on = pygame.image.load(keyboard_on_img_path).convert_alpha()
            raw_keyboard_high = pygame.image.load(keyboard_highlight_img_path).convert_alpha()
            raw_mouse_off = pygame.image.load(mouse_off_img_path).convert_alpha()
            raw_mouse_on = pygame.image.load(mouse_on_img_path).convert_alpha()
            raw_mouse_high = pygame.image.load(mouse_highlight_img_path).convert_alpha()
        except Exception:
            raw_off = None
            raw_on = None
            raw_high = None
            raw_keyboard_off = None
            raw_keyboard_on = None
            raw_keyboard_high = None
            raw_mouse_off = None
            raw_mouse_on = None
            raw_mouse_high = None

        if raw_off and raw_on:
            off_img = scale_icon(raw_off)
            hover_img = off_img.copy()
            active_img = scale_icon(raw_on)

            s.fav_toggle = ImageToggleButton(
                launcher,
                pos=(btn_x, btn_y),
                idle_img=off_img,
                hover_img=hover_img,
                active_img=active_img,
                text="",
                text_size=30,
                action=s.toggle_favorites_filter
            )

            if raw_high:
                highlight_max_w = int(max(off_img.get_width(), active_img.get_width()) * 1.3)
                highlight_max_h = int(max(off_img.get_height(), active_img.get_height()) * 1.3)
                rh_w, rh_h = raw_high.get_size()
                high_scale = min(highlight_max_w / rh_w, highlight_max_h / rh_h)
                h_w = max(1, int(rh_w * high_scale))
                h_h = max(1, int(rh_h * high_scale))
                s.fav_highlight_image = pygame.transform.smoothscale(raw_high, (h_w, h_h))
            else:
                s.fav_highlight_image = None
        else:
            s.fav_toggle = GenericToggleButton(
                launcher,
                size=(btn_w, btn_h),
                pos=(btn_x, btn_y),
                text="Favorites",
                text_size=30,
                active_colour=(0,255,0),
                inactive_colour=(255,0,0),
                action=s.toggle_favorites_filter
            )
            s.fav_toggle.set_theme_colours(use_theme=True)
            s.fav_highlight_image = None

        key_btn_x = btn_x + btn_w -50
        mouse_btn_x = key_btn_x + btn_w - 50

        if raw_keyboard_off and raw_keyboard_on and raw_mouse_off and raw_mouse_on:
            kb_idle = scale_icon(raw_keyboard_off)
            kb_hover = kb_idle.copy()
            kb_active = scale_icon(raw_keyboard_on)
            mouse_idle = scale_icon(raw_mouse_off)
            mouse_hover = mouse_idle.copy()
            mouse_active = scale_icon(raw_mouse_on)

            s.keyboard_filter_toggle = ImageToggleButton(
                launcher,
                pos=(key_btn_x, btn_y),
                idle_img=kb_idle,
                hover_img=kb_hover,
                active_img=kb_active,
                text="",
                text_size=30,
                action=lambda: s.set_control_filter('keyboard')
            )

            s.mouse_filter_toggle = ImageToggleButton(
                launcher,
                pos=(mouse_btn_x, btn_y),
                idle_img=mouse_idle,
                hover_img=mouse_hover,
                active_img=mouse_active,
                text="",
                text_size=30,
                action=lambda: s.set_control_filter('mouse')
            )

            if raw_keyboard_high:
                highlight_max_w = int(max(kb_idle.get_width(), kb_active.get_width()) * 1.3)
                highlight_max_h = int(max(kb_idle.get_height(), kb_active.get_height()) * 1.3)
                rh_w, rh_h = raw_keyboard_high.get_size()
                high_scale = min(highlight_max_w / rh_w, highlight_max_h / rh_h)
                h_w = max(1, int(rh_w * high_scale))
                h_h = max(1, int(rh_h * high_scale))
                s.keyboard_highlight_image = pygame.transform.smoothscale(raw_keyboard_high, (h_w, h_h))
            else:
                s.keyboard_highlight_image = None

            if raw_mouse_high:
                highlight_max_w = int(max(mouse_idle.get_width(), mouse_active.get_width()) * 1.3)
                highlight_max_h = int(max(mouse_idle.get_height(), mouse_active.get_height()) * 1.3)
                rh_w, rh_h = raw_mouse_high.get_size()
                high_scale = min(highlight_max_w / rh_w, highlight_max_h / rh_h)
                h_w = max(1, int(rh_w * high_scale))
                h_h = max(1, int(rh_h * high_scale))
                s.mouse_highlight_image = pygame.transform.smoothscale(raw_mouse_high, (h_w, h_h))
            else:
                s.mouse_highlight_image = None
        else:
            s.keyboard_filter_toggle = GenericToggleButton(
                launcher,
                size=(btn_w, btn_h),
                pos=(key_btn_x, btn_y),
                text="Keyboard",
                text_size=24,
                action=lambda: s.set_control_filter('keyboard')
            )
            s.keyboard_filter_toggle.set_theme_colours(use_theme=True)

            s.mouse_filter_toggle = GenericToggleButton(
                launcher,
                size=(btn_w, btn_h),
                pos=(mouse_btn_x, btn_y),
                text="Mouse",
                text_size=24,
                action=lambda: s.set_control_filter('mouse')
            )
            s.mouse_filter_toggle.set_theme_colours(use_theme=True)
            s.keyboard_highlight_image = None
            s.mouse_highlight_image = None

        # Small heart image placeholder (actual scaling done after layout attrs)
        s.fav_heart_image = None

        # Highlight animation timer
        s.fav_highlight_timer = 0.0

        s.bottombar = BottomBar(launcher, s)
        s.icon_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.05), bold=False)
        s.label_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.020), bold=False)
        s.filter_label_progress = {
            'favorites': 0.0,
            'keyboard': 0.0,
            'mouse': 0.0,
        }

        # LAYOUT ATTRIBUTES
        s.icon_w = int(WINDOW_WIDTH * 0.2)
        s.spacing = 60
        s.scroll_speed = 8
        s.current_scroll = 0
        s.icon_group = pygame.sprite.Group()

        # Now that `s.icon_w` is known, prepare the heart image if available
        if 'raw_on' in locals() and raw_on:
            # Scale heart image to fit within a square of size (heart_max, heart_max) preserving aspect ratio
            heart_max = int(s.icon_w * 0.2)
            raw_w, raw_h = raw_on.get_size()
            heart_scale = min(heart_max / raw_w, heart_max / raw_h)
            new_w = max(1, int(raw_w * heart_scale))
            new_h = max(1, int(raw_h * heart_scale))
            s.fav_heart_image = pygame.transform.smoothscale(raw_on, (new_w, new_h))

    def _load_game_title_font(s, game_id):
        font_dir = os.path.join(BASE_DIR, 'assets', 'store_assets', game_id, 'fonts')
        if os.path.isdir(font_dir):
            candidates = ['title.ttf', 'title_font.ttf', 'custom_title.ttf', 'custom_title_font.ttf']
            for filename in candidates:
                font_path = os.path.join(font_dir, filename)
                if os.path.isfile(font_path):
                    try:
                        return pygame.font.Font(font_path, int(WINDOW_WIDTH * 0.05))
                    except Exception as e:
                        print(f"Failed to load custom font for {game_id}: {e}")
        return None

    def toggle_favorites_filter(s):
        """Callback for the fav_toggle button."""
        s.show_favorites_only = s.fav_toggle.is_on
        s.apply_search_filter(s.searchbar.text)

    def set_control_filter(s, filter_name):
        if filter_name == 'keyboard':
            if s.keyboard_filter_toggle.is_on:
                s.mouse_filter_toggle.is_on = False
                s.control_filter = 'keyboard'
            else:
                s.control_filter = 'all'
        elif filter_name == 'mouse':
            if s.mouse_filter_toggle.is_on:
                s.keyboard_filter_toggle.is_on = False
                s.control_filter = 'mouse'
            else:
                s.control_filter = 'all'

        s.apply_search_filter(s.searchbar.text)

    def handling_events(s, events):
        controlls = s.launcher.controlls_data
        
        # --- NEW EVENT-BASED LOGIC ---
        for event in events:
            if event.type == pygame.KEYDOWN:
                key = event.key

                if s.navigation_tutorial.is_active():
                    if s.navigation_tutorial.handle_input(events):
                        return

                if s.searchbar.active:
                    s.searchbar.handle_events(events)
                    return

                if s.bottombar.visible:
                    s.bottombar.handling_events(events)
                    return

                if s.launcher.state_manager.ui_focus != 'content':
                    return

                # 3. TOPBAR NAVIGATION
                if s.topbar_focus:
                    s.fav_toggle.is_selected = (s.topbar_index == 1)
                    s.keyboard_filter_toggle.is_selected = (s.topbar_index == 2)
                    s.mouse_filter_toggle.is_selected = (s.topbar_index == 3)

                    if key == controlls['keyboard']['down']:
                        s.topbar_focus = False
                        s.fav_toggle.is_selected = False
                        s.keyboard_filter_toggle.is_selected = False
                        s.mouse_filter_toggle.is_selected = False
                    elif key == controlls['keyboard']['left']:
                        s.topbar_index = (s.topbar_index - 1) % 4
                    elif key == controlls['keyboard']['right']:
                        s.topbar_index = (s.topbar_index + 1) % 4
                    if key == pygame.K_RETURN or key == controlls['keyboard']['action_a']:
                        if s.topbar_index == 0:
                            s.searchbar.open_keyboard()
                        elif s.topbar_index == 1:
                            s.fav_toggle.toggle()
                        elif s.topbar_index == 2:
                            s.keyboard_filter_toggle.toggle()
                        elif s.topbar_index == 3:
                            s.mouse_filter_toggle.toggle()
                    return

                # 4. CONTENT NAVIGATION
                if key == controlls['keyboard']['action_b'] and len(s.game_library) != 0:
                    s.bottombar.open_bottombar()
                    return

                if key == controlls['keyboard']['left']:
                    if s.selected_index == 0:
                        s.launcher.state_manager.ui_focus = "sidebar"
                    else:
                        s.selected_index -= 1
                elif key == controlls['keyboard']['right']:
                    s.selected_index = min(len(s.filtered_games) - 1, s.selected_index + 1)
                elif key == pygame.K_RETURN or key == controlls['keyboard']['action_a']:
                    s.launch_game()
                elif key == controlls['keyboard']['up']:
                    s.topbar_focus = True

    def update(s, delta_time):
        super().update(delta_time)
        s.current_scroll += (s.selected_index - s.current_scroll) * s.scroll_speed * delta_time

        try:
            s.fav_toggle.is_selected = (s.topbar_focus and s.topbar_index == 1)
            s.keyboard_filter_toggle.is_selected = (s.topbar_focus and s.topbar_index == 2)
            s.mouse_filter_toggle.is_selected = (s.topbar_focus and s.topbar_index == 3)
        except Exception:
            pass

        s.fav_toggle.update(delta_time)
        s.keyboard_filter_toggle.update(delta_time)
        s.mouse_filter_toggle.update(delta_time)

        for key, toggle in [('favorites', s.fav_toggle), ('keyboard', s.keyboard_filter_toggle), ('mouse', s.mouse_filter_toggle)]:
            target = 1.0 if toggle.is_on else 0.0
            progress = s.filter_label_progress[key]
            progress += (target - progress) * min(10.0, 12.0 * delta_time)
            s.filter_label_progress[key] = 0.0 if abs(progress) < 0.01 else progress

        s.navigation_tutorial.update(delta_time)
        # Update highlight timer for pulsing effect
        s.fav_highlight_timer += delta_time

    def draw(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])

        s.draw_game_icons_titles(window)
        s.bottombar.draw(window)
        
        # Draw Searchbar (focused if topbar_index is 0)
        search_focused = (s.topbar_focus and s.topbar_index == 0)
        s.searchbar.draw(window, focused=search_focused)

        # Draw pulsing highlight behind the favorites or control filter toggles when selected
        freq = 2.0
        alpha = int((0.5 + 0.5 * math.sin(2 * math.pi * freq * s.fav_highlight_timer)) * (220 - 80) + 80)

        if getattr(s.fav_toggle, 'is_selected', False) and getattr(s, 'fav_highlight_image', None):
            hi = s.fav_highlight_image.copy()
            hi.set_alpha(alpha)
            rect = hi.get_rect(center=s.fav_toggle.rect.center)
            window.blit(hi, rect)

        if getattr(s.keyboard_filter_toggle, 'is_selected', False) and getattr(s, 'keyboard_highlight_image', None):
            hi = s.keyboard_highlight_image.copy()
            hi.set_alpha(alpha)
            rect = hi.get_rect(center=s.keyboard_filter_toggle.rect.center)
            window.blit(hi, rect)

        if getattr(s.mouse_filter_toggle, 'is_selected', False) and getattr(s, 'mouse_highlight_image', None):
            hi = s.mouse_highlight_image.copy()
            hi.set_alpha(alpha)
            rect = hi.get_rect(center=s.mouse_filter_toggle.rect.center)
            window.blit(hi, rect)

        # Draw the Favorites and control filter buttons
        s.fav_toggle.draw(window)
        s.keyboard_filter_toggle.draw(window)
        s.mouse_filter_toggle.draw(window)

        # Draw slide-out labels under active toggles
        for label_text, button, key in [
            ("Favorites", s.fav_toggle, 'favorites'),
            ("Keyboard", s.keyboard_filter_toggle, 'keyboard'),
            ("Mouse", s.mouse_filter_toggle, 'mouse'),
        ]:
            progress = s.filter_label_progress[key]
            if progress > 0.01:
                text_surf = s.label_font.render(label_text, True, theme['colour_3'])
                text_width, text_height = text_surf.get_size()
                x = button.rect.centerx - text_width // 2
                y = button.rect.bottom + int((1.0 - progress) * 16) + 8
                alpha = int(progress * 255)

                bg = pygame.Surface((text_width + 12, text_height + 8), pygame.SRCALPHA)
                bg.fill((0, 0, 0, 120))
                bg.set_alpha(alpha)
                window.blit(bg, (x - 6, y - 4))

                label_image = text_surf.copy()
                label_image.set_alpha(alpha)
                window.blit(label_image, (x, y))

        s.navigation_tutorial.draw(window)

        super().draw(window)

    def draw_game_icons_titles(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        if not s.filtered_games:
            msg = s.icon_font.render("NO GAMES INSTALLED", True, theme['colour_2'])
            rect = msg.get_rect(center=((WINDOW_WIDTH + s.launcher.sidebar.base_w) // 2, WINDOW_HEIGHT // 2))
            window.blit(msg, rect)
            return

        sidebar_w = s.launcher.sidebar.base_w
        workspace_center_x = sidebar_w + (WINDOW_WIDTH - sidebar_w) // 2
        center_y = WINDOW_HEIGHT // 2
        favorites = s.launcher.game_library_data.get('favorites', [])

        for i, folder_name in enumerate(s.filtered_games):
            icon = s.game_icons.get(folder_name)
            if not icon: continue

            offset = (i - s.current_scroll) * (s.icon_w + s.spacing)
            x = workspace_center_x + offset
            y = center_y

            icon.set_position(x, y)
            icon.set_selected(i == s.selected_index)
            icon.draw(window)

            if folder_name in favorites:
                if getattr(s, 'fav_heart_image', None):
                    heart_img = s.fav_heart_image
                    heart_rect = heart_img.get_rect(topright=(x + s.icon_w // 2 - 10, y - s.icon_w // 2 + 10))
                    window.blit(heart_img, heart_rect)
                else:
                    heart = s.icon_font.render("<3", True, (255, 60, 60)) 
                    heart_rect = heart.get_rect(topright=(x + s.icon_w // 2 - 10, y - s.icon_w // 2 + 10))
                    window.blit(heart, heart_rect)

            if i == s.selected_index:
                display_name = s.get_game_display_name(folder_name)
                
                # Fetch custom font, fallback to default icon_font if None
                font_to_use = s.title_fonts.get(folder_name) or s.icon_font
                
                # Render using our chosen font
                text = font_to_use.render(display_name.upper(), True, theme['colour_3'])
                text_rect = text.get_rect(center=(x, y - s.icon_w // 2 - 60))
                window.blit(text, text_rect)

    def get_game_display_name(self, folder_name):
        game_data = self.manifest.get(folder_name)
        if game_data and "name" in game_data:
            return game_data["name"]
        return folder_name.replace("_", " ").title()

    def get_game_library(s):
        s.manifest = load_data(s.manifest_path, {})
        if not os.path.exists(GAMES_DIR):
            os.makedirs(GAMES_DIR)
            s.game_library = []
        else:
            s.game_library = [
                name for name in os.listdir(GAMES_DIR)
                if os.path.isdir(os.path.join(GAMES_DIR, name))
            ]

        for game in s.game_library:
            s.game_icons[game] = GameIcon(
                launcher=s.launcher,
                groups=s.icon_group,
                game_id=game,
                size=s.icon_w,
                path=os.path.join(BASE_DIR, 'assets', 'store_assets', game, 'icon')
            )
            s.title_fonts[game] = s._load_game_title_font(game)
        s.apply_search_filter(s.searchbar.text)

    def apply_search_filter(s, query):
        query = query.lower()
        s.filtered_games = []
        favorites = s.launcher.game_library_data.get('favorites', [])
        
        for game_name in s.game_library:
            if s.show_favorites_only and game_name not in favorites:
                continue

            game_data = s.manifest.get(game_name, {})
            controls = game_data.get('controls', '').lower()
            if s.control_filter == 'keyboard' and controls != 'keyboard':
                continue
            if s.control_filter == 'mouse' and controls != 'mouse':
                continue
                
            display_name = s.get_game_display_name(game_name)
            if not query or query in display_name.lower():
                s.filtered_games.append(game_name)
        s.selected_index = 0

    def on_enter(self):
        self.get_game_library()

    def launch_game(self):
        if not self.filtered_games: return
        folder_name = self.filtered_games[self.selected_index]
        game_path = os.path.join(GAMES_DIR, folder_name, 'code')
        game_data = self.manifest.get(folder_name, {})
        main_file = game_data.get("main.py", "main.py") 
        full_path = os.path.join(game_path, main_file)

        if not os.path.exists(full_path): return

        try:
            self.launcher.game_process = subprocess.Popen(
                [sys.executable, full_path],
                cwd=game_path,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
            )            
            self.launcher.game_running = True 
            
            # --- NEW: Pause the launcher music ---
            self.launcher.audio_manager.pause_music()
            
        except Exception as e:
            print(f"Failed to start: {e}")
            return

        perf_data = self.launcher.performance_settings_data
        if perf_data.get('turn_off_launcher_when_game_active'):
            pygame.quit()
            sys.exit()