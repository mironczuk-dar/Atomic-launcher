#IMPORTING LIBRARIES
import pygame
from sys import exit
from os import environ
import platform
import socket

#IMPORTING FILES
from settings import *
from Tools.data_loading_tools import load_data, save_data

#IMPROTING STATES AND STATE MANAGERS
from Tools.game_installer import GameInstaller
from States.state_manager import StateManager
from UI.sidebar import Sidebar
from States.library import Library
from Store.store import Store
from States.options import Options
from Store.game_preview import GamePreview


#LAUNCHER CLASS
class Launcher:

    #INFORMATION ABOUT THE LAUNCHER
    def __str__(s):
        return'''
        A launcher for Pygame applications.
        '''
    
    #CONSTRUCTOR
    def __init__(s):

        #CHECKING THE SYSTEM THE DEVICE IS RUNNING ON
        s.system = s.checking_operating_system()

        #CHECKING INTERNET ACCESS
        s.online_mode = s.checking_internet_connection()

        #INITALIZING PYGAME
        pygame.init()

        #LOADING IN LAUNCHER DATA
        s.loading_in_launcher_data()

        #SETTING UP THE DISPLAY
        s.setting_up_display()

        #INITALIZING DISPLAY
        s.display = pygame.display.set_mode((s.window_data['width'], s.window_data['height']), s.flags)
        s.window = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('[ATOMIC LAUNCHER]')

        #INITALIZING CLOCK
        s.clock = pygame.time.Clock()
        s.fps = s.window_data['fps']

        #CREATING THE GAME INSTALLER
        s.installer = GameInstaller(GAMES_DIR)

        #CREATING STATE MANAGER AND STATES
        s.state_manager = StateManager(s)
        s.creating_states()
        s.sidebar = Sidebar(s)

        #GAME PROCESS
        s.game_process = None
        s.game_running = False

    #METHOD FOR CHECKING OPERATING SYSTEM
    def checking_operating_system(s):
        s.system = platform.system()
    
    #METHOD FOR CHECKING INTERNET CONNECTION
    def checking_internet_connection(s, timeout = 2):
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except OSError:
            return False

    #METHOD FOR LOADING IN LAUNCHER DATA
    def loading_in_launcher_data(s):
        s.window_data = load_data(WINDOW_DATA_PATH, DEFUALT_WINDOW_DATA)
        s.audio_data = load_data(AUDIO_DATA_PATH, DEFAULT_AUDIO_DATA)
        s.theme_data = load_data(THEMES_DATA_PATH, DEFAULT_THEME_DATA)
        s.performance_settings_data = load_data(PERFORMANCE_SETTINGS_DATA_PATH, DEFAULT_PERFORMANCE_SETTINGS_DATA)
        s.controlls_data = load_data(CONTROLLS_DATA_PATH, DEFAULT_CONTROLLS_DATA)

    #METHOD FOR CREATING STATE AND OS ELEMENTS (LIBRARY, STORE, SETTINGS, ...)
    def creating_states(s):
        s.state_manager.add_state('Library', Library(s))
        s.state_manager.add_state('Store', Store(s))
        s.state_manager.add_state('Options', Options(s))
        s.state_manager.add_state('Game preview', GamePreview(s))

        #SETTING CURRENT STATE
        s.state_manager.set_state('Library')

    #METHOD FOR SCALING MOUSE POSITTION
    def get_scaled_mouse_pos(s):
        mouse_x, mouse_y = pygame.mouse.get_pos()

        scaled_x = mouse_x * (s.screen.get_width() / s.display.get_width())
        scaled_y = mouse_y * (s.screen.get_height() / s.display.get_height())

        return int(scaled_x), int(scaled_y)
    
    #METHOD FOR SETTING UP THE DISPLAY
    def setting_up_display(s):
        s.fullscreen = s.window_data['fullscreen']
        s.last_window_size = (s.window_data['width'], s.window_data['height'])

        if s.fullscreen:
            s.flags = pygame.FULLSCREEN
        else:
            s.flags = pygame.RESIZABLE
     
    #METHOD FOR SAVING THE LAUNCHER SETTINGS
    def save(s):
        save_data(s.window_data, WINDOW_DATA_PATH)
        save_data(s.audio_data, AUDIO_DATA_PATH)
        save_data(s.theme_data, THEMES_DATA_PATH)
        save_data(s.performance_settings_data, PERFORMANCE_SETTINGS_DATA_PATH)
        save_data(s.controlls_data, CONTROLLS_DATA_PATH)

    #METHOD FOR HANDLING EVENTS
    def handling_events(s):
        events = pygame.event.get()


        for event in events:

            #CLOSING THE LAUNCHER IF WINDOW IS CLOSED
            if event.type == pygame.QUIT:
                s.save()
                pygame.quit()
                exit()

            #HANDLING WINDOW RESIZE
            if event.type == pygame.VIDEORESIZE and not s.fullscreen:

                #SAVING THE LAST NOT FULLSCREENED WINDOW SIZE
                s.window_data['width'] = event.w
                s.window_data['height'] = event.h

                #SETTING FULLSCREEN
                s.display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                s.screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))

                #SAVING CHANGES
                save_data(s.window_data, WINDOW_DATA_PATH)

            #USER BUTTON INPUT
            if event.type == pygame.KEYDOWN:

                #CLOSING LAUNCHER IF 'ESCAPE' BUTTON PRESSED
                if event.key == pygame.K_ESCAPE:
                    s.save()
                    pygame.quit()
                    exit()

                #TOGGLING FULLSCREEN MODE
                if event.key == pygame.K_9:
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

        #PASSING EVENTS TO THE CURRENT STATE
        s.state_manager.handling_events(events)

    #METHOD FOR UPDATING THE LAUNCHER
    def update(s):
        # LOWERING FPS IF THERE'S A GAME RUNNING
        if s.game_running:
            s.delta_time = s.clock.tick(s.performance_settings_data['decrease_launcher_fps_when_game_active']) / 1000
        else:
            if s.fps is None:
                s.delta_time = s.clock.tick() / 1000
            else:
                s.delta_time = s.clock.tick(s.fps) / 1000


        # UPDATING CURRENT STATE
        s.state_manager.update(s.delta_time)

    #METHOD FOR DRAWING THE LAUNCHER
    def draw(s):

        #FILLING THE WINDOW BLACK
        s.window.fill((255,0,0))

        #DRAWING THE CURRENT STATE
        s.state_manager.draw(s.window)

        #TRANSFORMING THE WINDOW TO PROPER DISPLAY | S.WINDOW ---> S.DISPLAY
        scaled_window = pygame.transform.scale(s.window, (s.display.get_width(), s.display.get_height()))

        #BLITTING THE SCALED WINDOW TO THE DISPLAY
        s.display.blit(scaled_window, (0,0))

        #UPDATING THE DISPLAY
        pygame.display.update()

    #METHOD FOR RUNNING THE LAUNCHER
    def run(s):

        #MAIN APPLICATION LOOP
        while True:

            #HANDILING EVENTS
            s.handling_events()

            #UPDATING THE LAUNCHER
            s.update()

            #DRAWING THE LAUNCHER
            s.draw()

#RUNNING THE LAUNCHER ONLY FROM THE MAIN FILE
if __name__ == '__main__':
    
    try:

        #RUNNING THE LAUNCHER
        launcher = Launcher()
        print(launcher)
        launcher.run()

    #CATCHING ANY ERRORS SO THE USER CAN TROUBLESHOOT
    except Exception as e:
        import traceback
        traceback.print_exc()
        input('Press [ENTER] to exit...')