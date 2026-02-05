#IMPORTING LIBRARIES
import pygame

#IMPORTING FILES
from UI.options_ui.FPS_preview_ball import Ball
from Tools.data_loading_tools import save_data
from settings import CONTROLLS_DATA_PATH
from settings import THEME_LIBRARY, THEMES_DATA_PATH
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
        
        s.current_theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        s.initial_pos = (WINDOW_WIDTH * 0.18, 600)
        s.button_size = (280, 80)
        
        s.font = pygame.font.SysFont(None, 60, False)
        s.value_font = pygame.font.SysFont(None, 45, False)

        # Definiujemy grupy klawiszy dla kolumn
        s.columns = {
            'movement': ['up', 'down', 'left', 'right'],
            'system': ['options'],
            'actions': ['action_a', 'action_b', 'action_x', 'action_y']
        }
        s.column_names = ['movement', 'system', 'actions']
        
        s.active_col_idx = 0  # 0: lewa, 1: środek, 2: prawa
        s.selected_index = 0  # Indeks wewnątrz danej kolumny
        
        s.waiting_for_key = False

    def handling_events(s, events, ctrl):
        if s.launcher.state_manager.ui_focus != 'content':
            return

        if s.waiting_for_key:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key != pygame.K_ESCAPE:
                        col_key = s.column_names[s.active_col_idx]
                        action_name = s.columns[col_key][s.selected_index]
                        s.update_control(action_name, event.key)
                    s.waiting_for_key = False
            return

        keys = pygame.key.get_just_pressed()
        current_col_key = s.column_names[s.active_col_idx]
        num_items = len(s.columns[current_col_key])

        # Nawigacja POZIOMA (między kolumnami)
        if keys[ctrl['left']]:
            s.active_col_idx = max(0, s.active_col_idx - 1)
            s.selected_index = min(s.selected_index, len(s.columns[s.column_names[s.active_col_idx]]) - 1)
        elif keys[ctrl['right']]:
            s.active_col_idx = min(len(s.column_names) - 1, s.active_col_idx + 1)
            s.selected_index = min(s.selected_index, len(s.columns[s.column_names[s.active_col_idx]]) - 1)

        # Nawigacja PIONOWA
        if keys[ctrl['up']]:
            s.selected_index = max(0, s.selected_index - 1)
        elif keys[ctrl['down']]:
            s.selected_index = min(num_items - 1, s.selected_index + 1)

        # Aktywacja zmiany
        if keys[ctrl['action_a']] or keys[pygame.K_RETURN]:
            s.waiting_for_key = True

    def draw(s, window):
        has_focus = (s.launcher.state_manager.ui_focus == 'content')
        
        # Rysowanie każdej kolumny
        for col_idx, col_name in enumerate(s.column_names):
            actions = s.columns[col_name]
            
            for row_idx, action_name in enumerate(actions):
                is_selected = (col_idx == s.active_col_idx and row_idx == s.selected_index)
                is_waiting = (is_selected and s.waiting_for_key)
                
                # Kolory
                if is_waiting:
                    bg_colour = (200, 50, 50)
                    text_colour = s.current_theme['colour_3']
                elif is_selected and has_focus:
                    bg_colour = s.current_theme['colour_2']
                    text_colour = s.current_theme['colour_3']
                else:
                    bg_colour = s.current_theme['colour_4']
                    text_colour = s.current_theme['colour_2']

                # Pozycjonowanie (3 kolumny)
                x = s.initial_pos[0] + col_idx * (s.button_size[0] + 300)
                y = s.initial_pos[1] + row_idx * (s.button_size[1] + 15)

                # Przycisk
                rect = pygame.Rect(x, y, s.button_size[0], s.button_size[1])
                pygame.draw.rect(window, bg_colour, rect)
                
                # Tekst: Akcja i Klawisz
                key_code = s.launcher.controlls_data[action_name]
                key_name = pygame.key.name(key_code).upper()
                
                label = action_name.replace('_', ' ').title()
                display_text = f"{label}: {key_name}" if not is_waiting else "PRESS..."
                
                text_surf = s.value_font.render(display_text, True, text_colour)
                text_rect = text_surf.get_rect(center=rect.center)
                window.blit(text_surf, text_rect)

    def update_control(s, action_name, new_key):
        s.launcher.controlls_data[action_name] = new_key
        save_data(s.launcher.controlls_data, CONTROLLS_DATA_PATH)

class PerformanceOptionsTab(GenericOptionsTab):

    def __init__(s, launcher):
        super().__init__(launcher)

class ThemesOptionsTab(GenericOptionsTab):

    def __init__(s, launcher):
        super().__init__(launcher)
        
        # UI Layout
        s.initial_pos = (WINDOW_WIDTH * 0.2, 250)
        s.button_size = (500, 100)
        s.spacing = 20
        
        s.font = pygame.font.SysFont(None, 70, False)
        
        # Logic
        s.theme_names = list(THEME_LIBRARY.keys())
        s.selected_index = 0
        
        # Sync index with current theme
        current = s.launcher.theme_data['current_theme']
        if current in s.theme_names:
            s.selected_index = s.theme_names.index(current)

    def handling_events(s, events, ctrl):
        if s.launcher.state_manager.ui_focus != 'content':
            return

        keys = pygame.key.get_just_pressed()

        if keys[ctrl['up']]:
            s.selected_index = (s.selected_index - 1) % len(s.theme_names)
        elif keys[ctrl['down']]:
            s.selected_index = (s.selected_index + 1) % len(s.theme_names)

        # Zmiana motywu
        if keys[ctrl['action_a']] or keys[pygame.K_RETURN]:
            new_theme = s.theme_names[s.selected_index]
            s.apply_theme(new_theme)

    def apply_theme(s, theme_name):
        s.launcher.theme_data['current_theme'] = theme_name
        save_data(s.launcher.theme_data, THEMES_DATA_PATH)
        
        # WYWOŁANIE REODŚWIEŻENIA:
        # Zakładając, że s.launcher.state_manager.current_state to instancja Options
        current_state = s.launcher.state_manager.active_state
        if hasattr(current_state, 'refresh_tabs'):
            current_state.refresh_tabs()

    def draw(s, window):
        has_focus = (s.launcher.state_manager.ui_focus == 'content')
        
        # We fetch the theme dynamically so the preview updates immediately 
        # if the user changes it
        current_visuals = THEME_LIBRARY[s.launcher.theme_data['current_theme']]

        for i, name in enumerate(s.theme_names):
            is_hovered = (i == s.selected_index and has_focus)
            is_active = (name == s.launcher.theme_data['current_theme'])
            
            # Button Colors
            bg_col = current_visuals['colour_2'] if is_hovered else current_visuals['colour_4']
            text_col = current_visuals['colour_3'] if is_hovered else current_visuals['colour_2']
            
            x = s.initial_pos[0]
            y = s.initial_pos[1] + i * (s.button_size[1] + s.spacing)
            
            rect = pygame.Rect(x, y, s.button_size[0], s.button_size[1])
            
            # Draw Button
            pygame.draw.rect(window, bg_col, rect, border_radius=10)
            
            # Active indicator (Border)
            if is_active:
                pygame.draw.rect(window, (255, 255, 255), rect, 4, border_radius=10)

            # Theme Name
            text_surf = s.font.render(name, True, text_col)
            text_rect = text_surf.get_rect(center=rect.center)
            window.blit(text_surf, text_rect)
            
            # Small Color Preview Swatches
            s.draw_color_previews(window, name, x + s.button_size[0] + 20, y)

    def draw_color_previews(s, window, theme_name, x, y):
        colors = THEME_LIBRARY[theme_name]
        swatch_size = 80
        for j, col_key in enumerate(['colour_1', 'colour_2', 'colour_3', 'colour_4']):
            swatch_rect = pygame.Rect(x + (j * (swatch_size + 5)), y + 15, swatch_size, swatch_size)
            pygame.draw.rect(window, colors[col_key], swatch_rect)
            pygame.draw.rect(window, (200, 200, 200), swatch_rect, 2) # Outline