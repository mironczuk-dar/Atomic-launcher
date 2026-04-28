import pygame
from os.path import join
import math

from settings import BASE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.store_ui.store_entry import StoreEntry, GameStatus
from UI.searchbar import SearchBar
from States.generic_state import BaseState
from Tools.data_loading_tools import load_data


class Store(BaseState):
    def __init__(s, launcher):
        super().__init__(launcher)

        # INTERNET
        s.online = launcher.checking_internet_connection()

        # SEARCHBAR
        s.search_query = ""
        s.searchbar = SearchBar(
            launcher,
            on_change=s.on_search_change
        )

        # CATEGORY TABS
        s.tabs = ["All", "Arcade", "Adventure & RPG", "Cozy", "Horror"]
        s.selected_tab_index = 0

        # SORTING
        s.sort_mode = "A-Z"

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

        # LOAD MANIFEST
        s.manifest_path = join(BASE_DIR, 'code', 'Store', 'games_manifest.json')
        s.manifest = load_data(s.manifest_path, {})

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
        start_y = 190

        for i, game_id in enumerate(s.filtered_games):
            data = s.manifest[game_id]
            manifest_version = data.get('version')

            if s.launcher.installer.is_downloading and s.launcher.installer.current_game_id == game_id:
                status = GameStatus.DOWNLOADING
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
        
        action_confirm = keys[controlls.get('action_a', pygame.K_RETURN)] or keys[pygame.K_r] or keys[pygame.K_RETURN]
        action_back = keys[controlls.get('action_b', pygame.K_ESCAPE)] or keys[pygame.K_e] or keys[pygame.K_ESCAPE]
        
        btn_left = controlls.get('left', pygame.K_LEFT)
        btn_right = controlls.get('right', pygame.K_RIGHT)
        btn_up = controlls.get('up', pygame.K_UP)
        btn_down = controlls.get('down', pygame.K_DOWN)
        btn_options = controlls.get('options', pygame.K_ESCAPE)

        if keys[pygame.K_TAB]:
            state_manager.ui_focus = "sidebar"
            return

        if action_back:
            if state_manager.ui_focus == "content":
                state_manager.ui_focus = "tabs"
            elif state_manager.ui_focus == "tabs":
                state_manager.ui_focus = "sidebar"
            elif state_manager.ui_focus == "searchbar":
                state_manager.ui_focus = "tabs"
                s.searchbar.active = False
            return

        if not s.online:
            if action_back or keys[btn_options] or keys[btn_left] or keys[pygame.K_LEFT]:
                state_manager.ui_focus = "sidebar"
            return

        if keys[pygame.K_s]:
            s.sort_mode = "Z-A" if s.sort_mode == "A-Z" else "A-Z"
            s.apply_filters()

        if state_manager.ui_focus == "searchbar":
            exited = s.searchbar.handle_events(events)
            if exited or keys[btn_down] or keys[pygame.K_DOWN]:
                state_manager.ui_focus = "tabs"
                s.searchbar.active = False
            return

        if state_manager.ui_focus == "tabs":
            if keys[btn_left] or keys[pygame.K_LEFT]:
                if s.selected_tab_index > 0:
                    s.selected_tab_index -= 1
                    s.apply_filters()
                else:
                    state_manager.ui_focus = "sidebar"
            elif keys[btn_right] or keys[pygame.K_RIGHT]:
                s.selected_tab_index = min(len(s.tabs) - 1, s.selected_tab_index + 1)
                s.apply_filters()
            elif keys[btn_up] or keys[pygame.K_UP]:
                state_manager.ui_focus = "searchbar"
                s.searchbar.active = True
            elif keys[btn_down] or keys[pygame.K_DOWN]:
                if s.entries:
                    state_manager.ui_focus = "content"
            return

        if state_manager.ui_focus == "content":
            if keys[btn_up] or keys[pygame.K_UP]:
                if s.selected_index < s.columns:
                    state_manager.ui_focus = "tabs"
                else:
                    s.selected_index -= s.columns
            elif keys[btn_down] or keys[pygame.K_DOWN]:
                if s.selected_index + s.columns < len(s.entries):
                    s.selected_index += s.columns
            elif keys[btn_left] or keys[pygame.K_LEFT]:
                if s.selected_index % s.columns == 0:
                    state_manager.ui_focus = "sidebar"
                else:
                    s.selected_index -= 1
            elif keys[btn_right] or keys[pygame.K_RIGHT]:
                if (s.selected_index + 1) % s.columns != 0 and s.selected_index + 1 < len(s.entries):
                    s.selected_index += 1
            elif action_confirm:
                s.enter_game_preview()

    def update(s, delta_time):
        super().update(delta_time)
        if not s.online or not s.entries:
            return

        row = s.selected_index // s.columns
        start_y = 190
        current_y = start_y + row * (s.entry_height + s.spacing)
        panel_y = 170
        panel_h = WINDOW_HEIGHT - 190

        if current_y + s.entry_height > s.target_scroll + panel_y + panel_h - 20:
            s.target_scroll = current_y + s.entry_height - (panel_y + panel_h - 20)
        if current_y < s.target_scroll + panel_y + 20:
            s.target_scroll = current_y - (panel_y + 20)

        s.target_scroll = max(0, s.target_scroll)
        total_rows = math.ceil(len(s.entries) / s.columns)
        total_content_height = (total_rows * (s.entry_height + s.spacing)) + 40
        max_scroll = max(0, total_content_height - panel_h)
        s.target_scroll = min(s.target_scroll, max_scroll)

        lerp_speed = min(1.0, 15 * delta_time) if delta_time < 1.0 else 0.15
        s.scroll += (s.target_scroll - s.scroll) * lerp_speed
        if abs(s.target_scroll - s.scroll) < 0.5:
            s.scroll = s.target_scroll

    def draw(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        # Base background
        window.fill(theme['colour_1'])

        # ---------- HEADER ----------
        header_h = 90
        # Header uses a slightly lighter background (colour_4) for subtle contrast
        pygame.draw.rect(window, theme['colour_4'], (s.launcher.sidebar.base_w, 0, WINDOW_WIDTH, header_h))

        title_font = pygame.font.SysFont(None, 48, bold=True)
        # Primary Accent (colour_2) for the title text
        title = title_font.render("STORE", True, theme['colour_2'])
        window.blit(title, (s.launcher.sidebar.base_w + 40, 25))

        # ---------- SEARCH BAR ----------
        s.searchbar.custom_x = WINDOW_WIDTH - 600
        s.searchbar.custom_y = 25
        s.searchbar.draw(window, focused=s.launcher.state_manager.ui_focus == "searchbar")

        # ---------- TABS ----------
        s.draw_tabs(window, theme)

        # ---------- LEGEND & CONTROLS ----------
        info_font = pygame.font.SysFont(None, 24)
        controls_text = f"Hotkeys: [TAB] Sidebar | [E] Back | [R] Details | [S] Sort: {s.sort_mode}"
        # Secondary Accent (colour_3) for helpful metadata
        sort_text = info_font.render(controls_text, True, theme['colour_3'])
        text_x = WINDOW_WIDTH - sort_text.get_width() - 40
        window.blit(sort_text, (text_x, 135))

        # ---------- CONTENT PANEL ----------
        panel_rect = pygame.Rect(
            s.launcher.sidebar.base_w + 20,
            170,
            WINDOW_WIDTH - s.launcher.sidebar.base_w - 40,
            WINDOW_HEIGHT - 190
        )

        # Panel body uses colour_4 (the middle-tone dark)
        pygame.draw.rect(window, theme['colour_4'], panel_rect, border_radius=16)
        # Panel border uses colour_3 (muted secondary accent)
        pygame.draw.rect(window, theme['colour_3'], panel_rect, 2, border_radius=16)

        clip_rect = panel_rect.inflate(-6, -6)
        window.set_clip(clip_rect)

        for i, entry in enumerate(s.entries):
            selected = i == s.selected_index and s.launcher.state_manager.ui_focus == "content"
            row = i // s.columns
            start_y = 190
            original_y = start_y + row * (s.entry_height + s.spacing)
            entry.rect.top = original_y - s.scroll

            if entry.rect.bottom > panel_rect.top and entry.rect.top < panel_rect.bottom:
                entry.draw(window)
                if selected:
                    # Focus highlight uses the bright Primary Accent (colour_2)
                    highlight = entry.rect.inflate(14, 14)
                    pygame.draw.rect(window, theme['colour_2'], highlight, 8, border_radius=14)

        # ---------- CUSTOM SCROLLBAR ----------
        total_rows = math.ceil(len(s.entries) / s.columns)
        total_content_height = (total_rows * (s.entry_height + s.spacing)) + 40
        if total_content_height > panel_rect.height:
            scrollbar_w = 8
            visible_ratio = panel_rect.height / total_content_height
            scrollbar_h = max(40, panel_rect.height * visible_ratio)
            max_scroll = total_content_height - panel_rect.height
            scroll_progress = s.scroll / max_scroll if max_scroll > 0 else 0
            scrollbar_y = panel_rect.top + 5 + scroll_progress * (panel_rect.height - scrollbar_h - 10)
            scrollbar_x = panel_rect.right - 15
            
            track_rect = pygame.Rect(scrollbar_x, panel_rect.top + 5, scrollbar_w, panel_rect.height - 10)
            pygame.draw.rect(window, theme['colour_1'], track_rect, border_radius=4)
            
            scroll_rect = pygame.Rect(scrollbar_x, scrollbar_y, scrollbar_w, scrollbar_h)
            pygame.draw.rect(window, theme['colour_2'], scroll_rect, border_radius=4)

        window.set_clip(None)
        super().draw(window)

    def draw_tabs(s, window, theme):
        font = pygame.font.SysFont(None, 26, bold=True)
        x = s.launcher.sidebar.base_w + 40
        y = 110

        for i, tab in enumerate(s.tabs):
            active = i == s.selected_tab_index
            focused = s.launcher.state_manager.ui_focus == "tabs"

            # Selection color logic: Accent 2 for active, Accent 3 for inactive
            text_color = theme['colour_1'] if active else theme['colour_3']
            text = font.render(tab, True, text_color)

            rect = pygame.Rect(x, y, text.get_width() + 32, text.get_height() + 16)

            if active:
                # Active tabs get a subtle background outline
                pygame.draw.rect(window, theme['colour_1'], rect, 3, border_radius=20)
            else:
                pygame.draw.rect(window, theme['colour_3'], rect, 2, border_radius=20)

            if active and focused:
                # Extra glow for focus
                pygame.draw.rect(window, theme['colour_4'], rect.inflate(6, 6), 4, border_radius=22)

            window.blit(text, (rect.x + 16, rect.y + 8))
            x += rect.width + 15

    def enter_game_preview(s):
        if not s.entries:
            return
        entry = s.entries[s.selected_index]
        preview = s.launcher.state_manager.states.get('Game preview')
        if preview:
            preview.setup(entry.game_id, entry.game_data)
            s.launcher.state_manager.set_state('Game preview')

    def on_enter(s):
        s.online = s.launcher.checking_internet_connection()
        s.manifest = load_data(s.manifest_path, {})
        if s.online:
            s.all_games = list(s.manifest.keys())
            s.apply_filters()