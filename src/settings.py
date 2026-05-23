#IMPORTING LIBRARIES
import pygame
from os.path import join, dirname, abspath

#ABSOLUTE PATH
# abspath(__file__) -> .../Atomic launcher/code/settings.py
# dirname(...)      -> .../Atomic launcher/code
# dirname(dirname(...)) -> .../Atomic launcher (ROOT)
BASE_DIR = dirname(dirname(abspath(__file__)))
GAMES_DIR = join(BASE_DIR, 'games')


#GAME LIBRARY SETTINGS
GAME_LIBRARY_DATA_PATH = join(BASE_DIR, 'data', 'game_library_data.json')
DEFAULT_GAME_LIBRARY_DATA = {
    'favorites' : [],
    'last_launched' : [],
    'navigation_tutorial_shown' : False
}

#CONTROLLS SETTIGNS
CONTROLLS_DATA_PATH = join(BASE_DIR, 'data', 'controlls_data.json')
DEFAULT_CONTROLLS_DATA = {
    'keyboard' : {
    'up' : pygame.K_UP,
    'down' : pygame.K_DOWN,
    'left' : pygame.K_LEFT,
    'right' : pygame.K_RIGHT,
    'options' : pygame.K_TAB,
    'action_a' : pygame.K_r,
    'action_b' : pygame.K_e,
    'action_x' : pygame.K_w,
    'action_y' : pygame.K_q
},
    'controller' : {
    'up' : 0,
    'down' : 1,
    'left' : 2,
    'right' : 3,
    'options' : 4,
    'action_a' : 5,
    'action_b' : 6,
    'action_x' : 7,
    'action_y' : 8
}}

#RASPBERRY PI GPIO CONTROLLER SETTINGS
GPIO_CONTROLLS_DATA_PATH = join(BASE_DIR, 'data', 'gpio_controlls_data.json')
DEFAULT_GPIO_CONTROLLS_DATA = {
    'up' : 17,
    'down' : 27,
    'left' : 22,
    'right' : 23,
    'options' : 24,
    'action_a' : 5,
    'action_b' : 6,
    'action_x' : 13,
    'action_y' : 19
}

#SCREEN / WINDOW SETTINGS
WINDOW_DATA_PATH = join(BASE_DIR, 'data', 'window_data.json')
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
DEFUALT_WINDOW_DATA = {
    'width' : 1280,
    'height' : 720,
    'fullscreen' : False,
    'fps' : 60,
    'show_fps' : False,
}

#AUDIO DATA
AUDIO_DATA_PATH = join(BASE_DIR, 'data', 'audio_data.json')
DEFAULT_AUDIO_DATA = {
    'music_on' : True,
    'sound_on' : True,
    'sound_volume' : 1,
    'music_volume' : 0.25
}

#PERFORMANCE SETTINGS
PERFORMANCE_SETTINGS_DATA_PATH = join(BASE_DIR, 'data', 'performance_settings_data.json')
DEFAULT_PERFORMANCE_SETTINGS_DATA = {
    'turn_off_launcher_when_game_active' : False,
    'decrease_launcher_fps_when_game_active' : 40
}

#THEMES DATA
THEMES_DATA_PATH = join(BASE_DIR, 'data', 'themes_data.json')
DEFAULT_THEME_DATA = {
    'current_theme' : 'Slate Bloom'
}
THEME_LIBRARY = {
    'Aurora' : {'colour_1' : "#0F1B3C",
                'colour_2' : "#84A5FF",
                'colour_3' : "#2B3A6A",
                'colour_4' : "#D7E0FF"},

    'Solar Flare' : {'colour_1' : "#3D180F",
                     'colour_2' : "#FF9C42",
                     'colour_3' : "#AA542C",
                     'colour_4' : "#F6E0C7"},

    'Forest Dusk' : {'colour_1' : "#102C1F",
                     'colour_2' : "#6BB78E",
                     'colour_3' : "#3E6752",
                     'colour_4' : "#DCEFE2"},

    'Ocean Depths' : {'colour_1' : "#04304D",
                      'colour_2' : "#64B2E4",
                      'colour_3' : "#1C5E80",
                      'colour_4' : "#D7EDFF"},

    'Neon Grid' : {'colour_1' : "#140B2A",
                   'colour_2' : "#FF5EBF",
                   'colour_3' : "#7E62E8",
                   'colour_4' : "#E9E1FF"},

    'Slate Bloom' : {'colour_1' : "#232F41",
                     'colour_2' : "#7AA1D2",
                     'colour_3' : "#4F6D8B",
                     'colour_4' : "#EFF4FA"},

    'High Contrast' : {'colour_1' : "#000000",
                       'colour_2' : "#FFFF00",
                       'colour_3' : "#FFFFFF",
                       'colour_4' : "#444444"},
}


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_contrast_text_color(bg_color):
    if isinstance(bg_color, str):
        r, g, b = hex_to_rgb(bg_color)
    else:
        r, g, b = bg_color

    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return (0, 0, 0) if luminance > 150 else (255, 255, 255)
