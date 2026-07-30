import os
import sys
import unittest

import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from Managers.input_manager import InputManager


class DummyGame:
    def __init__(self):
        self.controls_data = {
            'keyboard': {},
            'gamepad': {},
            'mouse': {},
            'trackpad': {},
            'gpio': {},
        }
        self.display = DummyDisplay()
        self.delta_time = 0.016


class DummyDisplay:
    def get_size(self):
        return (800, 600)


class FakeJoystick:
    def __init__(self, axis_x):
        self._axis_x = axis_x
        self._axis_y = 0.0

    def get_axis(self, index):
        if index == 0:
            return self._axis_x
        if index == 1:
            return self._axis_y
        return 0.0

    def get_numaxes(self):
        return 2


class InputManagerTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.game = DummyGame()
        self.manager = InputManager(self.game)

    def test_analog_axis_release_sets_just_released(self):
        fake_joy = FakeJoystick(-0.5)
        self.manager.joystick = {0: fake_joy}

        self.manager._update_analog_axes()
        self.assertTrue(self.manager.just_pressed('left'))

        fake_joy._axis_x = 0.0
        self.manager._update_analog_axes()

        self.assertTrue(self.manager.just_released('left'))


if __name__ == '__main__':
    unittest.main()
