#IMPORTING LIBRARIES
import pygame

#IMPORTING FILES
from settings import BASE_DIR, get_contrast_text_color
from UI.options_ui.FPS_preview_ball import Ball
from Tools.data_loading_tools import save_data
from Tools.asset_importing_tool import import_image
from settings import CONTROLLS_DATA_PATH
from settings import THEME_LIBRARY, THEMES_DATA_PATH
from settings import WINDOW_HEIGHT, WINDOW_WIDTH, WINDOW_DATA_PATH
from settings import PERFORMANCE_SETTINGS_DATA_PATH, THEME_LIBRARY, WINDOW_WIDTH

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
        
        # Responsive layout based on aspect ratio
        s.aspect_ratio = WINDOW_WIDTH / WINDOW_HEIGHT
        
        # Resolution options as ordered list for grid layout
        # Optimized for Raspberry Pi and various displays
        s.resolution_list = [
            ('Fullscreen', None),
            ('1280x720 (16:9)', [1280, 720]),
            ('1024x768 (4:3)', [1024, 768]),
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
        keys = pygame.key.get_just_pressed()

        if s.launcher.state_manager.ui_focus != 'content':
            return

        # --- MOVE UP / DOWN / LEFT / RIGHT ---
        if s.active_column == 'resolution':
            col = s.resolution_index % s.resolution_cols
            row = s.resolution_index // s.resolution_cols
            
            if keys[ctrl['up']]:
                if row > 0:
                    s.resolution_index -= s.resolution_cols
            elif keys[ctrl['down']]:
                if (row + 1) * s.resolution_cols + col < len(s.resolution_list):
                    s.resolution_index += s.resolution_cols
            
            if keys[ctrl['left']]:
                if col > 0:
                    # Move to left column in same row
                    s.resolution_index -= 1
                # If at col 0, stay there (can't go further left)
            elif keys[ctrl['right']]:
                if col < s.resolution_cols - 1:
                    # Move to right column in same row
                    s.resolution_index += 1
                else:
                    # At rightmost column, switch to FPS column
                    s.active_column = 'fps'
        
        else:  # fps column
            if keys[ctrl['up']]:
                if s.fps_index > 0:
                    s.fps_index -= 1
            elif keys[ctrl['down']]:
                if s.fps_index < len(s.FPS_options) - 1:
                    s.fps_index += 1
            
            if keys[ctrl['left']]:
                # Switch back to resolution at rightmost column
                s.active_column = 'resolution'
                # Position at rightmost column, aligned with FPS row
                row = min(s.fps_index, (len(s.resolution_list) - 1) // s.resolution_cols)
                s.resolution_index = row * s.resolution_cols + (s.resolution_cols - 1)
            elif keys[ctrl['right']]:
                # Can't go further right from FPS
                pass

        # --- CONFIRM ---
        if keys[ctrl['action_a']] or keys[pygame.K_RETURN]:
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

class ControlsOptionsTab(GenericOptionsTab):
    def __init__(s, launcher):
        super().__init__(launcher)
        
        s.current_theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        s.initial_pos = (WINDOW_WIDTH * 0.30, 400)
        s.button_size = (280, 80)
        s.spacing = 15
        s.column_spacing = 600
        
        s.font = pygame.font.SysFont(None, 60, False)
        s.title_font = pygame.font.SysFont(None, 50, True)
        s.value_font = pygame.font.SysFont(None, 45, False)

        # Definiujemy grupy klawiszy dla dwóch kolumn
        s.columns = {
            'left': ['up', 'down', 'left', 'right'],
            'right': ['options', 'action_a', 'action_b']
        }
        s.column_names = ['left', 'right']
        s.column_titles = ['Movement Buttons', 'Action Buttons']
        
        s.active_col_idx = 0  # 0: lewa, 1: prawa
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
        
        # Draw column titles
        for col_idx, col_name in enumerate(s.column_names):
            title = s.column_titles[col_idx]
            x = s.initial_pos[0] + col_idx * s.column_spacing + s.button_size[0] // 2
            y = s.initial_pos[1] - 60
            
            title_surf = s.title_font.render(title, True, s.current_theme['colour_2'])
            title_rect = title_surf.get_rect(center=(x, y))
            window.blit(title_surf, title_rect)
        
        # Rysowanie każdej kolumny
        for col_idx, col_name in enumerate(s.column_names):
            actions = s.columns[col_name]
            
            for row_idx, action_name in enumerate(actions):
                is_selected = (col_idx == s.active_col_idx and row_idx == s.selected_index)
                is_waiting = (is_selected and s.waiting_for_key)
                
                # Kolory
                if is_waiting:
                    bg_colour = (200, 50, 50)
                elif is_selected and has_focus:
                    bg_colour = s.current_theme['colour_2']
                else:
                    bg_colour = s.current_theme['colour_4']

                text_colour = get_contrast_text_color(bg_colour)

                # Pozycjonowanie (2 kolumny)
                x = s.initial_pos[0] + col_idx * s.column_spacing
                y = s.initial_pos[1] + row_idx * (s.button_size[1] + s.spacing)

                # Przycisk
                rect = pygame.Rect(x, y, s.button_size[0], s.button_size[1])
                pygame.draw.rect(window, bg_colour, rect)
                
                # 🔹 FOCUS INDICATOR = AKTUALNIE ZAZNACZONY ELEMENT
                if is_selected and has_focus:
                    pygame.draw.rect(window, (255, 200, 0), rect, 4)
                
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
        s.update_visuals()
        
        s.initial_pos = (WINDOW_WIDTH * 0.15, 250)
        s.col_width = 350
        s.fps_button_height = 80
        s.shutdown_button_size = (400, 200)
        s.spacing = 15
        
        s.font = pygame.font.SysFont(None, 45, False)
        s.header_font = pygame.font.SysFont(None, 55, True)

        # Opcje FPS do wyboru
        s.fps_levels = [60, 40, 30, 20, 15, 10, 5]
        
        # Nawigacja
        s.active_col = 'fps'  # 'fps' lub 'shutdown'
        s.fps_index = 0

    def update_visuals(s):
        s.current_theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]

    def handling_events(s, events, ctrl):
        if s.launcher.state_manager.ui_focus != 'content':
            return

        keys = pygame.key.get_just_pressed()

        # Zmiana kolumny
        if keys[ctrl['left']] or keys[ctrl['right']]:
            s.active_col = 'shutdown' if s.active_col == 'fps' else 'fps'

        # Nawigacja pionowa (tylko dla kolumny FPS)
        if s.active_col == 'fps':
            if keys[ctrl['up']]:
                s.fps_index = (s.fps_index - 1) % len(s.fps_levels)
            elif keys[ctrl['down']]:
                s.fps_index = (s.fps_index + 1) % len(s.fps_levels)

        # Akcja / Potwierdzenie
        if keys[ctrl['action_a']] or keys[pygame.K_RETURN]:
            if s.active_col == 'fps':
                s.launcher.performance_settings_data['decrease_launcher_fps_when_game_active'] = s.fps_levels[s.fps_index]
            else:
                current_val = s.launcher.performance_settings_data['turn_off_launcher_when_game_active']
                s.launcher.performance_settings_data['turn_off_launcher_when_game_active'] = not current_val
            
            save_data(s.launcher.performance_settings_data, PERFORMANCE_SETTINGS_DATA_PATH)

    def draw(s, window):
        has_focus = (s.launcher.state_manager.ui_focus == 'content')
        
        s.draw_fps_column(window, has_focus)
        s.draw_shutdown_column(window, has_focus)

    def draw_fps_column(s, window, has_focus):
        # Nagłówek
        header = s.header_font.render("Background FPS", True, s.current_theme['colour_2'])
        window.blit(header, (s.initial_pos[0], s.initial_pos[1] - 60))

        current_saved_fps = s.launcher.performance_settings_data['decrease_launcher_fps_when_game_active']

        for i, fps in enumerate(s.fps_levels):
            is_selected = (s.active_col == 'fps' and i == s.fps_index and has_focus)
            is_active = (fps == current_saved_fps)

            bg_col = s.current_theme['colour_2'] if is_selected else s.current_theme['colour_4']
            text_col = get_contrast_text_color(bg_col)

            rect = pygame.Rect(
                s.initial_pos[0], 
                s.initial_pos[1] + i * (s.fps_button_height + s.spacing),
                s.col_width, 
                s.fps_button_height
            )

            pygame.draw.rect(window, bg_col, rect, border_radius=5)
            
            # Ramka dla aktualnie wybranej wartości w danych
            if is_active:
                pygame.draw.rect(window, (0, 255, 0), rect, 3, border_radius=5)

            # 🔹 FOCUS INDICATOR = AKTUALNIE ZAZNACZONY ELEMENT
            if is_selected:
                pygame.draw.rect(window, (255, 200, 0), rect, 4, border_radius=5)

            text_surf = s.font.render(f"{fps} FPS", True, text_col)
            text_rect = text_surf.get_rect(center=rect.center)
            window.blit(text_surf, text_rect)

    def draw_shutdown_column(s, window, has_focus):
        # Pozycja prawej kolumny
        x_pos = s.initial_pos[0] + s.col_width + 100
        
        # Nagłówek
        header = s.header_font.render("Launcher Behavior", True, s.current_theme['colour_2'])
        window.blit(header, (x_pos, s.initial_pos[1] - 60))

        is_selected = (s.active_col == 'shutdown' and has_focus)
        is_on = s.launcher.performance_settings_data['turn_off_launcher_when_game_active']

        bg_col = s.current_theme['colour_2'] if is_selected else s.current_theme['colour_4']
        text_col = get_contrast_text_color(bg_col)

        rect = pygame.Rect(x_pos, s.initial_pos[1], s.shutdown_button_size[0], s.shutdown_button_size[1])
        pygame.draw.rect(window, bg_col, rect, border_radius=10)

        # 🔹 FOCUS INDICATOR = AKTUALNIE ZAZNACZONY ELEMENT
        if is_selected:
            pygame.draw.rect(window, (255, 200, 0), rect, 4, border_radius=10)

        # Tekst przycisku
        main_text = "Shutdown Launcher"
        status_text = "STATUS: ON" if is_on else "STATUS: OFF"
        status_col = (100, 255, 100) if is_on else (255, 100, 100)

        t1 = s.font.render(main_text, True, text_col)
        t2 = s.font.render(status_text, True, status_col if not is_selected else text_col)

        window.blit(t1, (rect.centerx - t1.get_width()//2, rect.y + 40))
        window.blit(t2, (rect.centerx - t2.get_width()//2, rect.y + 110))

        # Podpowiedź na dole
        desc = "Close app when game starts"
        desc_surf = s.font.render(desc, True, s.current_theme['colour_4'])
        window.blit(desc_surf, (x_pos, rect.bottom + 20))

class ThemesOptionsTab(GenericOptionsTab):

    def __init__(s, launcher):
        super().__init__(launcher)
        
        # UI Layout
        s.initial_pos = (WINDOW_WIDTH * 0.3, 175)
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
            text_col = get_contrast_text_color(bg_col)
            
            x = s.initial_pos[0]
            y = s.initial_pos[1] + i * (s.button_size[1] + s.spacing)
            
            rect = pygame.Rect(x, y, s.button_size[0], s.button_size[1])
            
            # Draw Button
            pygame.draw.rect(window, bg_col, rect, border_radius=10)
            
            # Active indicator (Border)
            if is_active:
                pygame.draw.rect(window, (255, 255, 255), rect, 4, border_radius=10)

            # 🔹 FOCUS INDICATOR = AKTUALNIE ZAZNACZONY ELEMENT
            if is_hovered:
                pygame.draw.rect(window, (255, 200, 0), rect, 4, border_radius=10)

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