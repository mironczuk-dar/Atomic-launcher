#IMPORTING LIBRARIES
import pygame

#IMPORTING FILES
from UI.sidebar import Sidebar

#CLASS FOR INHERITANCE | A BASIC STATE
class BaseState:
    def __init__(self, launcher):
        self.launcher = launcher
        self.system = launcher.system

        # każdy state ma sidebar
        self.sidebar = Sidebar(launcher)

        # domyślny focus
        self.ui_focus = "content"  # content | sidebar | topbar | status

    # =========================
    # INPUT
    # =========================

    def handling_events(self, events):
        keys = pygame.key.get_just_pressed()

        # Jeśli dopiero wchodzimy do sidebaru, ustaw highlight na aktualnym stanie
        if self.ui_focus == "sidebar" and not getattr(self, "sidebar_initialized", False):
            current_state_name = None
            for name, state in self.launcher.state_manager.states.items():
                if state is self.launcher.state_manager.active_state:
                    current_state_name = name
                    break

            if current_state_name and current_state_name in self.sidebar.options:
                self.sidebar.index = self.sidebar.options.index(current_state_name)

            # Oznaczamy, że już ustawiliśmy indeks, żeby nie resetować go co klatkę
            self.sidebar_initialized = True

        # Sidebar i topbar zawsze działają
        self.sidebar.handle_input(keys, self.ui_focus)

        # Wyjście z sidebaru resetuje flagę
        if self.ui_focus != "sidebar":
            self.sidebar_initialized = False

        # Przejście focusu z sidebaru do content
        if self.ui_focus == "sidebar" and keys[pygame.K_RIGHT]:
            self.ui_focus = "content"

    # =========================
    # UPDATE
    # =========================

    def update(self, delta_time):
        self.sidebar.update(delta_time, self.ui_focus)

    # =========================
    # DRAW
    # =========================

    def draw(self, window):
        self.sidebar.draw(window)
