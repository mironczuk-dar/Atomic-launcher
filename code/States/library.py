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
            elif keys[pygame.K_RETURN] or keys[pygame.K_r]:
                self.launch_game()

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
        
        # Wybór ścieżki do gry
        main_path = os.path.join(game_dir, "code", "main.py")
        if not os.path.exists(main_path):
            main_path = os.path.join(game_dir, "main.py")

        current_os = self.launcher.system

        try:
            if current_os == "Linux":
                # --- LOGIKA DLA RASPBERRY PI (OS LITE) ---
                # Tworzymy skrypt tymczasowy dla pętli Bash
                with open("/tmp/run_game.sh", "w") as f:
                    f.write(f"cd \"{game_dir}\" && python3 \"{main_path}\"")
                
                print(f"Linux: Przygotowano skrypt. Zamykanie launchera...")
                pygame.quit()
                sys.exit()

            else:
                # --- LOGIKA DLA WINDOWS (Visual Studio / Desktop) ---
                # Na Windowsie używamy starej metody subprocess, 
                # bo tutaj mamy menedżer okien i nie chcemy zamykać VS.
                print(f"Windows: Uruchamianie gry w nowym procesie...")
                
                # Otwieramy grę jako oddzielny proces
                subprocess.Popen([sys.executable, main_path], cwd=game_dir)
                
                # W opcjach testowych na Windowsie możemy np. zminimalizować okno
                self.launcher.game_running = True
                pygame.display.iconify()

        except Exception as e:
            print(f"Błąd uruchamiania ({current_os}): {e}")


    def on_enter(self):
        """Wywoływane automatycznie przez launcher przy wejściu do biblioteki."""
        print("[Library] Odświeżanie zawartości...")
        self.refresh_library()

    def refresh_library(self):
        # 1. Pobierz aktualne foldery z dysku
        current_folders = [
            name for name in os.listdir(GAMES_DIR)
            if os.path.isdir(os.path.join(GAMES_DIR, name))
        ]

        # 2. Dodaj nowe ikony (jeśli przybyło gier)
        for game in current_folders:
            if game not in self.game_icons:
                icon = GameIcon(
                    launcher=self.launcher,
                    groups=self.icon_group,
                    game_id=game,
                    size=self.icon_w,
                    source="library",
                )
                self.game_icons[game] = icon

        # 3. Usuń ikony gier, których już nie ma na dysku
        removed_games = set(self.game_icons.keys()) - set(current_folders)
        for game in removed_games:
            self.game_icons[game].kill()  # Usuwa sprite z grup Pygame
            del self.game_icons[game]

        # 4. Zaktualizuj listę nazw i filtry
        self.games_list = current_folders
        
        # Resetujemy filtr wyszukiwania, żeby nowa gra była widoczna
        # lub wywołujemy filtrację ponownie z aktualnym tekstem searchbara
        self.apply_search_filter(self.searchbar.text)
        
        # Zabezpieczenie selected_index (żeby nie wyszedł poza zakres po usunięciu gry)
        if self.selected_index >= len(self.filtered_games) and self.filtered_games:
            self.selected_index = len(self.filtered_games) - 1