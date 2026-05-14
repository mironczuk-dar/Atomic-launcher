#IMPORTING LIBRARIES
import pygame

try:
    from gpiozero import Button
except ImportError:
    Button = None

#RASPBERRY PI GPIO CONTROLLER CLASS
class RaspberryPiGPIOController:

    #CONSTRUCTOR
    def __init__(s, gpio_controlls_data, keyboard_mapping):
        s.buttons = {}
        s.prev_states = {}
        s.keyboard_mapping = keyboard_mapping

        if Button is None:
            print('gpiozero not available; RaspberryPiGPIOController disabled.')
            return

        for action, pin in gpio_controlls_data.items():
            if pin is None:
                continue

            try:
                btn = Button(pin, pull_up=True)
                s.buttons[action] = btn
                s.prev_states[action] = False
            except Exception as e:
                print(f"Failed to initialize GPIO button for {action} on pin {pin}: {e}")
                s.buttons[action] = None

    def poll(s):
        if Button is None:
            return

        for action, btn in s.buttons.items():
            if btn is None:
                continue

            try:
                is_pressed = btn.is_pressed
            except Exception:
                continue

            key = s.keyboard_mapping.get(action)
            if key is None:
                continue

            if is_pressed and not s.prev_states[action]:
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': key}))
                s.prev_states[action] = True

            elif not is_pressed and s.prev_states[action]:
                pygame.event.post(pygame.event.Event(pygame.KEYUP, {'key': key}))
                s.prev_states[action] = False

    def cleanup(s):
        for btn in s.buttons.values():
            if btn is not None:
                try:
                    btn.close()
                except Exception:
                    pass