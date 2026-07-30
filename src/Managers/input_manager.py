import pygame

class InputManager:
    def __init__(s, game):
        s.game = game

        s.actions_pressed = set()
        s.actions_just_pressed = set()
        s.actions_just_released = set()

        s.last_key_down = None

        # INITIALIZING JOYSTICK
        pygame.joystick.init()
        s.joystick = {}
        s._detect_joysticks()

        # ANALOG DEADZONE THRESHOLD (PREVENTS STICK DRIFT)
        s.DEADZONE = 0.2
        
        # MOUSE CURSOR SPEED (Pixels per second)
        s.cursor_speed = 1200 

        # TRACK D-PAD HAT STATES TO AVOID REPEAT TRIGGER ISSUES
        s.hat_states = {'up': False, 'down': False, 'left': False, 'right': False}

        # INITIALIZING GPIO BUTTONS (Fails gracefully on non-Pi devices)
        s.gpio_buttons = {}         # Maps action_name -> list of gpiozero.Button objects
        s.gpio_previous_state = {}  # Maps action_name -> bool

        try:
            from gpiozero import Button
            
            gpio_config = s.game.controls_data.get('gpio', {})
            
            # Iterate through all sub-groups inside 'gpio' (e.g., 'buttons', 'trackpad')
            for sub_group_name, pin_map in gpio_config.items():
                if isinstance(pin_map, dict):
                    for action, pin in pin_map.items():
                        if pin is not None:
                            if action not in s.gpio_buttons:
                                s.gpio_buttons[action] = []
                                s.gpio_previous_state[action] = False
                            
                            # Append the button instance to the action's list
                            s.gpio_buttons[action].append(Button(pin))
                            
            print(f"Successfully initialized GPIO input mapping for {len(s.gpio_buttons)} actions.")
        except ImportError:
            print("gpiozero library not found. Skipping GPIO setup.")
        except Exception as e:
            print(f"Could not initialize GPIO: {e}")

    def _trigger_action(s, action):
        """Helper method to trigger an action based on analog stick movement."""
        s.actions_pressed.add(action)
        s.actions_just_pressed.add(action)

    def _set_action_state(s, action, is_active):
        """Update pressed/released state for a single action while preserving just-released timing."""
        if is_active:
            s._trigger_action(action)
        else:
            was_active = action in s.actions_pressed
            if was_active:
                s.actions_just_released.add(action)
            s.actions_pressed.discard(action)

    # QUERY METHODS FOR ACTION STATES
    def is_pressed(s, action): return action in s.actions_pressed
    def just_pressed(s, action): return action in s.actions_just_pressed
    def just_released(s, action): return action in s.actions_just_released

    def _detect_joysticks(s):
        """Detects and initializes connected joysticks."""
        s.joystick = {}
        for i in range(pygame.joystick.get_count()):
            js = pygame.joystick.Joystick(i)
            js.init()
            s.joystick[js.get_id()] = js
            print(f"Joystick {js.get_name()} (ID: {js.get_id()}) initialized.")

    def update(s, events):
        """Updates the state of the input manager."""
        s.actions_just_pressed.clear()
        s.actions_just_released.clear()

        # CONFIG MAPPINGS
        kbd_config = s.game.controls_data.get('keyboard', {})
        key_to_action = {v: k for k, v in kbd_config.items()}

        pad_config = s.game.controls_data.get('gamepad', {})
        button_to_action = {v: k for k, v in pad_config.items()}

        # Fetch 'trackpad' config, with a fallback to 'mouse' just in case
        trackpad_config = s.game.controls_data.get('trackpad', s.game.controls_data.get('mouse', {}))
        mouse_to_action = {v: k for k, v in trackpad_config.items()}

        # PROCESSING EVENT QUEUE (KEYBOARD, GAMEPAD, AND TRACKPAD)
        for event in events:
            # HANDLING CONTROLLER CONNECTION/DISCONNECTION EVENTS
            if event.type == pygame.JOYDEVICEADDED or event.type == pygame.JOYDEVICEREMOVED:
                s._detect_joysticks()

            # KEYBOARD INPUTS
            elif event.type == pygame.KEYDOWN:
                s.last_key_down = event.key
                if event.key in key_to_action:
                    action = key_to_action[event.key]
                    s.actions_pressed.add(action)
                    s.actions_just_pressed.add(action)

            elif event.type == pygame.KEYUP and event.key in key_to_action:
                action = key_to_action[event.key]
                s.actions_pressed.discard(action)
                s.actions_just_released.add(action)

            # GAMEPAD BUTTON INPUTS (Standard SDL Buttons)
            elif event.type == pygame.JOYBUTTONDOWN and event.button in button_to_action:
                action = button_to_action[event.button]
                s.actions_pressed.add(action)
                s.actions_just_pressed.add(action)

            elif event.type == pygame.JOYBUTTONUP and event.button in button_to_action:
                action = button_to_action[event.button]
                s.actions_pressed.discard(action)
                s.actions_just_released.add(action)

            # GAMEPAD D-PAD (HAT) MOTION (XBOX / 8BITDO DIRECTIONAL PAD)
            elif event.type == pygame.JOYHATMOTION:
                hat_x, hat_y = event.value
                
                directions = {
                    'up': hat_y == 1,
                    'down': hat_y == -1,
                    'left': hat_x == -1,
                    'right': hat_x == 1
                }

                for dir_name, active in directions.items():
                    was_active = s.hat_states[dir_name]
                    if active and not was_active:
                        s.actions_pressed.add(dir_name)
                        s.actions_just_pressed.add(dir_name)
                    elif not active and was_active:
                        s.actions_pressed.discard(dir_name)
                        s.actions_just_released.add(dir_name)
                    s.hat_states[dir_name] = active
            
            # TRACKPAD TAP / MOUSE BUTTON CLICKS
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in mouse_to_action:
                action = mouse_to_action[event.button]
                s.actions_pressed.add(action)
                s.actions_just_pressed.add(action)

            elif event.type == pygame.MOUSEBUTTONUP and event.button in mouse_to_action:
                action = mouse_to_action[event.button]
                s.actions_pressed.discard(action)
                s.actions_just_released.add(action)

        # PROCESSING ANALOG STICKS (POLLING AXIS VALUES FOR CONTINUOUS MOVEMENT)
        s._update_analog_axes()

        # POLLING RASPBERRY PI GPIO BUTTONS
        s._update_gpio_buttons()

    def get_last_key_down(s):
        key = s.last_key_down
        s.last_key_down = None  # Consume it once read
        return key

    def _update_analog_axes(s):
        for joy in s.joystick.values():
            
            # 1. LEFT STICK MOVEMENT (Axes 0 and 1)
            axis_x = joy.get_axis(0)
            axis_y = joy.get_axis(1)

            # HORIZONTAL MOVEMENT
            s._set_action_state('left', axis_x < -s.DEADZONE)
            s._set_action_state('right', axis_x > s.DEADZONE)

            # VERTICAL MOVEMENT
            s._set_action_state('up', axis_y < -s.DEADZONE)
            s._set_action_state('down', axis_y > s.DEADZONE)
                
            # 2. RIGHT STICK MOUSE CONTROL (Axes 2 and 3)
            if joy.get_numaxes() >= 4:
                right_axis_x = joy.get_axis(2)
                right_axis_y = joy.get_axis(3)
                
                move_x = 0
                move_y = 0
                
                if abs(right_axis_x) > s.DEADZONE:
                    move_x = right_axis_x
                if abs(right_axis_y) > s.DEADZONE:
                    move_y = right_axis_y
                    
                if move_x != 0 or move_y != 0:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    delta = s.game.delta_time
                    
                    new_x = mouse_x + (move_x * s.cursor_speed * delta)
                    new_y = mouse_y + (move_y * s.cursor_speed * delta)
                    
                    # GET WINDOW DIMENSIONS TO CLAMP CURSOR
                    display_w, display_h = s.game.display.get_size()

                    # CLAMP WITHIN WINDOW BOUNDS (0 to display_size - 1)
                    clamped_x = max(0, min(int(new_x), display_w - 1))
                    clamped_y = max(0, min(int(new_y), display_h - 1))
                    
                    pygame.mouse.set_pos((clamped_x, clamped_y))

    def _update_gpio_buttons(s):
        """Polls Raspberry Pi GPIO pins and updates action states."""
        if not s.gpio_buttons:
            return

        for action, button_list in s.gpio_buttons.items():
            # Action is active if AT LEAST ONE connected pin is currently pressed
            is_pressed = any(btn.is_pressed for btn in button_list)
            was_pressed = s.gpio_previous_state[action]

            if is_pressed:
                s.actions_pressed.add(action)
                if not was_pressed:
                    s.actions_just_pressed.add(action)
            else:
                s.actions_pressed.discard(action)
                if was_pressed:
                    s.actions_just_released.add(action)
                    
            s.gpio_previous_state[action] = is_pressed