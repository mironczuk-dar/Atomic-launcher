# =========================
# generic_state.py
# =========================
import pygame


class BaseState:
    def __init__(self, launcher):
        self.launcher = launcher
        self.system = launcher.system

    # =========================
    # INPUT
    # =========================
    def handling_events(self, events):
        """
        Obsługa inputu lokalnego stanu.
        Globalny input (TAB, sidebar) jest w StateManager.
        """
        pass

    # =========================
    # UPDATE
    # =========================
    def update(self, delta_time):
        """
        Logika stanu.
        Sidebar i focus NIE są tu aktualizowane.
        """
        pass

    # =========================
    # DRAW
    # =========================
    def draw(self, window):
        """
        Rysowanie zawartości stanu.
        Sidebar rysowany jest w StateManager.
        """
        pass

    # =========================
    # LIFECYCLE
    # =========================
    def on_enter(self):
        pass
