"""Store state: UI for browsing and installing games from the store.

This module implements the `Store` state which displays store entries,
manages filtering/searching, shows the download queue, and integrates
with the launcher's installer subsystem.

Developer notes
- Manifests: store and game metadata live in `src/Manifests/games_manifest.json`.
- Assets: per-game assets (icons, fonts, images) live under
    `assets/store_assets/<game_id>/` (see `import_image` usage and
    `_get_cached_icon`).
- Installer integration: the active download/install state is provided
    by `launcher.installer`. Methods such as `update_statuses` and
    `draw_download_panel` read installer state and should remain
    synchronized with the installer API.
- UI components: this state composes `UI.store_ui.FeatureFrame`,
    `UI.store_ui.StoreEntry`, `UI.ui_elements.SearchBar`, and toggle
    buttons. See those modules when changing layout or behaviour.
- Focus and navigation: keyboard/controller focus is driven by
    `state_manager.ui_focus`. This state uses the focus set
    `['searchbar','filters','featured','tabs','content','download']` —
    update `state_manager` usage carefully when changing focus logic.

Quick developer tasks
- To add a new game: add an entry to the manifest and place assets in
    `assets/store_assets/<game_id>/` (icon, optional `fonts/`, etc.).
- To extend categories/tabs: update `self.tabs` and ensure the
    filtering logic in `apply_filters` supports the new tag names.
"""

import pygame
from os.path import join
import math

from settings import BASE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY, get_contrast_text_color
from UI.store_ui.store_entry import StoreEntry, GameStatus
from UI.store_ui.feature_frame import FeatureFrame
from UI.ui_elements.searchbar import SearchBar
from UI.store_ui.progress_bar import Bar
from UI.ui_elements.buttons import GenericToggleButton, ImageToggleButton
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
        s.control_filter = 'all'  # one of 'all', 'keyboard', 'mouse'
        s.filter_focus_index = 0  # 0 = keyboard, 1 = mouse, 2 = searchbar
        s.searchbar = SearchBar(
            launcher,
            on_change = s.on_search_change,
            width = 500,
            height = 60,
            x = WINDOW_WIDTH - 700,
            y = 10
        )

        s.keyboard_filter_toggle = None
        s.mouse_filter_toggle = None

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
        s.focus_order = ["searchbar", "filters", "featured", "tabs", "content", "download"]
        s.icon_cache = {}
        s.text_font = pygame.font.SysFont(None, 28)
        s.small_font = pygame.font.SysFont(None, 20)
        s.tab_font = pygame.font.SysFont(None, 26, bold=True)
        s.info_font = pygame.font.SysFont(None, 24)

        # LOAD MANIFEST
        s.manifest_path = join(BASE_DIR, 'src', 'Manifests', 'games_manifest.json')
        s.manifest = load_data(s.manifest_path, {})
        s.feature_frame_height = 520
        s.feature_frame = FeatureFrame(launcher, s.manifest)

        s._init_control_filters(launcher)
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
        y_current = 8

        # Current downloading
        if s.launcher.installer.is_downloading:
            current_id = s.launcher.installer.current_game_id
            icon = s._get_cached_icon(current_id, 34)
            if icon:
                window.blit(icon, (x_start, y_current))

            bar_x = x_start + 46
            bar_y = y_current + 8
            bar = Bar(bar_x, bar_y, 180, 16)
            bar.set_progress(s.launcher.installer.download_progress)
            bar.draw(window)

            cancel_x = bar_x + 190
            cancel_y = bar_y - 2
            s.cancel_rect = pygame.Rect(cancel_x, cancel_y, 48, 20)
            pygame.draw.rect(window, (200, 50, 50), s.cancel_rect, border_radius=4)
            if s.launcher.state_manager.ui_focus == "download":
                pygame.draw.rect(window, theme['colour_2'], s.cancel_rect, 2, border_radius=6)
            cancel_surf = s.small_font.render("X", True, (255, 255, 255))
            window.blit(cancel_surf, cancel_surf.get_rect(center=s.cancel_rect.center))

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

    def _init_control_filters(s, launcher):
        btn_w = int(WINDOW_WIDTH * 0.07)
        btn_h = int(40)
        btn_gap = 14
        base_x = s.searchbar.custom_x - (btn_w * 2 + btn_gap)
        btn_y = s.searchbar.custom_y + s.searchbar.h // 2

        def scale_icon(raw_img):
            raw_w, raw_h = raw_img.get_size()
            scale = min(btn_w / raw_w, btn_h / raw_h)
            return pygame.transform.smoothscale(raw_img, (max(1, int(raw_w * scale)), max(1, int(raw_h * scale))))

        try:
            kb_off = pygame.image.load(join(BASE_DIR, 'assets', 'keyboard_filter_off_icon.png')).convert_alpha()
            kb_on = pygame.image.load(join(BASE_DIR, 'assets', 'keyboard_icon.png')).convert_alpha()
            kb_high = pygame.image.load(join(BASE_DIR, 'assets', 'keyboard_filter_highlight_icon.png')).convert_alpha()
            mouse_off = pygame.image.load(join(BASE_DIR, 'assets', 'mouse_filter_off_icon.png')).convert_alpha()
            mouse_on = pygame.image.load(join(BASE_DIR, 'assets', 'mouse_icon.png')).convert_alpha()
            mouse_high = pygame.image.load(join(BASE_DIR, 'assets', 'mouse_filter_highlight_icon.png')).convert_alpha()
        except Exception:
            kb_off = kb_on = kb_high = mouse_off = mouse_on = mouse_high = None

        if kb_off and kb_on:
            kb_idle = scale_icon(kb_off)
            kb_hover = kb_idle.copy()
            kb_active = scale_icon(kb_on)
            kb_highlight = None
            if kb_high:
                highlight_max_w = int(max(kb_idle.get_width(), kb_active.get_width()) * 1.3)
                highlight_max_h = int(max(kb_idle.get_height(), kb_active.get_height()) * 1.3)
                rh_w, rh_h = kb_high.get_size()
                high_scale = min(highlight_max_w / rh_w, highlight_max_h / rh_h)
                h_w = max(1, int(rh_w * high_scale))
                h_h = max(1, int(rh_h * high_scale))
                kb_highlight = pygame.transform.smoothscale(kb_high, (h_w, h_h))

            s.keyboard_filter_toggle = ImageToggleButton(
                launcher,
                pos=(base_x + btn_w // 2, btn_y),
                idle_img=kb_idle,
                hover_img=kb_hover,
                active_img=kb_active,
                highlight_img=kb_highlight,
                text="",
                text_size=24,
                action=lambda: s.set_control_filter('keyboard')
            )
        else:
            s.keyboard_filter_toggle = GenericToggleButton(
                launcher,
                size=(btn_w, btn_h),
                pos=(base_x + btn_w // 2, btn_y),
                text="Keyboard",
                text_size=18,
                action=lambda: s.set_control_filter('keyboard')
            )
            s.keyboard_filter_toggle.set_theme_colours(use_theme=True)

        if mouse_off and mouse_on:
            mouse_idle = scale_icon(mouse_off)
            mouse_hover = mouse_idle.copy()
            mouse_active = scale_icon(mouse_on)
            mouse_highlight = None
            if mouse_high:
                highlight_max_w = int(max(mouse_idle.get_width(), mouse_active.get_width()) * 1.3)
                highlight_max_h = int(max(mouse_idle.get_height(), mouse_active.get_height()) * 1.3)
                rh_w, rh_h = mouse_high.get_size()
                high_scale = min(highlight_max_w / rh_w, highlight_max_h / rh_h)
                h_w = max(1, int(rh_w * high_scale))
                h_h = max(1, int(rh_h * high_scale))
                mouse_highlight = pygame.transform.smoothscale(mouse_high, (h_w, h_h))

            s.mouse_filter_toggle = ImageToggleButton(
                launcher,
                pos=(base_x + btn_w + btn_gap + btn_w // 2, btn_y),
                idle_img=mouse_idle,
                hover_img=mouse_hover,
                active_img=mouse_active,
                highlight_img=mouse_highlight,
                text="",
                text_size=24,
                action=lambda: s.set_control_filter('mouse')
            )
        else:
            s.mouse_filter_toggle = GenericToggleButton(
                launcher,
                size=(btn_w, btn_h),
                pos=(base_x + btn_w + btn_gap + btn_w // 2, btn_y),
                text="Mouse",
                text_size=18,
                action=lambda: s.set_control_filter('mouse')
            )
            s.mouse_filter_toggle.set_theme_colours(use_theme=True)

        # Use the actual icon widths so the keyboard and mouse buttons sit closer together.
        filter_gap = 8
        if s.mouse_filter_toggle:
            mouse_x = s.searchbar.custom_x - filter_gap - s.mouse_filter_toggle.rect.width // 2
            s.mouse_filter_toggle.pos = (mouse_x, btn_y)
            s.mouse_filter_toggle.rect = s.mouse_filter_toggle.image.get_rect(center=s.mouse_filter_toggle.pos)

            if s.keyboard_filter_toggle:
                kb_x = mouse_x - filter_gap - s.keyboard_filter_toggle.rect.width // 2
                s.keyboard_filter_toggle.pos = (kb_x, btn_y)
                s.keyboard_filter_toggle.rect = s.keyboard_filter_toggle.image.get_rect(center=s.keyboard_filter_toggle.pos)

    def _update_filter_positions(s):
        filter_gap = 40
        btn_y = s.searchbar.custom_y + s.searchbar.h // 2

        if s.mouse_filter_toggle:
            mouse_x = s.searchbar.custom_x - filter_gap - s.mouse_filter_toggle.rect.width // 2
            s.mouse_filter_toggle.pos = (mouse_x, btn_y)
            if hasattr(s.mouse_filter_toggle, 'update_appearance'):
                s.mouse_filter_toggle.update_appearance()
            else:
                s.mouse_filter_toggle.rect = s.mouse_filter_toggle.image.get_rect(center=s.mouse_filter_toggle.pos)

        if s.keyboard_filter_toggle:
            kb_x = s.searchbar.custom_x - filter_gap - s.mouse_filter_toggle.rect.width - filter_gap - s.keyboard_filter_toggle.rect.width // 2 if s.mouse_filter_toggle else s.searchbar.custom_x - filter_gap - s.keyboard_filter_toggle.rect.width // 2
            if s.mouse_filter_toggle:
                kb_x = s.mouse_filter_toggle.pos[0] - filter_gap - s.keyboard_filter_toggle.rect.width // 2
            else:
                kb_x = s.searchbar.custom_x - filter_gap - s.keyboard_filter_toggle.rect.width // 2
            s.keyboard_filter_toggle.pos = (kb_x, btn_y)
            if hasattr(s.keyboard_filter_toggle, 'update_appearance'):
                s.keyboard_filter_toggle.update_appearance()
            else:
                s.keyboard_filter_toggle.rect = s.keyboard_filter_toggle.image.get_rect(center=s.keyboard_filter_toggle.pos)

    def set_control_filter(s, filter_name):
        if s.control_filter == filter_name:
            s.control_filter = 'all'
            s.keyboard_filter_toggle.is_on = False
            s.mouse_filter_toggle.is_on = False
        else:
            s.control_filter = filter_name
            s.keyboard_filter_toggle.is_on = (filter_name == 'keyboard')
            s.mouse_filter_toggle.is_on = (filter_name == 'mouse')

        s.apply_filters()

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
            controls = data.get('controls', '').lower()

            if query and query not in name:
                continue
            if s.control_filter == 'keyboard' and controls != 'keyboard':
                continue
            if s.control_filter == 'mouse' and controls != 'mouse':
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
        state_manager = s.launcher.state_manager
        input_manager = getattr(s.launcher, 'input_manager', None)

        for event in events:
            if event.type == pygame.KEYDOWN:
                current_key = event.key

                if state_manager.ui_focus == "searchbar" and s.searchbar.active:
                    if s.searchbar.handle_events([event]):
                        state_manager.ui_focus = "tabs"
                    continue

                is_confirm = bool(input_manager and input_manager.just_pressed('action_a'))
                is_back = bool(input_manager and input_manager.just_pressed('action_b'))
                is_left = bool(input_manager and input_manager.just_pressed('left'))
                is_right = bool(input_manager and input_manager.just_pressed('right'))
                is_up = bool(input_manager and input_manager.just_pressed('up'))
                is_down = bool(input_manager and input_manager.just_pressed('down'))

                is_downloading_active = s.launcher.installer.is_downloading or s.launcher.installer.download_queue

                if state_manager.ui_focus in ["searchbar", "filters"]:
                    if state_manager.ui_focus == "searchbar":
                        if is_confirm:
                            s.searchbar.open_keyboard()
                        elif is_back:
                            s.searchbar.active = False
                            state_manager.ui_focus = "tabs"
                        elif is_left:
                            if is_downloading_active:
                                state_manager.ui_focus = "download"
                            else:
                                state_manager.ui_focus = "filters"
                                s.filter_focus_index = 1
                        elif is_up:
                            state_manager.ui_focus = "filters"
                            s.filter_focus_index = 1
                        elif is_down:
                            state_manager.ui_focus = "tabs"
                    else:
                        if is_left and s.filter_focus_index > 0:
                            s.filter_focus_index -= 1
                        elif is_right and s.filter_focus_index < 2:
                            s.filter_focus_index += 1
                        elif is_confirm:
                            if s.filter_focus_index == 0 and s.keyboard_filter_toggle:
                                s.keyboard_filter_toggle.toggle()
                            elif s.filter_focus_index == 1 and s.mouse_filter_toggle:
                                s.mouse_filter_toggle.toggle()
                            elif s.filter_focus_index == 2:
                                s.searchbar.open_keyboard()
                                state_manager.ui_focus = "searchbar"
                        elif is_back:
                            state_manager.ui_focus = "tabs"
                        elif is_down:
                            state_manager.ui_focus = "tabs"
                elif state_manager.ui_focus == "download":
                    if is_confirm and s.launcher.installer.is_downloading:
                        s.launcher.installer.cancel_download()
                    elif is_right:
                        state_manager.ui_focus = "searchbar"
                    elif is_down:
                        state_manager.ui_focus = "tabs"
                    elif is_back:
                        state_manager.ui_focus = "searchbar"
                elif state_manager.ui_focus == "tabs":
                    if is_left and s.selected_tab_index > 0:
                        s.selected_tab_index -= 1
                        s.apply_filters()
                    elif is_right and s.selected_tab_index < len(s.tabs) - 1:
                        s.selected_tab_index += 1
                        s.apply_filters()
                    elif is_up:
                        state_manager.ui_focus = "download" if is_downloading_active else "searchbar"
                    elif is_down or is_confirm:
                        state_manager.ui_focus = "featured" if s.selected_tab_index == 0 else "content"
                    elif is_back:
                        state_manager.ui_focus = "searchbar"
                elif state_manager.ui_focus == "featured":
                    if is_left:
                        s.feature_frame.previous()
                    elif is_right:
                        s.feature_frame.next()
                    elif is_up:
                        state_manager.ui_focus = "tabs"
                    elif is_down and s.entries:
                        state_manager.ui_focus = "content"
                    elif is_confirm:
                        s.enter_game_preview()
                    elif is_back:
                        state_manager.ui_focus = "tabs"
                elif state_manager.ui_focus == "content":
                    if is_back:
                        state_manager.ui_focus = "featured"
                    elif is_left:
                        if s.selected_index % s.columns != 0:
                            s.selected_index -= 1
                    elif is_right:
                        if (s.selected_index + 1) % s.columns != 0 and s.selected_index + 1 < len(s.entries):
                            s.selected_index += 1
                    elif is_up:
                        if s.selected_index < s.columns:
                            state_manager.ui_focus = "featured" if s.selected_tab_index == 0 else "tabs"
                        else:
                            s.selected_index -= s.columns
                    elif is_down and s.selected_index + s.columns < len(s.entries):
                        s.selected_index += s.columns
                    elif is_confirm:
                        s.enter_game_preview()

                if current_key == pygame.K_s:
                    s.sort_mode = "Z-A" if s.sort_mode == "A-Z" else "A-Z"
                    s.apply_filters()

        s.handle_mouse_events(events)

    def handle_mouse_events(s, events):
        state_manager = s.launcher.state_manager

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if hasattr(s, 'cancel_rect') and s.cancel_rect.collidepoint(event.pos):
                    s.launcher.installer.cancel_download()

                if s.keyboard_filter_toggle:
                    if s.keyboard_filter_toggle.rect.collidepoint(event.pos):
                        state_manager.ui_focus = 'filters'
                        s.filter_focus_index = 0
                    s.keyboard_filter_toggle.handling_events([event])
                if s.mouse_filter_toggle:
                    if s.mouse_filter_toggle.rect.collidepoint(event.pos):
                        state_manager.ui_focus = 'filters'
                        s.filter_focus_index = 1
                    s.mouse_filter_toggle.handling_events([event])

                search_rect = pygame.Rect(s.searchbar.custom_x, s.searchbar.custom_y, s.searchbar.w, s.searchbar.h)
                if search_rect.collidepoint(event.pos):
                    s.searchbar.open_keyboard()
                    state_manager.ui_focus = 'searchbar'

                if s.selected_tab_index == 0:
                    clicked_nav = s.feature_frame.handle_mouse_event(event)
                    if not clicked_nav and s.feature_frame.frame_rect.collidepoint(event.pos):
                        s.enter_game_preview()

    def update(s, delta_time):
        super().update(delta_time)
        s.feature_frame.update(delta_time)

        if s.keyboard_filter_toggle:
            s.keyboard_filter_toggle.update(delta_time)
        if s.mouse_filter_toggle:
            s.mouse_filter_toggle.update(delta_time)

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
        s._update_filter_positions()

        if s.keyboard_filter_toggle:
            s.keyboard_filter_toggle.is_selected = s.launcher.state_manager.ui_focus == 'filters' and s.filter_focus_index == 0
        if s.mouse_filter_toggle:
            s.mouse_filter_toggle.is_selected = s.launcher.state_manager.ui_focus == 'filters' and s.filter_focus_index == 1

        if s.keyboard_filter_toggle:
            s.keyboard_filter_toggle.draw(window)
        if s.mouse_filter_toggle:
            s.mouse_filter_toggle.draw(window)

        search_focused = s.launcher.state_manager.ui_focus == "searchbar" or (s.launcher.state_manager.ui_focus == 'filters' and s.filter_focus_index == 2)
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