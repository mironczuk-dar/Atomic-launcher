# IMPORTING LIBRARIES
import pygame
from os.path import join, isdir
from os import listdir

# IMPORTING FILES
from settings import BASE_DIR, THEME_LIBRARY, get_contrast_text_color, WINDOW_WIDTH, WINDOW_HEIGHT
from Tools.data_loading_tools import load_data
from Tools.asset_importing_tool import import_image


class FeatureFrame:
    def __init__(s, launcher, manifest):
        s.launcher = launcher
        s.manifest = manifest
        s.feature_data_path = join(BASE_DIR, 'code', 'Store', 'featured_games.json')
        s.featured_games = s._load_featured_games()
        s.current_index = 0
        s.slide_interval = 6.0
        s.slide_timer = 0.0
        s.screenshot_interval = 5.0
        s.screenshot_timer = 0.0
        s.left_rect = pygame.Rect(0, 0, 0, 0)
        s.right_rect = pygame.Rect(0, 0, 0, 0)
        s.frame_rect = pygame.Rect(0, 0, 0, 0)
        s.screenshots = {}
        s.current_screenshot_index = {}
        s.icon_cache = {}
        s.feature_reasons = {}
        s.scaled_screenshot_cache = {}
        s.title_font = pygame.font.SysFont(None, 48, bold=True)
        s.body_font = pygame.font.SysFont(None, 30)
        s.arrow_font = pygame.font.SysFont(None, 42, bold=True)
        s.label_font = pygame.font.SysFont(None, 28, bold=True)
        s.load_all_screenshots()

    def _load_featured_games(s):
        featured_data = load_data(s.feature_data_path, {})
        games_dict = featured_data.get('featured_games', {})
        s.feature_reasons = {}
        
        # Handle both old list format and new dict format
        if isinstance(games_dict, list):
            game_ids = [gid for gid in games_dict if gid in s.manifest]
        else:
            game_ids = []
            for item in games_dict.values():
                game_id = item.get('game')
                if game_id in s.manifest:
                    game_ids.append(game_id)
                    s.feature_reasons[game_id] = item.get('reason', '')
        
        return game_ids

    def load_all_screenshots(s):
        for game_id in s.featured_games:
            s._load_screenshots_for_game(game_id)
            s.current_screenshot_index[game_id] = 0

    def _load_screenshots_for_game(s, game_id):
        s.screenshots[game_id] = []
        path = join(BASE_DIR, 'assets', 'store_assets', game_id, 'screenshots')
        if isdir(path):
            files = sorted([f for f in listdir(path) if f.endswith(('.png', '.jpg', '.jpeg'))])
            for file in files:
                try:
                    img = import_image(join(BASE_DIR, 'assets', 'store_assets', game_id, 'screenshots', file), format='')
                    s.screenshots[game_id].append(img)
                except Exception:
                    pass

    def refresh(s, manifest):
        s.manifest = manifest
        s.featured_games = s._load_featured_games()
        s.current_index = min(s.current_index, len(s.featured_games) - 1) if s.featured_games else 0
        s.screenshot_timer = 0.0
        s.scaled_screenshot_cache.clear()
        s.load_all_screenshots()

    def update(s, delta_time):
        if not s.featured_games or not s.launcher.online_mode:
            return

        s.screenshot_timer += delta_time
        if s.screenshot_timer >= s.screenshot_interval:
            s.screenshot_timer -= s.screenshot_interval
            s._advance_screenshot()

    def next(s):
        if not s.featured_games:
            return
        s.current_index = (s.current_index + 1) % len(s.featured_games)
        s.screenshot_timer = 0.0
        current_game = s.featured_games[s.current_index]
        s.current_screenshot_index[current_game] = 0

    def previous(s):
        if not s.featured_games:
            return
        s.current_index = (s.current_index - 1) % len(s.featured_games)
        s.screenshot_timer = 0.0
        current_game = s.featured_games[s.current_index]
        s.current_screenshot_index[current_game] = 0

    def get_current_game(s):
        if not s.featured_games:
            return None, None
        game_id = s.featured_games[s.current_index]
        return game_id, s.manifest.get(game_id, {})

    def _advance_screenshot(s):
        if not s.featured_games:
            return
        game_id = s.featured_games[s.current_index]
        if game_id in s.screenshots and len(s.screenshots[game_id]) > 1:
            s.current_screenshot_index[game_id] = (s.current_screenshot_index[game_id] + 1) % len(s.screenshots[game_id])

    def handle_mouse_event(s, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return False

        if s.left_rect.collidepoint(event.pos):
            s.previous()
            return True
        elif s.right_rect.collidepoint(event.pos):
            s.next()
            return True

        return False

    def cycle_screenshot_forward(s):
        if not s.featured_games:
            return
        game_id = s.featured_games[s.current_index]
        if game_id in s.screenshots and len(s.screenshots[game_id]) > 0:
            s.current_screenshot_index[game_id] = (s.current_screenshot_index[game_id] + 1) % len(s.screenshots[game_id])
            s.slide_timer = 0.0

    def cycle_screenshot_backward(s):
        if not s.featured_games:
            return
        game_id = s.featured_games[s.current_index]
        if game_id in s.screenshots and len(s.screenshots[game_id]) > 0:
            s.current_screenshot_index[game_id] = (s.current_screenshot_index[game_id] - 1) % len(s.screenshots[game_id])
            s.slide_timer = 0.0

    def draw(s, window, theme, scroll_offset=0):
        if not s.featured_games or not s.launcher.online_mode:
            return

        # Available content area after sidebar
        content_left = s.launcher.sidebar.base_w
        content_width = window.get_width() - content_left

        # Desired feature frame size
        frame_w = content_width - 600  # 20px padding on both sides

        # Center frame inside remaining usable area
        frame_x = content_left + (content_width - frame_w) // 2

        # Vertical positioning
        frame_y = s.launcher.store.store_top - scroll_offset + 10
        frame_h = s.launcher.store.feature_frame_height

        # Final rect
        s.frame_rect = pygame.Rect(frame_x, frame_y, frame_w, frame_h)

        # Main frame background with subtle border
        pygame.draw.rect(window, theme['colour_1'], s.frame_rect, border_radius=24)
        pygame.draw.rect(window, theme['colour_3'], s.frame_rect, 3, border_radius=24)
        
        # Main frame background with subtle border
        pygame.draw.rect(window, theme['colour_1'], s.frame_rect, border_radius=24)
        pygame.draw.rect(window, theme['colour_3'], s.frame_rect, 3, border_radius=24)

        if s.launcher.state_manager.ui_focus == "featured":
            focus_border = s.frame_rect.inflate(12, 12)
            pygame.draw.rect(window, theme['colour_2'], focus_border, 4, border_radius=28)

        # Fill with screenshot as background
        game_id = s.featured_games[s.current_index]
        if game_id in s.screenshots and len(s.screenshots[game_id]) > 0:
            screenshot_idx = s.current_screenshot_index.get(game_id, 0)
            screenshot = s.screenshots[game_id][screenshot_idx]
            scaled_bg = s._get_cached_scaled_screenshot(game_id, screenshot_idx, screenshot, frame_w - 6, frame_h - 6)
            window.blit(scaled_bg, (frame_x + 3, frame_y + 3))

        # Vignette overlay (dark edges, lighter center)
        vignette = pygame.Surface((frame_w - 6, frame_h - 6), pygame.SRCALPHA)
        for y in range(frame_h - 6):
            alpha = int(150 * (abs(y - (frame_h - 6) / 2) / ((frame_h - 6) / 2)) ** 0.8)
            pygame.draw.line(vignette, (0, 0, 0, alpha), (0, y), (frame_w - 6, y))
        window.blit(vignette, (frame_x + 3, frame_y + 3))

        # Bottom gradient overlay (semi-transparent black gradient from top to bottom)
        gradient_height = 200
        bottom_gradient = pygame.Surface((frame_w - 6, gradient_height), pygame.SRCALPHA)
        for y in range(gradient_height):
            alpha = int(180 * (y / gradient_height))
            pygame.draw.line(bottom_gradient, (0, 0, 0, alpha), (0, y), (frame_w - 6, y))
        window.blit(bottom_gradient, (frame_x + 3, s.frame_rect.bottom - gradient_height - 3))

        # Bottom section: icon + reason text
        icon_size = 130
        icon_x = frame_x + 30
        icon_y = s.frame_rect.bottom - icon_size - 25

        # Draw icon with shadow and background
        shadow_offset = 8
        shadow_rect = pygame.Rect(icon_x - 12 + shadow_offset, icon_y - 12 + shadow_offset, icon_size + 24, icon_size + 24)
        pygame.draw.rect(window, (0, 0, 0, 100), shadow_rect, border_radius=18)
        
        icon_bg = pygame.Rect(icon_x - 12, icon_y - 12, icon_size + 24, icon_size + 24)
        pygame.draw.rect(window, theme['colour_1'], icon_bg, border_radius=18)
        pygame.draw.rect(window, theme['colour_2'], icon_bg, 3, border_radius=18)

        # Draw game icon with caching
        icon = s._get_cached_icon(game_id, icon_size)
        if icon:
            window.blit(icon, (icon_x, icon_y))
        else:
            pygame.draw.rect(window, theme['colour_3'], (icon_x, icon_y, icon_size, icon_size), border_radius=14)

        # Game name and reason text
        text_x = icon_x + icon_size + 35
        text_max_width = s.frame_rect.right - text_x - 30

        game_data = s.manifest.get(game_id, {})
        
        # Title with enhanced styling
        title_surf = s.title_font.render(game_data.get('name', 'Unknown Game'), True, theme['colour_2'])
        window.blit(title_surf, (text_x, icon_y + 5))

        # Reason text with better styling
        reason = s._get_reason_text(game_id)
        if reason:
            wrapped_reason = s._wrap_text(reason, s.body_font, text_max_width, max_lines=3)
            y = icon_y + 60
            text_color = (240, 240, 240)
            for line in wrapped_reason:
                line_surf = s.body_font.render(line, True, text_color)
                window.blit(line_surf, (text_x, y))
                y += line_surf.get_height() + 6

        # Navigation buttons with improved styling
        button_size = 65
        button_y = s.frame_rect.centery - button_size // 2
        s.left_rect = pygame.Rect(s.frame_rect.left + 10, button_y, button_size, button_size)
        s.right_rect = pygame.Rect(s.frame_rect.right - button_size - 10, button_y, button_size, button_size)

        # Draw buttons with shadow and hover effect
        for button_rect in [s.left_rect, s.right_rect]:
            # Shadow
            shadow_rect = button_rect.inflate(4, 4)
            shadow_rect.topleft = (button_rect.left + 3, button_rect.top + 3)
            pygame.draw.rect(window, (0, 0, 0, 80), shadow_rect, border_radius=16)
            
            # Button background
            pygame.draw.rect(window, theme['colour_2'], button_rect, border_radius=16)
            pygame.draw.rect(window, (255, 255, 255, 50), button_rect, 2, border_radius=16)

        left_surf = s.arrow_font.render('<', True, theme['colour_1'])
        right_surf = s.arrow_font.render('>', True, theme['colour_1'])
        window.blit(left_surf, left_surf.get_rect(center=s.left_rect.center))
        window.blit(right_surf, right_surf.get_rect(center=s.right_rect.center))

        # Indicator dots at top with enhanced styling
        dot_radius = 7
        total = len(s.featured_games)
        indicator_width = total * (dot_radius * 2 + 12) - 12
        indicator_x = s.frame_rect.centerx - indicator_width // 2
        indicator_y = s.frame_rect.bottom - 25

        for index in range(total):
            dot_x = indicator_x + index * (dot_radius * 2 + 12)
            if index == s.current_index:
                # Active dot with glow effect
                pygame.draw.circle(window, theme['colour_2'], (dot_x, indicator_y), dot_radius + 2, 1)
                pygame.draw.circle(window, theme['colour_2'], (dot_x, indicator_y), dot_radius)
            else:
                # Inactive dots
                pygame.draw.circle(window, theme['colour_3'], (dot_x, indicator_y), dot_radius)

        # "FEATURED" label in top-right
        label_text = s.label_font.render('FEATURED', True, theme['colour_2'])
        label_x = s.frame_rect.right - label_text.get_width() - 25
        label_y = s.frame_rect.top + 20
        window.blit(label_text, (label_x, label_y))

    def _get_reason_text(s, game_id):
        return s.feature_reasons.get(game_id, '')

    def _get_cached_icon(s, game_id, icon_size):
        cache_key = (game_id, icon_size)
        if cache_key in s.icon_cache:
            return s.icon_cache[cache_key]

        icon_path = join(BASE_DIR, 'assets', 'store_assets', game_id, 'icon')
        try:
            icon = import_image(icon_path)
            icon = pygame.transform.smoothscale(icon, (icon_size, icon_size))
            s.icon_cache[cache_key] = icon
            return icon
        except Exception:
            s.icon_cache[cache_key] = None
            return None

    def _get_cached_scaled_screenshot(s, game_id, screenshot_idx, img, target_w, target_h):
        cache_key = (game_id, screenshot_idx, target_w, target_h)
        if cache_key in s.scaled_screenshot_cache:
            return s.scaled_screenshot_cache[cache_key]

        scaled = s._scale_screenshot(img, target_w, target_h)
        s.scaled_screenshot_cache[cache_key] = scaled
        return scaled

    def _wrap_text(s, text, font, max_width, max_lines=4):
        words = text.split(' ')
        lines = []
        current = ''

        for word in words:
            test = (current + ' ' + word).strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                lines.append(current)
                current = word
                if len(lines) == max_lines:
                    break

        if current and len(lines) < max_lines:
            lines.append(current)

        if len(lines) == max_lines and ' '.join(words) != ' '.join(lines):
            while font.size(lines[-1] + '...')[0] > max_width and lines[-1]:
                lines[-1] = lines[-1][:-1]
            lines[-1] += '...'

        return lines

    def _scale_screenshot(s, img, target_w, target_h):
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

        