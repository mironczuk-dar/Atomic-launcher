#IMPORTING LIBRARIES
import pygame

#A MANAGER FOR MOVING TO DIFFERENT PARTS OF THE OS
class StateManager:
    def __init__(s, launcher):
        s.launcher = launcher
        s.states = {}
        s.active_state = None
        s.ui_focus = 'content'

    def add_state(s, name, state_object):
        s.states[name] = state_object

    def set_state(s, name):
        if name in s.states:
            s.active_state = s.states[name]
            print(f"State changed to: {name}")

            if hasattr(s.active_state, 'on_enter'):
                s.active_state.on_enter()

    def handling_events(s, events):
        keys = pygame.key.get_just_pressed()

        if keys[s.launcher.controlls_data['options']]:
            s.ui_focus = "sidebar" if s.ui_focus != "sidebar" else "content"

        if s.ui_focus == "sidebar":
            s.launcher.sidebar.handle_input(keys)
        else:
            if s.active_state:
                s.active_state.handling_events(events)

    def update(s, delta_time):
        s.launcher.sidebar.update(delta_time)

        if s.active_state:
            s.active_state.update(delta_time)

    def draw(s, window):

        if s.active_state:
            s.active_state.draw(window)

        s.launcher.sidebar.draw(window)
