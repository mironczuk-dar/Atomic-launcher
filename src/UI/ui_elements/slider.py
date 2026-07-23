"""Horizontal slider control for numeric settings.

This slider supports mouse dragging and keyboard/controller adjustment
when the slider has focus. It is used by audio and performance settings
for volume, speed, and other tunable values.
"""

import pygame


class Slider:
    """Slider widget supporting discrete step changes and drag input."""

    # ==========================================
    # CONSTRUCTOR
    # ==========================================
    def __init__(s, game, pos, size, min_val=0.0, max_val=1.0, start_val=0.5, step=0.05, on_change=None):

        s.game = game

        s.x, s.y = pos
        s.width, s.height = size

        s.track_rect = pygame.Rect(s.x, s.y, s.width, s.height)

        s.min_val = min_val
        s.max_val = max_val
        s.value = start_val

        s.step = step

        s.on_change = on_change

        # UI navigation support
        s.is_selected = False

        # Handle
        s.handle_width = 20
        s.handle_height = s.height + 10

        s.dragging = False

        s.handle_rect = pygame.Rect(0,0,s.handle_width,s.handle_height)

        s.update_handle_position()


    # ==========================================
    # HANDLE POSITION
    # ==========================================
    def update_handle_position(s):

        ratio = (s.value - s.min_val) / (s.max_val - s.min_val)

        handle_x = s.x + int(ratio * (s.width - s.handle_width))

        s.handle_rect.topleft = (
            handle_x,
            s.y - (s.handle_height - s.height)//2
        )


    # ==========================================
    # VALUE CHANGE
    # ==========================================
    def change_value(s, amount):

        s.value += amount

        s.value = max(s.min_val, min(s.value, s.max_val))

        s.update_handle_position()

        if s.on_change:
            s.on_change(s.value)


    # ==========================================
    # KEYBOARD ACTIVATION
    # ==========================================
    def activate(s):
        pass


    def handling_events(s, events, ctrl=None):
        """Process mouse and keyboard/controller events for the slider."""
        engine = s.game if hasattr(s, 'game') else s.launcher
        input_manager = getattr(engine, 'input_manager', None)
        mouse_pos = engine.get_scaled_mouse_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and s.handle_rect.collidepoint(mouse_pos):
                    s.dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    s.dragging = False

        if s.is_selected and input_manager is not None:
            if input_manager.just_pressed('right'):
                s.change_value(s.step)
            elif input_manager.just_pressed('left'):
                s.change_value(-s.step)


        # =============================
        # DRAGGING UPDATE
        # =============================
        if s.dragging:
            new_x = max(
                s.x,
                min(mouse_pos[0] - s.handle_width//2, s.x + s.width - s.handle_width)
            )
            ratio = (new_x - s.x) / (s.width - s.handle_width)
            s.value = s.min_val + ratio * (s.max_val - s.min_val)
            s.update_handle_position()

            if s.on_change:
                s.on_change(s.value)


    def update(s, delta_time):
        """Advance timed state for the slider if needed."""
        pass


    # ==========================================
    # DRAW
    # ==========================================
    def draw(s, surface):

        # TRACK
        pygame.draw.rect(surface,(120,120,120),s.track_rect, border_radius=4)

        # FILL
        ratio = (s.value - s.min_val) / (s.max_val - s.min_val)
        fill_width = int(ratio * s.width)

        pygame.draw.rect(
            surface,
            (60,200,120),
            (s.x, s.y, fill_width, s.height),
            border_radius=4
        )

        # HANDLE COLOR
        handle_color = (240,240,240)

        if s.is_selected:
            handle_color = (255,230,120)

        pygame.draw.rect(
            surface,
            handle_color,
            s.handle_rect,
            border_radius=4
        )