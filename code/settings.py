#IMPORTING LIBRARIES
import pygame
from os.path import join, dirname, abspath

#ABSOLUTE PATH
BASE_DIR = dirname(abspath(__file__))

#SCREEN / WINDOW SETTINGS
WINDOW_DATA_PATH = join(BASE_DIR, '..', 'data', 'screen_data.json')
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480
DEFUALT_WINDOW_DATA = {
    'width' : 800,
    'height' : 480,
    'fullscreen' : False,
    'fps' : 60,
    'show_fps' : False
}

#AUDIO DATA
AUDIO_DATA_PATH = join(BASE_DIR, '..', 'data', 'audio_data.json')
DEFAULT_AUDIO_DATA = {
    'sound' : 1
}