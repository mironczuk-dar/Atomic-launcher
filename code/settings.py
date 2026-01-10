#IMPORTING LIBRARIES
import pygame
from os.path import join, dirname, abspath

#ABSOLUTE PATH
# abspath(__file__) -> .../Atomic launcher/code/settings.py
# dirname(...)      -> .../Atomic launcher/code
# dirname(dirname(...)) -> .../Atomic launcher (ROOT)
BASE_DIR = dirname(dirname(abspath(__file__)))

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

#THEMES DATA
THEMES_DATA_PATH = join(BASE_DIR, '..', 'data', 'themes_data.json')
DEFAULT_THEME_DATA = {
    'current_theme' : 'Dariusz'
}
THEME_LIBRARY = {
    'Dariusz' : {'colour_1' : "#240040",
                 'colour_2' : "#FF891C",
                 'colour_3' : "#41E9FF",
                 'colour_4' : "#550096"},

    'High contrast' : {'colour_1' : "#0C0C0C",
                        'colour_2' : "#F9FF40",
                        'colour_3' : "#4DACFF",
                        'colour_4' : "#353535"}
}