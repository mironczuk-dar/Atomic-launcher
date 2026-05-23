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
                'colour_2' : "#D7E0FF",  # Lighter, more distinct blue
                'colour_3' : "#5A7A9E",  # Mid-tone with better contrast
                'colour_4' : "#B8D0FF"},

    'Solar Flare' : {'colour_1' : "#2D1806",  # Darker base for contrast
                     'colour_2' : "#FF8F3C",  # Bright orange with better visibility
                     'colour_3' : "#CC5E2B",  # Distinct warm tone
                     'colour_4' : "#FFE4BC"},

    'Forest Dusk' : {'colour_1' : "#0A1F10",  # Dark green base
                     'colour_2' : "#98C99D",  # Bright sage (better contrast)
                     'colour_3' : "#5D876E",  # Medium with good distinction
                     'colour_4' : "#BDE8CC"},

    'Ocean Depths' : {'colour_1' : "#042539",  # Dark blue for better contrast
                      'colour_2' : "#6CBCEC",  # Brighter cyan (distinguishable)
                      'colour_3' : "#3A7E8B",  # Mid-tone with contrast
                      'colour_4' : "#CCF0FF"},

    'Neon Grid' : {'colour_1' : "#150C2F",   # Dark purple base
                   'colour_2' : "#E035F8",   # Bright magenta (more distinct)
                   'colour_3' : "#9B64FF",   # Medium violet with contrast
                   'colour_4' : "#EDE1FE"},

    'Slate Bloom' : {'colour_1' : "#232D3E", # Darker slate for better text contrast
                     'colour_2' : "#A8C9EE", # Bright blue (more visible)
                     'colour_3' : "#6B8FAF", # Medium with good distinction
                     'colour_4' : "#DCEAF7"},

    'High Contrast' : {'colour_1' : "#1A1A1A",  # Dark gray background (non-black)
                       'colour_2' : "#FFFFFF",   # White text
                       'colour_3' : "#000000",   # Black elements
                       'colour_4' : "#FFD700"},   # Gold for accents
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
