import pygame
from os.path import join
import math

from settings import BASE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY, get_contrast_text_color
from UI.store_ui.store_entry import StoreEntry, GameStatus
from UI.store_ui.feature_frame import FeatureFrame
from UI.searchbar import SearchBar
from UI.store_ui.progress_bar import Bar
from States.generic_state import BaseState
from Tools.data_loading_tools import load_data
from Tools.asset_importing_tool import import_image


class Store(BaseState):
    def __init__(s, launcher):
        super().__init__(launcher)
        launcher.store = s
        
        # INTERNET
        s.online = launcher.online_mode

        # SEARCHBAR
        # SearchBar now handles internal keyboard logic and typing state[cite: 16]
        s.search_query = ""
        s.searchbar = SearchBar(
            launcher,
            on_change = s.on_search_change,
            width = 500,
            height = 60
        )

        # CATEGORY TABS
        s.tabs = ["All", "Arcade", "Adventure & RPG", "Cozy", "Horror"]
        s.selected_tab_index = 0

        # SORTING
        s.sort_mode = "A-Z"

        s.header_h = 40
        s.tabs_y = 55
        s.store_top = 95
        s.feature_frame_height = 420
        s.entry_height = 190
        s.spacing = 20

        # GRID SETTINGS
        s.columns = 2
        s.entry_height = 200
        s.spacing = 25

        # DATA
        s.manifest = {}
        s.all_games = []
        s.filtered_games = []
        s.entries = []

        s.selected_index = 0
        s.scroll = 0
        s.target_scroll = 0 
        s.focus_order = ["searchbar", "featured", "tabs", "content", "download"]
        s.icon_cache = {}
        s.text_font = pygame.font.SysFont(None, 28)
        s.small_font = pygame.font.SysFont(None, 20)
        s.tab_font = pygame.font.SysFont(None, 26, bold=True)
        s.info_font = pygame.font.SysFont(None, 24)

        # LOAD MANIFEST
        s.manifest_path = join(BASE_DIR, 'code', 'Store', 'games_manifest.json')
        s.manifest = load_data(s.manifest_path, {})
        s.feature_frame_height = 520
        s.feature_frame = FeatureFrame(launcher, s.manifest)

        s.was_downloading = False

    def update_statuses(s):
        for entry in s.entries:
            game_id = entry.game_id
            data = s.manifest[game_id]
            manifest_version = data.get('version')

            if s.launcher.installer.is_downloading and s.launcher.installer.current_game_id == game_id:
                entry.status = GameStatus.DOWNLOADING
            elif any(q[0] == game_id for q in s.launcher.installer.download_queue):
                entry.status = GameStatus.QUEUED
            elif not s.launcher.installer.is_installed(game_id):
                entry.status = GameStatus.NOT_INSTALLED
            elif s.launcher.installer.has_update(game_id, manifest_version):
                entry.status = GameStatus.UPDATE_AVAILABLE
            else:
                entry.status = GameStatus.INSTALLED

    def draw_download_panel(s, window, theme):
        if not (s.launcher.installer.is_downloading or s.launcher.installer.download_queue):
            return

        x_start = s.launcher.sidebar.base_w + 40
        y_current = 5

        # Current downloading
        if s.launcher.installer.is_downloading:
            current_id = s.launcher.installer.current_game_id
            icon = s._get_cached_icon(current_id, 45)
            if icon:
                window.blit(icon, (x_start, y_current))

            # Title
            title_surf = s.text_font.render(s.manifest[current_id]['name'], True, theme['colour_3'])
            window.blit(title_surf, (x_start + 70, y_current + 10))

            # Progress bar
            bar_x = x_start + 70
            bar_y = y_current + 45
            bar = Bar(bar_x, bar_y, 200, 20)
            bar.set_progress(s.launcher.installer.download_progress)
            bar.draw(window)

            # Cancel button
            cancel_x = bar_x + 220
            cancel_y = bar_y - 5
            s.cancel_rect = pygame.Rect(cancel_x, cancel_y, 60, 30)
            pygame.draw.rect(window, (200, 50, 50), s.cancel_rect, border_radius=5)
            if s.launcher.state_manager.ui_focus == "download":
                pygame.draw.rect(window, theme['colour_2'], s.cancel_rect, 3, border_radius=7)
            cancel_surf = s.small_font.render("Cancel", True, (255, 255, 255))
            window.blit(cancel_surf, cancel_surf.get_rect(center=s.cancel_rect.center))

        # Next in queue
        if s.launcher.installer.download_queue:
            next_x = x_start + 500 if s.launcher.installer.is_downloading else x_start
            next_id = s.launcher.installer.download_queue[0][0]
            icon = s._get_cached_icon(next_id, 30)
            if icon:
                window.blit(icon, (next_x, y_current))

            # Title
            next_surf = s.info_font.render(f"Next: {s.manifest[next_id]['name']}", True, theme['colour_3'])
            window.blit(next_surf, (next_x + 40, y_current + 5))

    def _get_cached_icon(s, game_id, size):
        cache_key = (game_id, size)
        if cache_key in s.icon_cache:
            return s.icon_cache[cache_key]

        icon_path = join(BASE_DIR, 'assets', 'store_assets', game_id, 'icon')
        try:
            icon = import_image(icon_path)
            icon = pygame.transform.smoothscale(icon, (size, size))
            s.icon_cache[cache_key] = icon
            return icon
        except Exception:
            s.icon_cache[cache_key] = None
            return None

    def on_search_change(s, query):
        s.search_query = query
        s.apply_filters()

    def apply_filters(s):
        if not s.online:
            return

        query = s.search_query.lower()
        active_tab = s.tabs[s.selected_tab_index]

        s.filtered_games = []

        for game_id in s.all_games:
            data = s.manifest[game_id]
            name = data.get('name', '').lower()
            tags = data.get('tags', [])

            if query and query not in name:
                continue

            if active_tab == "Arcade" and "arcade" not in tags:
                continue
            if active_tab == "Adventure & RPG" and not any(t in tags for t in ["adventure", "rpg"]):
                continue
            if active_tab == "Cozy" and "cozzy" not in tags:
                continue
            if active_tab == "Horror" and "horror" not in tags:
                continue

            s.filtered_games.append(game_id)

        if s.sort_mode == "A-Z":
            s.filtered_games.sort(key=lambda gid: s.manifest[gid]['name'])
        else:
            s.filtered_games.sort(key=lambda gid: s.manifest[gid]['name'], reverse=True)

        s.selected_index = 0
        s.target_scroll = 0
        s.scroll = 0
        s.load_store_entries()

    def load_store_entries(s):
        s.entries.clear()

        if not s.online:
            return

        fixed_sidebar_w = s.launcher.sidebar.base_w
        panel_padding = 40
        available_width = WINDOW_WIDTH - fixed_sidebar_w - (panel_padding * 2)
        entry_width = (available_width - s.spacing) // s.columns

        start_x = fixed_sidebar_w + panel_padding
        start_y = s.store_top + (s.feature_frame_height if s.selected_tab_index == 0 else 0) + 20

        for i, game_id in enumerate(s.filtered_games):
            data = s.manifest[game_id]
            manifest_version = data.get('version')

            if s.launcher.installer.is_downloading and s.launcher.installer.current_game_id == game_id:
                status = GameStatus.DOWNLOADING
            elif any(q[0] == game_id for q in s.launcher.installer.download_queue):
                status = GameStatus.QUEUED
            elif not s.launcher.installer.is_installed(game_id):
                status = GameStatus.NOT_INSTALLED
            elif s.launcher.installer.has_update(game_id, manifest_version):
                status = GameStatus.UPDATE_AVAILABLE
            else:
                status = GameStatus.INSTALLED

            row = i // s.columns
            col = i % s.columns

            x = start_x + col * (entry_width + s.spacing)
            y = start_y + row * (s.entry_height + s.spacing)

            entry = StoreEntry(
                launcher=s.launcher,
                game_id=game_id,
                game_data=data,
                status=status,
                size=(entry_width, s.entry_height),
                position=(x, y)
            )

            s.entries.append(entry)

    def handling_events(s, events):
        keys = pygame.key.get_just_pressed()
        state_manager = s.launcher.state_manager
        controlls = getattr(s.launcher, 'controlls_data', {})
        
        action_confirm = keys[controlls['keyboard'].get('action_a', pygame.K_RETURN)] or keys[pygame.K_RETURN]
        action_back = keys[controlls['keyboard'].get('action_b', pygame.K_ESCAPE)] or keys[pygame.K_ESCAPE]
        
        btn_left = controlls['keyboard'].get('left', pygame.K_LEFT)
        btn_right = controlls['keyboard'].get('right', pygame.K_RIGHT)
        btn_up = controlls['keyboard'].get('up', pygame.K_UP)
        btn_down = controlls['keyboard'].get('down', pygame.K_DOWN)

        # Check if download panel is physically visible
        is_downloading_active = s.launcher.installer.is_downloading or s.launcher.installer.download_queue

        # 1. SEARCHBAR FOCUS (Top Right)
        if state_manager.ui_focus == "searchbar":
            if s.searchbar.active:
                if s.searchbar.handle_events(events):
                    state_manager.ui_focus = "tabs"
                elif action_back:
                    s.searchbar.active = False
                    state_manager.ui_focus = "tabs"
                return

            if action_confirm:
                s.searchbar.open_keyboard()
                return
            if keys[btn_left] and is_downloading_active:
                state_manager.ui_focus = "download"
                return
            if keys[btn_down]:
                state_manager.ui_focus = "tabs"
                return

        # 2. DOWNLOAD FOCUS (Top Left)
        elif state_manager.ui_focus == "download":
            if action_confirm and s.launcher.installer.is_downloading:
                s.launcher.installer.cancel_download()
                return
            if keys[btn_right]:
                state_manager.ui_focus = "searchbar"
                return
            if keys[btn_down]:
                state_manager.ui_focus = "tabs"
                return
            if action_back:
                state_manager.ui_focus = "searchbar"
                return

        # 3. TABS FOCUS (Second Row)
        elif state_manager.ui_focus == "tabs":
            if keys[btn_left] and s.selected_tab_index > 0:
                s.selected_tab_index -= 1
                s.apply_filters()
                return
            if keys[btn_right] and s.selected_tab_index < len(s.tabs) - 1:
                s.selected_tab_index += 1
                s.apply_filters()
                return
            if keys[btn_up]:
                state_manager.ui_focus = "download" if is_downloading_active else "searchbar"
                return
            if keys[btn_down]:
                state_manager.ui_focus = "featured" if s.selected_tab_index == 0 else "content"
                return
            if action_confirm:
                state_manager.ui_focus = "featured" if s.selected_tab_index == 0 else "content"
                return
            if action_back:
                state_manager.ui_focus = "searchbar"
                return

        # 4. FEATURED FOCUS (Third Row)
        elif state_manager.ui_focus == "featured":
            if keys[btn_left]:
                s.feature_frame.previous()
                return
            if keys[btn_right]:
                s.feature_frame.next()
                return
            if keys[btn_up]:
                state_manager.ui_focus = "tabs"
                return
            if keys[btn_down] and s.entries:
                state_manager.ui_focus = "content"
                return
            if action_confirm:
                s.enter_game_preview()
                return
            if action_back:
                state_manager.ui_focus = "tabs"
                return

        # 5. CONTENT GRID FOCUS (Bottom Row)
        elif state_manager.ui_focus == "content":
            if action_back:
                state_manager.ui_focus = "featured"
                return
            if keys[btn_left]:
                if s.selected_index % s.columns != 0:
                    s.selected_index -= 1
                return
            if keys[btn_right]:
                # Move right only if it doesn't cross into the next row visually
                if (s.selected_index + 1) % s.columns != 0 and s.selected_index + 1 < len(s.entries):
                    s.selected_index += 1
                return
            if keys[btn_up]:
                if s.selected_index < s.columns:
                    state_manager.ui_focus = "featured" if s.selected_tab_index == 0 else "tabs"
                else:
                    s.selected_index -= s.columns
                return
            if keys[btn_down] and s.selected_index + s.columns < len(s.entries):
                s.selected_index += s.columns
                return
            if action_confirm:
                s.enter_game_preview()
                return

        # Global Hotkeys
        if keys[pygame.K_s]:
            s.sort_mode = "Z-A" if s.sort_mode == "A-Z" else "A-Z"
            s.apply_filters()

        s.handle_mouse_events(events)

    def handle_mouse_events(s, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if hasattr(s, 'cancel_rect') and s.cancel_rect.collidepoint(event.pos):
                    s.launcher.installer.cancel_download()

                if s.selected_tab_index == 0:
                    clicked_nav = s.feature_frame.handle_mouse_event(event)
                    if not clicked_nav and s.feature_frame.frame_rect.collidepoint(event.pos):
                        s.enter_game_preview()

    def update(s, delta_time):
        super().update(delta_time)
        s.feature_frame.update(delta_time)
        if not s.online or not s.entries:
            return

        # Check if downloading status changed
        current_downloading = s.launcher.installer.is_downloading
        if current_downloading != s.was_downloading:
            s.was_downloading = current_downloading
            if not current_downloading:
                s.update_statuses()

        # ---------- UNIFIED SCROLLING LOGIC ----------
        view_top = s.store_top
        view_bottom = WINDOW_HEIGHT - 20

        # Prevent featured focus when the featured frame is not visible
        if s.launcher.state_manager.ui_focus == "featured" and s.selected_tab_index != 0:
            s.launcher.state_manager.ui_focus = "content" if s.entries else "tabs"

        # Jump to top if focused on featured
        if s.launcher.state_manager.ui_focus == "featured":
            s.target_scroll = 0
            
        elif s.launcher.state_manager.ui_focus == "content":
            row = s.selected_index // s.columns
            start_y = s.store_top + (s.feature_frame_height if s.selected_tab_index == 0 else 0) + 20
            current_y = start_y + row * (s.entry_height + s.spacing)

            # Track where the entry is visually on the screen
            entry_screen_top = current_y - s.target_scroll
            entry_screen_bottom = entry_screen_top + s.entry_height

            # Push camera down or up to keep the entry in the view bounds
            if entry_screen_bottom > view_bottom:
                s.target_scroll = current_y + s.entry_height - view_bottom
            if entry_screen_top < view_top:
                s.target_scroll = current_y - view_top

        # Clamp max scroll so we don't scroll into the void
        s.target_scroll = max(0, s.target_scroll)
        total_rows = math.ceil(len(s.entries) / s.columns)
        
        # Total height now includes featured frame if visible + content grid + padding
        feature_offset = s.feature_frame_height if s.selected_tab_index == 0 else 0
        total_content_height = feature_offset + 40 + (total_rows * (s.entry_height + s.spacing))
        max_scroll = max(0, total_content_height - (WINDOW_HEIGHT - s.store_top))
        s.target_scroll = min(s.target_scroll, max_scroll)

        # Smooth scrolling application
        lerp_speed = min(1.0, 15 * delta_time) if delta_time < 1.0 else 0.15
        s.scroll += (s.target_scroll - s.scroll) * lerp_speed
        if abs(s.target_scroll - s.scroll) < 0.5:
            s.scroll = s.target_scroll

    def draw(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])

        # ---------- HEADER ----------
        header_h = s.header_h
        pygame.draw.rect(window, theme['colour_4'], (s.launcher.sidebar.base_w, 0, WINDOW_WIDTH, header_h))

        # Download panel
        s.draw_download_panel(window, theme)

        # ---------- TABS ----------
        s.draw_tabs(window, theme)

        # ---------- LEGEND & CONTROLS ----------
        controls_text = f"Hotkeys: [TAB] Sidebar | [E] Back | [R] Details | [S] Sort: {s.sort_mode}"
        sort_text = s.info_font.render(controls_text, True, theme['colour_4'])
        text_x = WINDOW_WIDTH - sort_text.get_width() - 120
        window.blit(sort_text, (text_x, s.tabs_y + 20))

        # ==========================================
        #        UNIFIED SCROLLABLE VIEW AREA
        # ==========================================
        view_top = s.store_top
        view_rect = pygame.Rect(
            s.launcher.sidebar.base_w,
            view_top,
            WINDOW_WIDTH - s.launcher.sidebar.base_w,
            WINDOW_HEIGHT - view_top
        )
        
        # Apply clip to the whole lower screen
        window.set_clip(view_rect)

        # 1. Draw Feature Frame inside scroll area (pass the scroll offset)
        if s.selected_tab_index == 0:
            s.feature_frame.draw(window, theme, scroll_offset=s.scroll)

        # 2. Draw Content Grid Panel
        total_rows = math.ceil(len(s.entries) / s.columns)
        grid_height = (total_rows * (s.entry_height + s.spacing)) + 40
        
        # Stretch background panel to bottom if there are barely any games
        min_panel_height = WINDOW_HEIGHT - (view_top + (s.feature_frame_height if s.selected_tab_index == 0 else 0) + 20)
        panel_h = max(grid_height, min_panel_height)

        panel_top = view_top + (s.feature_frame_height if s.selected_tab_index == 0 else 0) + 20 - s.scroll
        panel_rect = pygame.Rect(
            s.launcher.sidebar.base_w + 20,
            panel_top,
            WINDOW_WIDTH - s.launcher.sidebar.base_w - 40,
            panel_h
        )

        pygame.draw.rect(window, theme['colour_4'], panel_rect, border_radius=16)
        pygame.draw.rect(window, theme['colour_3'], panel_rect, 2, border_radius=16)

        # 3. Draw Entries inside the panel
        for i, entry in enumerate(s.entries):
            selected = i == s.selected_index and s.launcher.state_manager.ui_focus == "content"
            row = i // s.columns
            start_y = view_top + (s.feature_frame_height if s.selected_tab_index == 0 else 0) + 20
            original_y = start_y + row * (s.entry_height + s.spacing) + 20 # 20 is inner top padding
            
            # Translate position based on scroll
            entry.rect.top = original_y - s.scroll

            # Performance check: Only draw if it intersects the physical view area
            if entry.rect.bottom > view_rect.top and entry.rect.top < view_rect.bottom:
                entry.draw(window)
                if selected:
                    highlight = entry.rect.inflate(14, 14)
                    pygame.draw.rect(window, theme['colour_2'], highlight, 8, border_radius=14)

        # 4. Draw Custom Scrollbar mapping the unified height
        total_content_height = (s.feature_frame_height if s.selected_tab_index == 0 else 0) + 20 + grid_height
        if total_content_height > view_rect.height:
            scrollbar_w = 8
            visible_ratio = view_rect.height / total_content_height
            scrollbar_h = max(40, view_rect.height * visible_ratio)
            max_scroll = total_content_height - view_rect.height
            scroll_progress = s.scroll / max_scroll if max_scroll > 0 else 0
            
            scrollbar_y = view_rect.top + 5 + scroll_progress * (view_rect.height - scrollbar_h - 10)
            scrollbar_x = view_rect.right - 15
            
            # Track
            track_rect = pygame.Rect(scrollbar_x, view_rect.top + 5, scrollbar_w, view_rect.height - 10)
            pygame.draw.rect(window, theme['colour_1'], track_rect, border_radius=4)
            # Handle
            scroll_rect = pygame.Rect(scrollbar_x, scrollbar_y, scrollbar_w, scrollbar_h)
            pygame.draw.rect(window, theme['colour_2'], scroll_rect, border_radius=4)

        # Lift the clip rect so UI overlays (like the search drop down) draw correctly
        window.set_clip(None)

        # ---------- SEARCH BAR (DRAWN LAST) ----------
        s.searchbar.custom_x = WINDOW_WIDTH - 600
        s.searchbar.custom_y = 10
        search_focused = s.launcher.state_manager.ui_focus == "searchbar"
        s.searchbar.draw(window, focused=search_focused)

        super().draw(window)

    def draw_tabs(s, window, theme):
        font = s.tab_font
        x = s.launcher.sidebar.base_w + 40
        y = s.tabs_y

        for i, tab in enumerate(s.tabs):
            active = i == s.selected_tab_index
            focused = s.launcher.state_manager.ui_focus == "tabs"

            bg_color = theme['colour_2'] if active else theme['colour_4']
            text_color = bg_color
            text = font.render(tab, True, text_color)

            rect = pygame.Rect(x, y, text.get_width() + 32, text.get_height() + 16)

            if active:
                pygame.draw.rect(window, theme['colour_2'], rect, 3, border_radius=20)
            else:
                pygame.draw.rect(window, theme['colour_3'], rect, 2, border_radius=20)

            if active and focused:
                pygame.draw.rect(window, theme['colour_4'], rect.inflate(6, 6), 4, border_radius=22)

            window.blit(text, (rect.x + 16, rect.y + 8))
            x += rect.width + 15

    def enter_game_preview(s):
        game_id = None
        game_data = None

        if s.launcher.state_manager.ui_focus == "featured":
            game_id, game_data = s.feature_frame.get_current_game()
            if not game_id:
                return
        else:
            if not s.entries:
                return
            entry = s.entries[s.selected_index]
            game_id = entry.game_id
            game_data = entry.game_data

        preview = s.launcher.state_manager.states.get('Game preview')
        if preview:
            preview.setup(game_id, game_data)
            s.launcher.state_manager.set_state('Game preview')

    def on_enter(s):
        s.launcher.online_mode = s.launcher.checking_internet_connection()
        s.online = s.launcher.online_mode
        s.manifest = load_data(s.manifest_path, {})
        s.feature_frame.refresh(s.manifest)
        s.selected_index = 0
        s.launcher.state_manager.ui_focus = "featured"
        if s.online:
            s.all_games = list(s.manifest.keys())
            s.apply_filters()