#IMPORTING LIBRARIES
import pygame

#IMPORTING FILES
from settings import get_contrast_text_color
from UI.options_ui.FPS_preview_ball import Ball
from Tools.data_loading_tools import save_data
from settings import THEME_LIBRARY
from settings import WINDOW_HEIGHT, WINDOW_WIDTH, WINDOW_DATA_PATH
from settings import THEME_LIBRARY, WINDOW_WIDTH
from UI.options_ui.generic_options_tab import GenericOptionsTab

class VideoOptionsTab(GenericOptionsTab):
    def __init__(s, launcher):
        super().__init__(launcher)

        s.current_theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        
        # Responsive layout based on aspect ratio
        s.aspect_ratio = WINDOW_WIDTH / WINDOW_HEIGHT
        
        # Resolution options as ordered list for grid layout
        # Optimized for Raspberry Pi and various displays
        s.resolution_list = [
            ('Fullscreen', None),
            ('1920x1080 (16:9)', [1920, 1080]),
            ('1280x720 (16:9)', [1280, 720]),
            ('1024x600 (17:10)', [1024, 600]),
            ('800x600 (4:3)', [800, 600]),
            ('800x480 (16:9)', [800, 480]),
            ('640x480 (4:3)', [640, 480]),
            ('640x360 (16:9)', [640, 360]),
            ('720x480 (3:2)', [720, 480])
        ]
        
        # Grid layout: 2 columns on the left for resolutions
        s.resolution_cols = 2
        s.resolution_button_width = int(WINDOW_WIDTH * 0.18)
        s.resolution_button_height = int(WINDOW_HEIGHT * 0.11)
        s.resolution_spacing_x = int(WINDOW_WIDTH * 0.015)
        s.resolution_spacing_y = int(WINDOW_HEIGHT * 0.015)
        s.resolution_grid_start_x = int(WINDOW_WIDTH * 0.12)
        s.resolution_grid_start_y = int(WINDOW_HEIGHT * 0.20)
        
        # FPS column in the middle, 1 column layout
        s.fps_col_x = int(WINDOW_WIDTH * 0.55)
        s.fps_button_width = int(WINDOW_WIDTH * 0.18)
        s.fps_button_height = int(WINDOW_HEIGHT * 0.08)
        s.fps_spacing_y = int(WINDOW_HEIGHT * 0.015)
        s.fps_col_start_y = int(WINDOW_HEIGHT * 0.20)
        
        # FPS preview ball positioned to the right of FPS buttons
        s.ball_x = int(WINDOW_WIDTH * 0.88)
        s.ball_y = int(WINDOW_HEIGHT * 0.35)
        
        # Responsive fonts
        s.font = pygame.font.SysFont(None, int(WINDOW_HEIGHT * 0.06), False)
        s.value_font = pygame.font.SysFont(None, int(WINDOW_HEIGHT * 0.035), False)
        s.header_font = pygame.font.SysFont(None, int(WINDOW_HEIGHT * 0.04), True)
        s.fps_label_font = pygame.font.SysFont(None, int(WINDOW_HEIGHT * 0.03), False)
        
        s.FPS_options = ['Uncapped', 90, 60, 40, 30]

        s.FPS_preview_ball = Ball((s.ball_x, s.ball_y), s.current_theme['colour_2'])

        s.active_column = 'resolution'   # 'resolution' | 'fps'
        s.resolution_index = 0
        s.fps_index = 0

        s.selected_resolution = None
        s.selected_fps = None

    def handling_events(s, events, ctrl):
        if s.launcher.state_manager.ui_focus != 'content':
            return

        # 1. Capture the single KEYDOWN event from the queue
        current_key = None
        for event in events:
            if event.type == pygame.KEYDOWN:
                current_key = event.key
                break # We only need one key press per frame

        if current_key is None:
            return

        # 2. Map current_key to actions
        is_up = current_key == ctrl['up']
        is_down = current_key == ctrl['down']
        is_left = current_key == ctrl['left']
        is_right = current_key == ctrl['right']
        is_confirm = current_key in [ctrl['action_a'], pygame.K_RETURN]

        # --- MOVE UP / DOWN / LEFT / RIGHT ---
        if s.active_column == 'resolution':
            col = s.resolution_index % s.resolution_cols
            row = s.resolution_index // s.resolution_cols
            
            if is_up:
                if row > 0:
                    s.resolution_index -= s.resolution_cols
            elif is_down:
                if (row + 1) * s.resolution_cols + col < len(s.resolution_list):
                    s.resolution_index += s.resolution_cols
            
            if is_left:
                if col > 0:
                    s.resolution_index -= 1
            elif is_right:
                if col < s.resolution_cols - 1:
                    s.resolution_index += 1
                else:
                    s.active_column = 'fps'
        
        else:  # fps column
            if is_up:
                if s.fps_index > 0:
                    s.fps_index -= 1
            elif is_down:
                if s.fps_index < len(s.FPS_options) - 1:
                    s.fps_index += 1
            
            if is_left:
                s.active_column = 'resolution'
                row = min(s.fps_index, (len(s.resolution_list) - 1) // s.resolution_cols)
                s.resolution_index = row * s.resolution_cols + (s.resolution_cols - 1)

        # --- CONFIRM ---
        if is_confirm:
            if s.active_column == 'resolution':
                res_label, res_dims = s.resolution_list[s.resolution_index]
                if res_label == 'Fullscreen':
                    s.go_fullscreen()
                else:
                    width, height = res_dims
                    s.change_resolution(width, height)
            else:
                fps = s.FPS_options[s.fps_index]
                if fps == 'Uncapped':
                    s.update_fps(0)
                else:
                    s.update_fps(fps)

    def update(s, delta_time):
        s.FPS_preview_ball.update(delta_time)

    def draw(s, window):
        has_focus = (s.launcher.state_manager.ui_focus == 'content')

        s.FPS_preview_ball.draw(window)
        
        # Draw headers
        res_header = s.header_font.render("Resolution", True, s.current_theme['colour_2'])
        window.blit(res_header, (s.resolution_grid_start_x, s.resolution_grid_start_y - int(WINDOW_HEIGHT * 0.06)))
        
        fps_header = s.header_font.render("FPS", True, s.current_theme['colour_2'])
        window.blit(fps_header, (s.fps_col_x, s.fps_col_start_y - int(WINDOW_HEIGHT * 0.06)))

        s.draw_resolution_grid(window, has_focus)
        s.draw_FPS_buttons(window, has_focus)
        s.draw_current_settings(window)

    def get_resolution_grid_pos(s, index):
        """Calculate grid position for a resolution button."""
        row = index // s.resolution_cols
        col = index % s.resolution_cols
        x = s.resolution_grid_start_x + col * (s.resolution_button_width + s.resolution_spacing_x)
        y = s.resolution_grid_start_y + row * (s.resolution_button_height + s.resolution_spacing_y)
        return x, y

    def draw_resolution_grid(s, window, has_focus):
        for i, (res_label, res_dims) in enumerate(s.resolution_list):
            is_selected = (s.active_column == 'resolution' and i == s.resolution_index)
            is_current = s.is_current_resolution(res_label)

            bg_colour = (
                s.current_theme['colour_2']
                if is_selected and has_focus
                else s.current_theme['colour_4']
            )

            text_colour = get_contrast_text_color(bg_colour)
            x, y = s.get_resolution_grid_pos(i)

            rect = pygame.Rect(x, y, s.resolution_button_width, s.resolution_button_height)
            pygame.draw.rect(window, bg_colour, rect, border_radius=8)

            # Current resolution indicator
            if is_current:
                pygame.draw.rect(window, (0, 200, 0), rect, 4, border_radius=8)

            # Focus indicator
            if is_selected and has_focus:
                pygame.draw.rect(window, (255, 200, 0), rect, 3, border_radius=8)

            # Text - fit resolution label into button
            display_text = res_label
            text_surf = s.value_font.render(display_text, True, text_colour)
            
            # Scale down text if it's too wide
            max_text_width = s.resolution_button_width - int(WINDOW_WIDTH * 0.01)
            if text_surf.get_width() > max_text_width:
                scale_factor = max_text_width / text_surf.get_width()
                scaled_font_size = max(int(s.value_font.get_height() * scale_factor), 10)
                small_font = pygame.font.SysFont(None, scaled_font_size, False)
                text_surf = small_font.render(display_text, True, text_colour)
            
            text_rect = text_surf.get_rect(center=rect.center)
            window.blit(text_surf, text_rect)

    def draw_FPS_buttons(s, window, has_focus):
        for i, fps in enumerate(s.FPS_options):

            is_selected = (
                s.active_column == 'fps' and
                i == s.fps_index
            )

            is_current = s.is_current_fps(fps)

            bg_colour = (
                s.current_theme['colour_2']
                if is_selected and has_focus
                else s.current_theme['colour_4']
            )

            text_colour = get_contrast_text_color(bg_colour)

            x = s.fps_col_x
            y = s.fps_col_start_y + i * (s.fps_button_height + s.fps_spacing_y)
            
            rect = pygame.Rect(x, y, s.fps_button_width, s.fps_button_height)
            pygame.draw.rect(window, bg_colour, rect, border_radius=8)

            # Current FPS indicator
            if is_current:
                pygame.draw.rect(window, (0, 200, 0), rect, 4, border_radius=8)

            # Focus indicator
            if is_selected and has_focus:
                pygame.draw.rect(window, (255, 200, 0), rect, 3, border_radius=8)

            fps_text = str(fps) if fps != 'Uncapped' else 'Uncapped'
            text_surface = s.fps_label_font.render(fps_text, True, text_colour)
            text_rect = text_surface.get_rect(center=rect.center)
            window.blit(text_surface, text_rect)

    def get_fps_values(s):
        return s.FPS_options
    
    def is_current_fps(s, fps):
        if fps == 'Uncapped':
            return s.launcher.window_data['fps'] == 0
        return s.launcher.window_data['fps'] == fps

    def is_current_resolution(s, res_label):
        if res_label == 'Fullscreen':
            return s.launcher.window_data['fullscreen']

        # Find dimensions for this label
        for label, dims in s.resolution_list:
            if label == res_label and dims is not None:
                width, height = dims
                return (
                    not s.launcher.window_data['fullscreen'] and
                    s.launcher.window_data['width'] == width and
                    s.launcher.window_data['height'] == height
                )
        return False

    #METHOD FOR CHANGING THE RESOLUTION
    def change_resolution(s, width, height):

        s.launcher.window_data['width'] = width
        s.launcher.window_data['height'] = height
        s.launcher.display = pygame.display.set_mode((width, height), pygame.RESIZABLE)

        #SAVING CHANGES
        save_data(s.launcher.window_data, WINDOW_DATA_PATH)

    #METHOD FOR GOING FULLSCREEN
    def go_fullscreen(s):

        s.launcher.fullscreen = not s.launcher.fullscreen
        s.launcher.window_data['fullscreen'] = s.launcher.fullscreen

        if s.launcher.fullscreen:
            s.launcher.last_window_size = (s.launcher.display.get_width(), s.launcher.display.get_height())
            s.launcher.flags = pygame.FULLSCREEN
            s.launcher.display = pygame.display.set_mode((s.launcher.window_data['width'], s.launcher.window_data['height']), s.launcher.flags)
        else:
            s.launcher.flags = pygame.RESIZABLE
            s.launcher.display = pygame.display.set_mode(s.launcher.last_window_size, s.launcher.flags)
            s.launcher.window_data['width'], s.launcher.window_data['height'] = s.launcher.last_window_size

        #SAVING CHANGES
        save_data(s.launcher.window_data, WINDOW_DATA_PATH)

    #METHOD FOR CHANGING FPS
    def update_fps(s, new_fps):
        s.launcher.fps = None if new_fps == 0 else new_fps
        s.launcher.window_data['fps'] = new_fps

        save_data(s.launcher.window_data, WINDOW_DATA_PATH)

    def draw_current_settings(s, window):
        text = f"Resolution: {s.launcher.window_data['width']}x{s.launcher.window_data['height']} | FPS: "
        text += "Uncapped" if s.launcher.window_data['fps'] == 0 else str(s.launcher.window_data['fps'])

        surf = s.font.render(text, True, s.current_theme['colour_2'])
        window.blit(surf, (s.resolution_grid_start_x, WINDOW_HEIGHT - int(WINDOW_HEIGHT * 0.12)))