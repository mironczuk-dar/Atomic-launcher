"""
Atomic Launcher - main entrypoint

This module initializes and runs the Atomic Launcher application built with
Pygame. It configures platform-specific features (GPIO on Raspberry Pi),
loads application data and assets, manages application states, and runs the
main event/update/draw loop.

The `Launcher` class encapsulates the runtime environment and lifecycle of
the launcher.
"""

import pygame
from sys import exit
import platform
import socket
import threading

from settings import *
from Tools.data_loading_tools import load_data, save_data

# State machines, managers and UI states
from Machines.game_installing_machine import GameInstaller
from Managers.audio_manager import AudioManager
from Managers.state_manager import StateManager
from Managers.input_manager import InputManager
from UI.ui_elements.sidebar import Sidebar
from States.library import Library
from States.store import Store
from States.options import Options
from UI.store_ui.game_preview import GamePreview

# Helpers that import and prepare game assets and audio in background
from Machines.asset_importing_machine import load_audio, load_assets


class Launcher:
    """Encapsulates the launcher lifecycle, configuration and main loop.

    The class is responsible for initializing platform-specific components,
    loading persistent settings, starting a background asset-loading thread,
    creating the game installer and state manager, and running the main
    application loop.
    """

    def __str__(s):
        return 'Atomic Launcher - runtime controller for the Pygame UI'

    def __init__(s):
        """Initialize runtime, configuration, managers and surfaces."""

        # platform and online status
        s.system = s.checking_operating_system()
        s.online_mode = s.checking_internet_connection()

        # initialize pygame and load persistent configuration
        pygame.init()
        s.loading_in_launcher_data()

        # configure display flags (fullscreen or resizable)
        s.setting_up_display()

        # initialize display surfaces and window properties
        s.display = pygame.display.set_mode((s.window_data['width'], s.window_data['height']), s.flags)
        s.window = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        s.screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.mouse.set_visible(False)
        pygame.display.set_caption('[ATOMIC LAUNCHER]')
        pygame.display.set_icon(pygame.image.load(join(BASE_DIR, 'assets', 'icon.png')))

        # timing
        s.clock = pygame.time.Clock()
        s.fps = s.window_data['fps']

        # background thread to import assets without blocking startup
        s.assets_loaded = False
        s.assets_thread = threading.Thread(target=s.import_assets, daemon=True)
        s.assets_thread.start()

        # installer and state management
        s.installer = GameInstaller(GAMES_DIR)
        s.setting_up_managers()
        s.creating_states()
        s.sidebar = Sidebar(s)

        # process tracking for launched games
        s.game_process = None
        s.game_running = False

    def import_assets(s):
        """Load audio and other assets in background threads.

        This uses a small thread pool to parallelize expensive I/O so the UI
        can become responsive quickly while assets finish loading.
        """
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(load_audio, s),
                executor.submit(load_assets, s),
            ]
            # Wait for both tasks to complete and propagate exceptions
            for f in futures:
                f.result()

        s.assets_loaded = True
        print('Assets loaded')

    def checking_operating_system(s):
        """Detect the operating system and whether this is a Raspberry Pi.

        Returns a human-readable OS name. Sets `s.is_pi` flag when a
        Raspberry Pi device tree model file is found.
        """
        s.os_type = platform.system()
        try:
            with open('/proc/device-tree/model', 'r') as f:
                s.is_pi = 'Raspberry Pi' in f.read()
        except FileNotFoundError:
            s.is_pi = False

        return 'Raspberry Pi Os' if s.is_pi else s.os_type

    def checking_internet_connection(s, timeout=2):
        """Quick check for outgoing internet connectivity.

        Attempts to open a socket to a public DNS server. This provides
        a simple online/offline boolean used by other components.
        """
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except OSError:
            return False

    def loading_in_launcher_data(s):
        """Load persistent configuration and launcher data from disk."""
        s.window_data = load_data(WINDOW_DATA_PATH, DEFUALT_WINDOW_DATA)
        s.audio_data = load_data(AUDIO_DATA_PATH, DEFAULT_AUDIO_DATA)
        s.theme_data = load_data(THEMES_DATA_PATH, DEFAULT_THEME_DATA)
        s.performance_settings_data = load_data(PERFORMANCE_SETTINGS_DATA_PATH, DEFAULT_PERFORMANCE_SETTINGS_DATA)
        s.controlls_data = load_data(CONTROLS_DATA_PATH, DEFAULT_CONTROLS_DATA)
        s.controls_data = s.controlls_data
        s.game_library_data = load_data(GAME_LIBRARY_DATA_PATH, DEFAULT_GAME_LIBRARY_DATA)

    def creating_states(s):
        """Instantiate application states and set the initial state."""
        s.state_manager.add_state('Library', Library(s))
        s.state_manager.add_state('Store', Store(s))
        s.state_manager.add_state('Options', Options(s))
        s.state_manager.add_state('Game preview', GamePreview(s))
        s.state_manager.set_state('Library')

    def get_scaled_mouse_pos(s):
        """Return mouse position scaled from display space to virtual window.

        The launcher renders to a fixed virtual resolution (`s.window`) and
        scales to the actual display surface. This helper converts mouse
        coordinates from the real display to the virtual coordinate space.
        """
        mouse_x, mouse_y = pygame.mouse.get_pos()
        scaled_x = mouse_x * (s.screen.get_width() / s.display.get_width())
        scaled_y = mouse_y * (s.screen.get_height() / s.display.get_height())
        return int(scaled_x), int(scaled_y)

    def setting_up_managers(s):
        """Create top-level managers used across the application."""
        s.state_manager = StateManager(s)
        s.audio_manager = AudioManager(s)
        s.input_manager = InputManager(s)
        s.inpute_manager = s.input_manager

    def setting_up_display(s):
        """Configure initial display flags and remember last window size."""
        s.fullscreen = s.window_data['fullscreen']
        s.last_window_size = (s.window_data['width'], s.window_data['height'])
        s.flags = pygame.FULLSCREEN if s.fullscreen else pygame.RESIZABLE

    def save(s):
        """Persist launcher state and configuration to disk."""
        save_data(s.window_data, WINDOW_DATA_PATH)
        save_data(s.audio_data, AUDIO_DATA_PATH)
        save_data(s.theme_data, THEMES_DATA_PATH)
        save_data(s.performance_settings_data, PERFORMANCE_SETTINGS_DATA_PATH)
        save_data(s.controlls_data, CONTROLS_DATA_PATH)
        save_data(s.game_library_data, GAME_LIBRARY_DATA_PATH)

    def handling_events(s):
        """Process Pygame events and forward them to the active state.

        This method also polls optional GPIO input, blocks unwanted mouse
        events (the launcher uses controller/keyboard navigation), and
        handles window lifecycle events such as resize and quit.
        """
        # ignore raw mouse motion and clicks; launcher navigation is keyboard/controller-driven
        pygame.event.set_blocked([pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP])

        events = pygame.event.get()
        if hasattr(s, 'input_manager'):
            s.input_manager.update(events)

        for event in events:
            if event.type == pygame.QUIT:
                s.save()
                pygame.quit()
                exit()

            if event.type == pygame.VIDEORESIZE and not s.fullscreen:
                # store new non-fullscreen size and recreate display surface
                s.window_data['width'] = event.w
                s.window_data['height'] = event.h
                s.display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                s.screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                save_data(s.window_data, WINDOW_DATA_PATH)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    s.save()
                    pygame.quit()
                    exit()

                if event.key == pygame.K_9:
                    # toggle fullscreen and persist choice
                    s.fullscreen = not s.fullscreen
                    s.window_data['fullscreen'] = s.fullscreen
                    if s.fullscreen:
                        s.last_window_size = (s.display.get_width(), s.display.get_height())
                        s.flags = pygame.FULLSCREEN
                        s.display = pygame.display.set_mode((s.window_data['width'], s.window_data['height']), s.flags)
                    else:
                        s.flags = pygame.RESIZABLE
                        s.display = pygame.display.set_mode(s.last_window_size, s.flags)
                        s.window_data['width'], s.window_data['height'] = s.last_window_size
                    save_data(s.window_data, WINDOW_DATA_PATH)

        # forward events to the current application state for domain handling
        s.state_manager.handling_events(events)

    def update(s):
        """Update launcher state, timing and monitor any launched game process."""
        # if a child game process has ended, restore launcher audio and flags
        if s.game_running and s.game_process:
            if s.game_process.poll() is not None:
                s.game_running = False
                s.game_process = None
                s.audio_manager.unpause_music()

        # reduce launcher FPS while a game is active to save CPU if configured
        if s.game_running:
            s.delta_time = s.clock.tick(s.performance_settings_data['decrease_launcher_fps_when_game_active']) / 1000
        else:
            s.delta_time = s.clock.tick(s.fps) / 1000

        print(f"FPS: {s.clock.get_fps():.2f}", end='\r')
        s.state_manager.update(s.delta_time)

    def draw(s):
        """Render the active state to the virtual window and scale to the display."""
        # background fill (currently red for debugging; change as appropriate)
        s.window.fill((255, 0, 0))
        s.state_manager.draw(s.window)

        scaled_window = pygame.transform.scale(s.window, (s.display.get_width(), s.display.get_height()))
        s.display.blit(scaled_window, (0, 0))
        pygame.display.update()

    def run(s):
        """Enter the main application loop (event -> update -> draw)."""
        while True:
            s.handling_events()
            s.update()
            s.draw()


if __name__ == '__main__':
    try:
        launcher = Launcher()
        print(launcher)
        launcher.run()
    except KeyboardInterrupt:
        print("\nLauncher terminated manually.")
    except Exception:
        import traceback

        traceback.print_exc()
        input('Press [ENTER] to exit...')