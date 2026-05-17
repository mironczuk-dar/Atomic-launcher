#IMPORTING LIBRARIES
import pygame

#IMPORTING FILES
from settings import get_contrast_text_color
from Tools.data_loading_tools import save_data
from settings import THEME_LIBRARY
from settings import WINDOW_WIDTH
from settings import THEME_LIBRARY, WINDOW_WIDTH
from UI.options_ui.generic_options_tab import GenericOptionsTab

class AudioSettings(OptionsSection):

    def __init__(s, game):

        super().__init__(game)
        s.setup()


    def setup(s):

        slider_size = (800, 40)
        music_slider = Slider(
            s.game,
            pos=(WINDOW_WIDTH/2-slider_size[0]/2, WINDOW_HEIGHT/3),
            size=slider_size,
            min_val=0,
            max_val=1,
            start_val=s.game.audio_data.get("music_volume", 1.0),
            on_change=lambda v: s.game.audio_manager.set_music_volume(v)
        )

        sound_slider = Slider(
            s.game,
            pos=(WINDOW_WIDTH/2-slider_size[0]/2, WINDOW_HEIGHT/3*2),
            size=(slider_size),
            min_val=0,
            max_val=1,
            start_val=s.game.audio_data.get("sound_volume", 1.0),
            on_change=lambda v: s.game.audio_manager.set_sound_volume(v)
        )

        music_toggle = GenericToggleButton(
            s.game,
            size=(220, 50),
            pos=(WINDOW_WIDTH/2, WINDOW_HEIGHT/3+slider_size[1]+50),
            text="Music",
            action=s.game.audio_manager.toggle_music
        )

        sound_toggle = GenericToggleButton(
            s.game,
            size=(220, 50),
            pos=(WINDOW_WIDTH/2, WINDOW_HEIGHT/3*2+slider_size[1]+50),
            text="Sound",
            action=s.game.audio_manager.toggle_sound
        )

        s.ui_elements.extend([
            music_slider,
            music_toggle,
            sound_slider,
            sound_toggle
        ])


class AudioOptionsTab(GenericOptionsTab):

    def __init__(s, launcher):
        super().__init__(launcher)
        s.update_visuals()
        
        s.initial_pos = (WINDOW_WIDTH * 0.15, 250)
        s.col_width = 350
        s.button_height = 80
        s.spacing = 15
        
        s.font = pygame.font.SysFont(None, 45, False)
        s.header_font = pygame.font.SysFont(None, 55, True)

        # Opcje głośności do wyboru
        s.volume_levels = [0, 20, 40, 60, 80, 100]
        
        # Nawigacja
        s.active_col = 'music'  # 'music' lub 'effects'
        s.music_index = 0
        s.effects_index = 0

    def update_visuals(s):
        s.current_theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]

    def handling_events(s, events, ctrl):
        if s.launcher.state_manager.ui_focus != 'content':
            return

        # 1. Capture the single KEYDOWN event from the queue
        current_key = None
        for event in events:
            if event.type == pygame.KEYDOWN:
                current_key = event.key
                break 

        if current_key is None:
            return

        # 2. Map current_key to logical navigation
        is_up = current_key == ctrl['up']
        is_down = current_key == ctrl['down']
        is_left = current_key == ctrl['left']
        is_right = current_key == ctrl['right']
        is_confirm = current_key in [ctrl['action_a'], pygame.K_RETURN]