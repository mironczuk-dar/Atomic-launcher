#IMPORTING LIBRARIES
import pygame

#A MANAGER FOR MOVING TO DIFFERENT PARTS OF THE OS
class StateManager:
    def __init__(s, launcher):
        s.launcher = launcher
        s.states = {}
        s.active_state = None

    def add_state(s, name, state_object):
        """Dodaje stan do managera."""
        s.states[name] = state_object

    def set_state(s, name):
        """Przełącza aktywny stan na inny."""
        if name in s.states:
            s.active_state = s.states[name]
            print(f"State changed to: {name}")

    def handling_events(s, events):
        """Przekazuje eventy do aktywnego stanu."""
        if s.active_state:
            s.active_state.handling_events(events)

    def update(s, delta_time):
        """Aktualizuje logikę aktywnego stanu."""
        if s.active_state:
            s.active_state.update(delta_time)
            s.active_state.handling_events()

    def draw(s, window):
        """Rysuje aktywny stan."""
        if s.active_state:
            s.active_state.draw(window)