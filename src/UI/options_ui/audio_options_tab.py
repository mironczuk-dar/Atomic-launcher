"""Audio options tab: volume controls and audio toggles.

This tab exposes music and sound sliders and allows the user to toggle
background music and sound effects on or off. It also performs a preview
sound effect after the user changes the sound volume, throttled by a
cooldown timer.

Developer notes
+- `handling_events` supports both keyboard navigation and raw UI element
+  mouse events. If you add new UI elements, ensure they implement
+  `handling_events(events, ctrl)` or fallback gracefully.
+- Audio state is written through `launcher.audio_manager` and should stay
+  consistent with `launcher.audio_data`.
"""

import pygame

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY
from UI.options_ui.generic_options_tab import GenericOptionsTab
from UI.ui_elements.slider import Slider
from UI.ui_elements.buttons import GenericToggleButton

class AudioOptionsTab(GenericOptionsTab):
    """Options tab for audio volume and toggle settings.

    This tab controls music and sound settings through `AudioManager` and
    schedules preview audio playback whenever the sound volume changes.
    """

    def __init__(s, launcher):
        super().__init__(launcher)
        
        # Pull the current theme just like in VideoOptionsTab
        s.current_theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        
        s.ui_elements = []
        s.selected_index = 0  # Used for tracking keyboard navigation focus
        
        # Cooldown properties for the volume preview sound
        s.preview_cooldown_timer = 0.0
        s.preview_cooldown_duration = 0.3  # Interval in seconds between preview sounds
        s.sound_changed_flag = False        # Tracks if the volume was adjusted
        
        s.setup()

    def setup(s):
        slider_size = (800, 40)
        
        music_slider = Slider(
            s.launcher,
            pos=(WINDOW_WIDTH/2 - slider_size[0]/2, WINDOW_HEIGHT/3),
            size=slider_size,
            min_val=0,
            max_val=1,
            start_val=s.launcher.audio_data.get("music_volume", 1.0),
            on_change=lambda v: s.launcher.audio_manager.set_music_volume(v)
        )

        # Redirected on_change to our custom tracker method
        sound_slider = Slider(
            s.launcher,
            pos=(WINDOW_WIDTH/2 - slider_size[0]/2, WINDOW_HEIGHT/3*2),
            size=slider_size,
            min_val=0,
            max_val=1,
            start_val=s.launcher.audio_data.get("sound_volume", 1.0),
            on_change=s.handle_sound_volume_change
        )

        music_toggle = GenericToggleButton(
            s.launcher,
            size=(220, 50),
            pos=(WINDOW_WIDTH/2, WINDOW_HEIGHT/3 + slider_size[1] + 50),
            text="Music",
            action=s.launcher.audio_manager.toggle_music
        )

        sound_toggle = GenericToggleButton(
            s.launcher,
            size=(220, 50),
            pos=(WINDOW_WIDTH/2, WINDOW_HEIGHT/3*2 + slider_size[1] + 50),
            text="Sound",
            action=s.launcher.audio_manager.toggle_sound
        )

        s.ui_elements.extend([
            music_slider,
            music_toggle,
            sound_slider,
            sound_toggle
        ])

    def handle_sound_volume_change(s, v):
        """Update the sound volume and mark the change for a preview sound."""
        s.launcher.audio_manager.set_sound_volume(v)
        s.sound_changed_flag = True

    def handling_events(s, events, ctrl):
        """Handle keyboard and UI element events inside the audio tab."""
        if s.launcher.state_manager.ui_focus != 'content':
            return

        input_manager = getattr(s.launcher, 'input_manager', None)

        if input_manager is None:
            for element in s.ui_elements:
                if hasattr(element, 'handling_events'):
                    try:
                        element.handling_events(events, ctrl)
                    except TypeError:
                        element.handling_events(events)
            return

        if input_manager.just_pressed('up'):
            s.selected_index = (s.selected_index - 1) % len(s.ui_elements)
        elif input_manager.just_pressed('down'):
            s.selected_index = (s.selected_index + 1) % len(s.ui_elements)

        for i, element in enumerate(s.ui_elements):
            if hasattr(element, 'is_selected'):
                element.is_selected = (i == s.selected_index)

        active_element = s.ui_elements[s.selected_index]

        if active_element.__class__.__name__ == "Slider":
            if input_manager.just_pressed('left'):
                active_element.change_value(-active_element.step)
            elif input_manager.just_pressed('right'):
                active_element.change_value(active_element.step)
        elif input_manager.just_pressed('action_a'):
            if hasattr(active_element, 'activate'):
                active_element.activate()
            elif hasattr(active_element, 'action') and active_element.action:
                active_element.action()

        if hasattr(active_element, 'handling_events'):
            try:
                active_element.handling_events(events, ctrl)
            except TypeError:
                active_element.handling_events(events)

    def update(s, delta_time):
        """Update internal timers and UI elements each frame."""
        # Update logic for sliders/buttons
        for element in s.ui_elements:
            if hasattr(element, 'update'):
                element.update(delta_time)

        # --- PREVIEW COOLDOWN TIMER ---
        if s.preview_cooldown_timer > 0:
            s.preview_cooldown_timer -= delta_time

        # If a sound volume change occurred and our cooldown is ready, play sound
        if s.sound_changed_flag and s.preview_cooldown_timer <= 0:
            # Calls your audio manager to trigger a quick test blip/noise
            if hasattr(s.launcher.audio_manager, 'play_sound_preview'):
                s.launcher.audio_manager.play_sound_preview()
            elif hasattr(s.launcher.audio_manager, 'play_preview_sound'):
                s.launcher.audio_manager.play_preview_sound()

            s.sound_changed_flag = False
            s.preview_cooldown_timer = s.preview_cooldown_duration

    def draw(s, window):
        """Draw the audio controls and highlight the focused element."""
        has_focus = (s.launcher.state_manager.ui_focus == 'content')
        
        for i, element in enumerate(s.ui_elements):
            is_selected = (i == s.selected_index)
            
            if hasattr(element, 'draw'):
                try:
                    element.draw(window, is_focused=(is_selected and has_focus))
                except TypeError:
                    element.draw(window)