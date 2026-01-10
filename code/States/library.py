# IMPORTING LIBRARIES
import pygame
import os
import subprocess
import sys

# IMPORTING FILES
from States.generic_state import BaseState
from settings import BASE_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY

# POINTING TO THE GAMES FOLDER
GAMES_DIR = os.path.join(BASE_DIR, 'games')


class Library(BaseState):
    def __init__(s, launcher):
        super().__init__(launcher)

        # ---------- UI FOCUS ----------
        # games | sidebar | topbar | status
        s.ui_focus = "games"

        # ---------- GAMES ----------
        s.games_list = [
            name for name in os.listdir(GAMES_DIR)
            if os.path.isdir(os.path.join(GAMES_DIR, name))
        ]
        s.selected_index = 0

        # ---------- FONTS ----------
        s.game_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.06), bold=True)
        s.sidebar_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.05), bold=True)
        s.internet_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.02), bold=True)

        # ---------- SIDEBAR ----------
        s.sidebar_index = 0
        s.base_sidebar_w = int(WINDOW_WIDTH * 0.1)
        s.expanded_sidebar_w = int(WINDOW_WIDTH * 0.4)
        s.current_sidebar_w = s.base_sidebar_w

        # ---------------- TOP BAR ----------------
        s.topbar_h = int(WINDOW_HEIGHT * 0.1)
        s.search_active = False
        s.search_text = ""
        s.filtered_games = s.games_list.copy()

        s.search_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.035))

        # ---------- INTERNET ----------
        s.reconnect_cooldown = 0.0

        # ---------- ICONS ----------
        s.icon_w = int(WINDOW_WIDTH * 0.2)
        s.spacing = 40
        s.scroll_speed = 2
        s.current_scroll = 0
        s.icons = {}
        s.load_game_assets()

    # ==================================================
    # INPUT
    # ==================================================

    def handling_events(s, events):
        keys = pygame.key.get_just_pressed()

        if s.search_active:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    s.handle_text_input(event)
            return

        # -------- GAMES --------
        if s.ui_focus == "games":
            if keys[pygame.K_UP]:
                s.ui_focus = "topbar"
            elif keys[pygame.K_LEFT]:
                if s.selected_index == 0: s.ui_focus = "sidebar"
                else: s.selected_index -= 1
            elif keys[pygame.K_RIGHT]:
                s.selected_index = min(s.selected_index + 1, len(s.filtered_games) - 1)
            elif keys[pygame.K_a]:
                s.selected_index = max(0, s.selected_index - 1)
            elif keys[pygame.K_RETURN]:
                s.launch_game()

        # -------- SIDEBAR --------
        elif s.ui_focus == "sidebar":
            if keys[pygame.K_RIGHT]:
                s.ui_focus = "games"
            elif keys[pygame.K_DOWN]:
                s.sidebar_index = (s.sidebar_index + 1) % len(s.sidebar_options)
            elif keys[pygame.K_UP]:
                s.sidebar_index = (s.sidebar_index - 1) % len(s.sidebar_options)
            elif keys[pygame.K_RETURN]:
                s.execute_sidebar_action()

        # -------- TOP BAR --------
        elif s.ui_focus == "topbar":
            if keys[pygame.K_DOWN]:
                s.ui_focus = "games"
            elif keys[pygame.K_RIGHT]:
                s.ui_focus = "status"
            elif keys[pygame.K_RETURN]:
                s.search_active = True
                s.search_text = ""
                s.apply_search_filter()

        # -------- STATUS --------
        elif s.ui_focus == "status":
            if keys[pygame.K_LEFT]:
                s.ui_focus = "topbar"
            elif keys[pygame.K_RETURN]:
                s.try_reconnect()

    # ==================================================
    # UPDATE
    # ==================================================

    def update(s, delta_time):
        target_scroll = max(0, s.selected_index)
        s.current_scroll += (target_scroll - s.current_scroll) * s.scroll_speed * delta_time

        target_w = s.expanded_sidebar_w if s.ui_focus == "sidebar" else s.base_sidebar_w
        s.current_sidebar_w += (target_w - s.current_sidebar_w) * 12 * delta_time

        s.reconnect_cooldown = max(0, s.reconnect_cooldown - delta_time)

    # ==================================================
    # DRAW
    # ==================================================

    def draw(s, window):
        s.drawing_game_icons(window)
        s.draw_topbar(window)
        s.drawing_sidebar(window)

    # --------------------------------------------------

    def drawing_sidebar(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]

        s.sidebar_options = list(s.launcher.state_manager.states.keys())
        if not s.sidebar_options:
            return

        pygame.draw.rect(
            window,
            theme['colour_2'],
            (0, 0, int(s.current_sidebar_w), WINDOW_HEIGHT)
        )

        pygame.draw.line(
            window,
            theme['colour_3'],
            (int(s.current_sidebar_w), 0),
            (int(s.current_sidebar_w), WINDOW_HEIGHT),
            4
        )

        width_diff = s.expanded_sidebar_w - s.base_sidebar_w
        progress = (s.current_sidebar_w - s.base_sidebar_w) / max(1, width_diff)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.05:
            return

        section_h = WINDOW_HEIGHT / len(s.sidebar_options)

        for i, state in enumerate(s.sidebar_options):
            selected = (s.ui_focus == "sidebar" and i == s.sidebar_index)
            color = theme['colour_3'] if selected else (220, 220, 220)

            text = s.sidebar_font.render(state.upper(), True, color).convert_alpha()
            text.set_alpha(int(progress * 255))

            x = 30
            y = section_h * i + section_h / 2 - text.get_height() / 2
            window.blit(text, (x, y))

    # --------------------------------------------------

    def drawing_game_icons(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])

        if not s.filtered_games:
            msg = s.game_font.render("NO GAMES FOUND", True, theme['colour_2'])
            window.blit(msg, (WINDOW_WIDTH // 2 - msg.get_width() // 2, WINDOW_HEIGHT // 2))
            return

        center_x = s.base_sidebar_w + (WINDOW_WIDTH - s.base_sidebar_w) // 2
        center_y = WINDOW_HEIGHT // 2

        for i, game in enumerate(s.filtered_games):
            offset = (i - s.current_scroll) * (s.icon_w + s.spacing)
            x = center_x - s.icon_w // 2 + offset
            y = center_y - s.icon_w // 2

            if i == s.selected_index and s.ui_focus == "games":
                pygame.draw.rect(
                    window,
                    theme['colour_3'],
                    (x - 8, y - 8, s.icon_w + 16, s.icon_w + 16),
                    border_radius=10
                )

            window.blit(s.icons[game], (x, y))

            if i == s.selected_index:
                name = game.replace("_", " ").upper()
                text = s.game_font.render(name, True, theme['colour_3'])
                window.blit(
                    text,
                    (x + s.icon_w // 2 - text.get_width() // 2, y - 55)
                )

    # --------------------------------------------------

    def draw_topbar(s, window):
        theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]

        # -------- BACKGROUND --------
        pygame.draw.rect(
            window,
            theme['colour_1'],
            pygame.Rect(0, 0, WINDOW_WIDTH, s.topbar_h)
        )

        # -------- SEARCH BAR --------
        bar_w = int(WINDOW_WIDTH * 0.5)
        bar_h = int(s.topbar_h * 0.55)
        bar_x = WINDOW_WIDTH // 2 - bar_w // 2
        bar_y = s.topbar_h // 2 - bar_h // 2

        # border kolor jeśli focus na search
        if s.ui_focus == 'topbar' and s.search_active:
            search_border_color = theme['colour_3']
        elif s.ui_focus == 'topbar':
            search_border_color = theme['colour_4']
        else:
            search_border_color = theme['colour_2']

        pygame.draw.rect(
            window,
            search_border_color,
            (bar_x, bar_y, bar_w, bar_h),
            3,
            border_radius=8
        )

        # tekst w search barze
        display_text = s.search_text
        
        # Jeśli szukanie jest aktywne, dodaj migający kursor
        if s.search_active:
            if pygame.time.get_ticks() % 1000 < 500:
                display_text += "|"
        
        text_to_render = display_text if display_text else "Search game..."
        
        # Zmiana koloru tekstu, gdy szukanie jest aktywne
        if s.search_active:
            color = (255, 255, 255) # Biały przy pisaniu
        elif s.search_text:
            color = (220, 220, 220) # Jasny jeśli coś wpisano
        else:
            color = (140, 140, 140) # Szary dla placeholder'a

        surf = s.search_font.render(text_to_render, True, color)
        window.blit(surf, (bar_x + 12, bar_y + bar_h // 2 - surf.get_height() // 2))

        # -------- STATUS BAR --------
        status_w = int(WINDOW_WIDTH * 0.12)
        status_h = int(bar_h)
        status_x = WINDOW_WIDTH - status_w - 20
        status_y = bar_y

        # border kolor jeśli focus na status
        status_border_color = theme['colour_4'] if s.ui_focus == 'status' else (180, 180, 180)

        pygame.draw.rect(
            window,
            status_border_color,
            (status_x, status_y, status_w, status_h),
            3,
            border_radius=8
        )

        # tekst statusu
        status_text = "ONLINE" if s.launcher.online_mode else "OFFLINE"
        if s.ui_focus == "status":
            status_text = f"[ {status_text} ]"
        status_color = (80, 200, 120) if s.launcher.online_mode else (220, 80, 80)

        status_surf = s.internet_font.render(status_text, True, status_color)
        window.blit(
            status_surf,
            (status_x + status_w // 2 - status_surf.get_width() // 2,
            status_y + status_h // 2 - status_surf.get_height() // 2)
        )

    # ==================================================
    # LOGIC
    # ==================================================

    def launch_game(s):
        if not s.filtered_games:
            return

        game_name = s.filtered_games[s.selected_index]
        game_dir = os.path.join(GAMES_DIR, game_name)

        # Wykrywanie systemu
        is_windows = sys.platform.startswith("win")
        is_linux = sys.platform.startswith("linux")

        if is_windows:
            run_file = "[RUN]-Windows.bat"
            # Zamień wywołanie bat na bezpośrednie pythonw
            # Zakładamy, że gra jest plikiem Python lub exe
            game_exec = os.path.join(game_dir, 'code', "main.py")  # przykładowo
            if not os.path.exists(game_exec):
                print(f"Brak pliku gry: {game_exec}")
                return

            proc = subprocess.Popen(
                ["pythonw", game_exec],
                cwd=game_dir
            )

        elif is_linux:
            run_file = "[RUN]-linux.sh"
            os.chmod(os.path.join(game_dir, run_file), 0o755)
            proc = subprocess.Popen(
                ["bash", run_file],
                cwd=game_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            print("Nieobsługiwany system operacyjny")
            return

        s.launcher.game_process = proc
        s.launcher.game_running = True

        if s.launcher.performance_settings_data['minimise_launcher_when_game_active']:
            pygame.display.iconify()

    def try_reconnect(s):
        if s.reconnect_cooldown > 0:
            return
        s.launcher.online_mode = s.launcher.checking_internet_connection()
        s.reconnect_cooldown = 2.0

    def execute_sidebar_action(s):
        state = s.sidebar_options[s.sidebar_index]
        s.launcher.state_manager.set_state(state)

    def load_game_assets(s):
        icon_size = (s.icon_w, s.icon_w)
        default = pygame.Surface(icon_size)
        default.fill(THEME_LIBRARY[s.launcher.theme_data['current_theme']]['colour_2'])

        for game in s.games_list:
            path = os.path.join(GAMES_DIR, game, "icon.png")
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                s.icons[game] = pygame.transform.scale(img, icon_size)
            else:
                s.icons[game] = default

    def handle_text_input(s, event):
        if not s.search_active:
            return

        if event.key == pygame.K_BACKSPACE:
            s.search_text = s.search_text[:-1]

        elif event.key == pygame.K_RETURN:
            s.search_active = False

        else:
            if event.unicode and len(event.unicode) == 1:
                s.search_text += event.unicode

        s.apply_search_filter()

    def apply_search_filter(s):
            query = s.search_text.lower()

            if query == "":
                s.filtered_games = s.games_list.copy()
            else:
                s.filtered_games = [
                    g for g in s.games_list if query in g.lower()
                ]

            s.selected_index = 0