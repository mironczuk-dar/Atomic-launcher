#IMPORTING LIBRARIES
import pygame
from sys import exit
from os import environ
import platform

#IMPORTING FILES
from settings import *
from Tools.data_loading_tools import load_data, save_data

#IMPROTING STATES AND STATE MANAGERS
from States.state_manager import StateManager
from States.library import Library


#LAUNCHER CLASS
class Launcher:

    #INFORMATION ABOUT THE LAUNCHER
    def __str__(s):
        return'''
        A launcher for Pygame applications.
        '''
    
    #CONSTRUCTOR
    def __init__(s):

        #POINTING TO CORRECT VIDEO DRIVERS
        s.system = s.checking_operating_system()

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

        #CREATING STATE MANAGER AND STATES
        s.state_manager = StateManager(s)
        s.creating_states()

    #METHOD FOR CHECKING OPERATING SYSTEM
    def checking_operating_system(s):
            s.system = platform.system() # RETURNS 'Linux', 'Darwin' (macOS) OR 'Windows'

            if s.system == 'Linux':
                # CHECKING IF IT'S A Raspberry Pi (Lite/No X11)
                if 'arm' in platform.machine() or 'aarch64' in platform.machine():
                    if not environ.get('DISPLAY'):
                        environ['SDL_VIDEODRIVER'] = 'kmsdrm'
                        environ['SDL_VIDEO_EGL_DRIVER'] = '/usr/lib/aarch64-linux-gnu/libEGL.so'
                        print("Running on Raspberry Pi: KMSDRM Enabled")
                    else:
                        print("Running on Raspberry Pi: X11 detected, using default drivers")
                else:
                    print("Running on standard Linux (Desktop)")

            elif s.system == 'Darwin':
                print("Running on macOS: Drivers handled by OS")
                
            elif s.system == 'Windows':
                print("Running on Windows")
    
    #METHOD FOR LOADING IN LAUNCHER DATA
    def loading_in_launcher_data(s):
        s.window_data = load_data(WINDOW_DATA_PATH, DEFUALT_WINDOW_DATA)
        s.audio_data = load_data(AUDIO_DATA_PATH, DEFAULT_AUDIO_DATA)
        s.theme_data = load_data(THEMES_DATA_PATH, DEFAULT_THEME_DATA)

    #METHOD FOR CREATING STATE AND OS ELEMENTS (LIBRARY, STORE, SETTINGS, ...)
    def creating_states(s):
        s.state_manager.add_state('Library', Library(s))

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

    #METHOD FOR HANDLING EVENTS
    def handling_events(s):
        for event in pygame.event.get():

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

    #METHOD FOR UPDATING THE LAUNCHER
    def update(s):

        #SETTING THE FPS AND DELTA TIME
        s.delta_time = s.clock.tick(s.fps) / 1000

        #UPDATING CURRENT STATE
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