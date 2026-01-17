#IMPORTING LIBRARIES
import pygame

#IMPORTING FILES
from UI.options_ui.FPS_preview_ball import Ball
from Tools.data_loading_tools import save_data
from settings import THEME_LIBRARY
from settings import WINDOW_HEIGHT, WINDOW_WIDTH, WINDOW_DATA_PATH

class GenericOptionsTab:

    def __init__(s, launcher):
        s.launcher = launcher

    def update(s, delta_time):
        pass

    def draw(s, window):
        pass


class VideoOptionsTab(GenericOptionsTab):
    def __init__(s, launcher):
        super().__init__(launcher)

        s.current_theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        s.initial_pos = (WINDOW_WIDTH * 0.15 + 10, 200)
        s.resolution_button_size = (400, 180)
        s.FPS_button_size = (400, 120)

        s.font = pygame.font.SysFont(None, 80, False)
        s.value_font = pygame.font.SysFont(None, 60, False)

        s.resolution_options = {
            'Fullscreen' : None,
            1080 : [1920, 1080],
            720 : [1280, 720],
            360 : [640, 360]
        }
        s.FPS_options = ['Uncapped', 90, 60, 40, 30]

        s.FPS_preview_ball = Ball((WINDOW_WIDTH * 0.8, 50), s.current_theme['colour_2'])

        s.active_column = 'resolution'   # 'resolution' | 'fps'
        s.resolution_index = 0
        s.fps_index = 0

        s.selected_resolution = None
        s.selected_fps = None

    def handling_events(s, events, ctrl):
        keys = pygame.key.get_just_pressed()

        if s.launcher.state_manager.ui_focus != 'content':
            return


        # --- MOVE BETWEEN COLUMNS ---
        if keys[ctrl['left']] or keys[ctrl['right']]:
            s.active_column = 'fps' if s.active_column == 'resolution' else 'resolution'

        # --- MOVE UP / DOWN ---
        if keys[ctrl['up']]:
            if s.active_column == 'resolution':
                s.resolution_index = max(0, s.resolution_index - 1)
            else:
                s.fps_index = max(0, s.fps_index - 1)

        elif keys[ctrl['down']]:
            if s.active_column == 'resolution':
                s.resolution_index = min(
                    len(s.get_resolution_keys()) - 1,
                    s.resolution_index + 1
                )
            else:
                s.fps_index = min(
                    len(s.get_fps_values()) - 1,
                    s.fps_index + 1
                )

        # --- CONFIRM ---
        if s.active_column == 'resolution':
            key = s.get_resolution_keys()[s.resolution_index]

            if keys[ctrl['action_a']] or keys[pygame.K_RETURN]:
                if key == 'Fullscreen':
                    s.go_fullscreen()
                else:
                    width, height = s.resolution_options[key]
                    s.change_resolution(width, height)

        else:
            fps = s.get_fps_values()[s.fps_index]

            if keys[ctrl['action_a']] or keys[pygame.K_RETURN]:
                if fps == 'Uncapped':
                    s.update_fps(0)
                else:
                    s.update_fps(fps)

    def update(s, delta_time):
        s.FPS_preview_ball.update(delta_time)

    def draw(s, window):
        has_focus = (s.launcher.state_manager.ui_focus == 'content')

        s.FPS_preview_ball.draw(window)

        s.draw_resolution_buttons(window, has_focus)
        s.draw_FPS_buttons(window, has_focus)
        s.draw_current_settings(window)

    def draw_resolution_buttons(s, window, has_focus):
        for i, key in enumerate(s.resolution_options.keys()):

            is_selected = (
                s.active_column == 'resolution' and
                i == s.resolution_index
            )

            is_current = s.is_current_resolution(key)

            bg_colour = (
                s.current_theme['colour_2']
                if is_selected and has_focus
                else s.current_theme['colour_4']
            )

            text_colour = (
                s.current_theme['colour_3']
                if is_selected and has_focus
                else s.current_theme['colour_2']
            )

            button_surf = pygame.Surface(s.resolution_button_size)
            button_surf.fill(bg_colour)

            # 🔹 RAMKA = OBECNIE UŻYWANA OPCJA
            if is_current:
                pygame.draw.rect(
                    button_surf,
                    (0, 200, 0),
                    button_surf.get_rect(),
                    6
                )

            x = s.initial_pos[0]
            y = s.initial_pos[1] + i * (s.resolution_button_size[1] + 10)

            text_surface = s.value_font.render(str(key), False, text_colour)
            text_rect = text_surface.get_rect(center=button_surf.get_rect().center)

            button_surf.blit(text_surface, text_rect)
            window.blit(button_surf, (x, y))

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

            text_colour = (
                s.current_theme['colour_3']
                if is_selected and has_focus
                else s.current_theme['colour_2']
            )

            button_surf = pygame.Surface(s.FPS_button_size)
            button_surf.fill(bg_colour)

            # 🔹 RAMKA = AKTUALNY FPS
            if is_current:
                pygame.draw.rect(
                    button_surf,
                    (0, 200, 0),
                    button_surf.get_rect(),
                    6
                )

            x = s.initial_pos[0] + s.FPS_button_size[0] + 50
            y = s.initial_pos[1] + i * (s.FPS_button_size[1] + 10)

            text_surface = s.value_font.render(str(fps), False, text_colour)
            text_rect = text_surface.get_rect(center=button_surf.get_rect().center)

            button_surf.blit(text_surface, text_rect)
            window.blit(button_surf, (x, y))

    def get_resolution_keys(s):
        return list(s.resolution_options.keys())

    def get_fps_values(s):
        return s.FPS_options

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

    def is_current_resolution(s, key):
        if key == 'Fullscreen':
            return s.launcher.window_data['fullscreen']

        width, height = s.resolution_options[key]
        return (
            not s.launcher.window_data['fullscreen'] and
            s.launcher.window_data['width'] == width and
            s.launcher.window_data['height'] == height
        )
    
    def is_current_fps(s, fps):
        if fps == 'Uncapped':
            return s.launcher.window_data['fps'] == 0
        return s.launcher.window_data['fps'] == fps

    def draw_current_settings(s, window):
        text = f"Resolution: {s.launcher.window_data['width']}x{s.launcher.window_data['height']} | FPS: "
        text += "Uncapped" if s.launcher.window_data['fps'] == 0 else str(s.launcher.window_data['fps'])

        surf = s.font.render(text, True, s.current_theme['colour_2'])
        window.blit(surf, (WINDOW_WIDTH * 0.15, WINDOW_HEIGHT - 80))


class ControlsOptionsTab(GenericOptionsTab):

    def __init__(s, launcher):
        super().__init__(launcher)

class PerformanceOptionsTab(GenericOptionsTab):

    def __init__(s, launcher):
        super().__init__(launcher)

class ThemesOptionsTab(GenericOptionsTab):

    def __init__(s, launcher):
        super().__init__(launcher)