# IMPORTING LIBRARIES
import pygame
import os
import subprocess
import sys

# IMPORTING FILES
from States.generic_state import BaseState
from settings import GAMES_DIR, WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.searchbar import SearchBar
from UI.game_icon import GameIcon


class Library(BaseState):
    def __init__(self, launcher):
        super().__init__(launcher)

        # ---------- UI FOCUS ----------
        # content | sidebar | topbar | status
        self.ui_focus = "content"

        # ---------- GAMES ----------
        self.games_list = [
            name for name in os.listdir(GAMES_DIR)
            if os.path.isdir(os.path.join(GAMES_DIR, name))
        ]
        self.filtered_games = self.games_list.copy()
        self.selected_index = 0

        # ---------- UI ----------
        self.searchbar = SearchBar(
            launcher,
            on_change=self.apply_search_filter
        )

        # ---------- FONTS ----------
        self.game_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.06))
        self.internet_font = pygame.font.SysFont(None, int(WINDOW_WIDTH * 0.02), bold=True)

        # ---------- TOP BAR ----------
        self.topbar_h = int(WINDOW_HEIGHT * 0.1)

        # ---------- INTERNET ----------
        self.reconnect_cooldown = 0.0

        # ---------- ICONS ----------
        self.icon_w = int(WINDOW_WIDTH * 0.2)
        self.spacing = 40
        self.scroll_speed = 6
        self.current_scroll = 0

        # ---------- ICON OBJECTS ----------
        self.icon_group = pygame.sprite.Group()
        self.game_icons = {}

        for game in self.games_list:
            icon = GameIcon(
                launcher=self.launcher,
                groups=self.icon_group,
                game_id=game,
                size=self.icon_w,
                source="library",
            )
            self.game_icons[game] = icon

    # ==================================================
    # INPUT
    # ==================================================

    def handling_events(self, events):
        keys = pygame.key.get_just_pressed()

        exited_search = self.searchbar.handle_events(events)
        if exited_search:
            self.ui_focus = "content"
            return
        if self.searchbar.active:
            return

        initial_focus = self.ui_focus
        super().handling_events(events)

        if initial_focus != self.ui_focus:
            return

        # -------- CONTENT --------
        if self.ui_focus == "content":
            if keys[pygame.K_UP]:
                self.ui_focus = "topbar"
            elif keys[pygame.K_LEFT]:
                if self.selected_index > 0:
                    self.selected_index -= 1
                else:
                    self.ui_focus = "sidebar"
            elif keys[pygame.K_RIGHT]:
                if self.filtered_games:
                    self.selected_index = min(
                        self.selected_index + 1,
                        len(self.filtered_games) - 1
                    )

        # -------- TOP BAR --------
        elif self.ui_focus == "topbar":
            if keys[pygame.K_DOWN]:
                self.ui_focus = "content"
            elif keys[pygame.K_RIGHT]:
                self.ui_focus = "status"
            elif keys[pygame.K_RETURN]:
                self.searchbar.active = True

        # -------- STATUS --------
        elif self.ui_focus == "status":
            if keys[pygame.K_LEFT]:
                self.ui_focus = "topbar"
            elif keys[pygame.K_DOWN]:
                self.ui_focus = "content"
            elif keys[pygame.K_RETURN]:
                self.try_reconnect()

    # ==================================================
    # UPDATE
    # ==================================================

    def update(self, delta_time):
        super().update(delta_time)

        # smooth scroll
        self.current_scroll += (
            self.selected_index - self.current_scroll
        ) * self.scroll_speed * delta_time

        self.reconnect_cooldown = max(0, self.reconnect_cooldown - delta_time)

    # ==================================================
    # DRAW
    # ==================================================

    def draw(self, window):
        self.draw_game_icons(window)
        self.draw_topbar(window)

        self.searchbar.draw(
            window,
            focused=self.ui_focus == "topbar"
        )

        super().draw(window)  # sidebar

    # --------------------------------------------------

    def draw_game_icons(self, window):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        window.fill(theme['colour_1'])

        if not self.filtered_games:
            msg = self.game_font.render("NO GAMES FOUND", True, theme['colour_2'])
            window.blit(
                msg,
                (WINDOW_WIDTH // 2 - msg.get_width() // 2,
                 WINDOW_HEIGHT // 2)
            )
            return

        center_x = self.sidebar.current_w + (WINDOW_WIDTH - self.sidebar.current_w) // 2 -100
        center_y = WINDOW_HEIGHT // 2

        for i, game in enumerate(self.filtered_games):
            icon = self.game_icons.get(game)
            if not icon:
                continue

            offset = (i - self.current_scroll) * (self.icon_w + self.spacing)
            x = center_x + offset
            y = center_y

            icon.set_position(x, y)
            icon.set_selected(
                i == self.selected_index and self.ui_focus == "content"
            )
            icon.draw(window)

            if i == self.selected_index and self.ui_focus == 'content':
                name = game.replace("_", " ").upper()
                text = self.game_font.render(name, True, theme['colour_3'])
                window.blit(
                    text,
                    (x - text.get_width() // 2,
                     y - self.icon_w // 2 - 80)
                )

    # --------------------------------------------------

    def draw_topbar(self, window):
        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]

        pygame.draw.rect(
            window,
            theme['colour_1'],
            (0, 0, WINDOW_WIDTH, self.topbar_h)
        )

        # -------- STATUS --------
        status_w = int(WINDOW_WIDTH * 0.12)
        status_h = int(self.topbar_h * 0.55)
        status_x = WINDOW_WIDTH - status_w - 20
        status_y = self.topbar_h // 2 - status_h // 2

        border = theme['colour_4'] if self.ui_focus == "status" else theme['colour_2']

        pygame.draw.rect(
            window,
            border,
            (status_x, status_y, status_w, status_h),
            3,
            border_radius=8
        )

        status_text = "ONLINE" if self.launcher.online_mode else "OFFLINE"
        color = (80, 200, 120) if self.launcher.online_mode else (220, 80, 80)

        surf = self.internet_font.render(status_text, True, color)
        window.blit(
            surf,
            (status_x + status_w // 2 - surf.get_width() // 2,
             status_y + status_h // 2 - surf.get_height() // 2)
        )

    # ==================================================
    # LOGIC
    # ==================================================

    def apply_search_filter(self, query):
        query = query.lower()
        self.filtered_games = [
            g for g in self.games_list if query in g.lower()
        ] if query else self.games_list.copy()
        self.selected_index = 0

    def try_reconnect(self):
        if self.reconnect_cooldown > 0:
            return
        self.launcher.online_mode = self.launcher.checking_internet_connection()
        self.reconnect_cooldown = 2.0

    def launch_game(self):
        if not self.filtered_games:
            return

        game = self.filtered_games[self.selected_index]
        game_dir = os.path.join(GAMES_DIR, game)

        if sys.platform.startswith("win"):
            subprocess.Popen(
                ["pythonw", os.path.join(game_dir, "code", "main.py")],
                cwd=game_dir
            )
        elif sys.platform.startswith("linux"):
            run_file = os.path.join(game_dir, "[RUN]-linux.sh")
            os.chmod(run_file, 0o755)
            subprocess.Popen(["bash", run_file], cwd=game_dir)
