"""State manager for the launcher.

This module provides `StateManager`, a thin router that switches between
application states (Library, Store, Options, etc.), manages UI focus
between the sidebar and content area, and forwards events/update/draw
calls to the active state.
"""

import pygame


class StateManager:
    """Manage application states and route input/updates/draws.

    Attributes
    - launcher: reference to the top-level `Launcher` instance
    - states: dict mapping state names to state instances
    - active_state: currently active state instance
    - ui_focus: which UI region has focus ('content' or 'sidebar')
    """

    def __init__(s, launcher):
        s.launcher = launcher
        s.states = {}
        s.active_state = None
        s.ui_focus = 'content'

    def add_state(s, name, state_object):
        """Register a state instance under `name`."""
        s.states[name] = state_object

    def set_state(s, name):
        """Switch to a registered state by name and trigger lifecycle hooks."""
        if name in s.states:
            s.active_state = s.states[name]
            print(f"State changed to: {name}")

            if hasattr(s.active_state, 'on_enter'):
                s.active_state.on_enter()

            s.launcher.audio_manager.play_for_state(name)

    def handling_events(s, events):
        """Handle input events and forward them to the sidebar or active state.

        The `options` key toggles focus between the sidebar and the content
        area. Events are then dispatched accordingly.
        """
        input_manager = getattr(s.launcher, 'input_manager', None)
        if input_manager and input_manager.just_pressed('options'):
            s.ui_focus = "sidebar" if s.ui_focus != "sidebar" else "content"

        # Route events to the focused UI component
        if s.ui_focus == "sidebar":
            s.launcher.sidebar.handle_input(events)
        else:
            if s.active_state:
                s.active_state.handling_events(events)

    def update(s, delta_time):
        """Update sidebar and the active state each frame."""
        s.launcher.sidebar.update(delta_time)
        if s.active_state:
            s.active_state.update(delta_time)

    def draw(s, window):
        """Draw the active state, then overlay the sidebar."""
        if s.active_state:
            s.active_state.draw(window)
        s.launcher.sidebar.draw(window)
