"""Control remapping tab.

This tab allows the user to choose between preset control layouts, or
manually rebind individual keyboard buttons. It persists the chosen
bindings to the controls data file.
"""

import pygame

from settings import get_contrast_text_color
from Tools.data_loading_tools import save_data
from settings import CONTROLS_DATA_PATH, THEME_LIBRARY, WINDOW_WIDTH
from UI.options_ui.generic_options_tab import GenericOptionsTab


class ControlsOptionsTab(GenericOptionsTab):
    """Options tab for control presets and key rebinding."""
    def __init__(s, launcher):
        super().__init__(launcher)
        
        s.current_theme = THEME_LIBRARY[s.launcher.theme_data['current_theme']]
        
        # --- Layout for the preset selector and rebinding panels ---
        s.initial_pos = (WINDOW_WIDTH * 0.25, 430) 
        s.button_size = (460, 130)  # Expanded size to gracefully house both text and images
        s.spacing = 15
        s.column_spacing = 700
        
        s.font = pygame.font.SysFont(None, 60, False)
        s.preset_font = pygame.font.SysFont(None, 40, True)
        s.title_font = pygame.font.SysFont(None, 70, False)
        s.value_font = pygame.font.SysFont(None, 45, False)

        # Map pygame.key.name strings to your exact launcher.button_images keys
        s.asset_mapping = {
            'up': 'up_arrow_button',
            'down': 'down_arrow_button',
            'left': 'left_arrow_button',
            'right': 'right_arrow_button',
            'return': 'enter_button',
            'tab': 'tab_button',
            'action_a': 'r_button',
            'action_b': 'e_button',
        }

        # --- PRESET CONFIGURATION ---
        s.preset_names = ['Arrows', 'WASD', 'Custom']
        s.presets = {
            'Arrows': {
                'up': pygame.K_UP, 'down': pygame.K_DOWN, 
                'left': pygame.K_LEFT, 'right': pygame.K_RIGHT,
                'action_a': pygame.K_r, 'action_b': pygame.K_e
            },
            'WASD': {
                'up': pygame.K_w, 'down': pygame.K_s, 
                'left': pygame.K_a, 'right': pygame.K_d,
                'action_a': pygame.K_p, 'action_b': pygame.K_o
            }
        }
        
        s.focus_area = 'preset'  # Starts on 'preset', can switch to 'bindings'
        s.preset_idx = 2         # The currently active preset (Defaults to Custom)
        s.preset_focus_idx = 2   # Which preset button the cursor is hovering over
        
        # Check current keys on boot
        s.evaluate_current_preset()

        # Group components back into clearly labeled rows across two columns
        s.columns = {
            'left': ['up', 'down', 'left', 'right'],
            'right': ['options', 'action_a', 'action_b']
        }
        s.column_names = ['left', 'right']
        s.column_titles = ['Movement Buttons', 'Action Buttons']
        
        s.active_col_idx = 0  # 0: left, 1: right
        s.selected_index = 0  # Row index within the current column
        
        s.waiting_for_key = False

    def evaluate_current_preset(s):
        """Detect whether the current bindings match a known preset."""
        ctrl = s.launcher.controlls_data['keyboard']
        s.preset_idx = 2  # Default to Custom
        for idx, name in enumerate(['Arrows', 'WASD']):
            preset = s.presets[name]
            if all(ctrl.get(k) == preset[k] for k in preset):
                s.preset_idx = idx
                break
        
        s.preset_focus_idx = s.preset_idx

    def apply_preset(s):
        """Apply the selected control preset and persist it to disk."""
        preset_name = s.preset_names[s.preset_idx]
        if preset_name == 'Custom':
            return
        
        preset_data = s.presets[preset_name]
        for key, val in preset_data.items():
            s.launcher.controlls_data['keyboard'][key] = val
            
        save_data(s.launcher.controlls_data, CONTROLS_DATA_PATH)

    def handling_events(s, events, ctrl):
        if s.launcher.state_manager.ui_focus != 'content':
            return

        input_manager = getattr(s.launcher, 'input_manager', None)

        for event in events:
            if event.type == pygame.KEYDOWN and s.waiting_for_key:
                current_key = event.key
                if current_key != pygame.K_ESCAPE:
                    col_key = s.column_names[s.active_col_idx]
                    action_name = s.columns[col_key][s.selected_index]
                    s.update_control(action_name, current_key)
                    s.preset_idx = 2
                    s.preset_focus_idx = 2
                s.waiting_for_key = False
                return

        if s.waiting_for_key:
            return

        if input_manager is None:
            return

        if input_manager.just_pressed('up'):
            if s.focus_area == 'preset':
                if s.preset_focus_idx > 0:
                    s.preset_focus_idx -= 1
            else:
                if s.selected_index == 0:
                    s.focus_area = 'preset'
                    s.preset_focus_idx = s.preset_idx
                else:
                    s.selected_index -= 1
        elif input_manager.just_pressed('down'):
            if s.focus_area == 'preset':
                s.focus_area = 'bindings'
            else:
                current_col_key = s.column_names[s.active_col_idx]
                num_items = len(s.columns[current_col_key])
                s.selected_index = min(num_items - 1, s.selected_index + 1)
        elif input_manager.just_pressed('left'):
            if s.focus_area == 'preset':
                s.preset_focus_idx = max(0, s.preset_focus_idx - 1)
            else:
                s.active_col_idx = max(0, s.active_col_idx - 1)
                s.selected_index = min(s.selected_index, len(s.columns[s.column_names[s.active_col_idx]]) - 1)
        elif input_manager.just_pressed('right'):
            if s.focus_area == 'preset':
                s.preset_focus_idx = min(len(s.preset_names) - 1, s.preset_focus_idx + 1)
            else:
                s.active_col_idx = min(len(s.column_names) - 1, s.active_col_idx + 1)
                s.selected_index = min(s.selected_index, len(s.columns[s.column_names[s.active_col_idx]]) - 1)
        elif input_manager.just_pressed('action_a'):
            if s.focus_area == 'preset':
                s.preset_idx = s.preset_focus_idx
                s.apply_preset()
            else:
                s.waiting_for_key = True

    def draw(s, window):
        has_focus = (s.launcher.state_manager.ui_focus == 'content')
        pressed_keys = pygame.key.get_pressed()
        
        # ---------------------------------------------------------
        # 1. DRAW PRESET SELECTOR
        # ---------------------------------------------------------
        preset_y = s.initial_pos[1] - 230
        p_btn_w, p_btn_h, p_spacing = 200, 60, 30
        total_preset_width = (p_btn_w * 3) + (p_spacing * 2)
        start_x = (WINDOW_WIDTH - total_preset_width) // 2 + 100

        p_title_surf = s.value_font.render("Control Scheme", True, s.current_theme['colour_2'])
        window.blit(p_title_surf, p_title_surf.get_rect(midbottom=(WINDOW_WIDTH // 2 +100, preset_y - 20)))

        for i, preset_name in enumerate(s.preset_names):
            x = start_x + i * (p_btn_w + p_spacing)
            rect = pygame.Rect(x, preset_y, p_btn_w, p_btn_h)
            
            is_active = (i == s.preset_idx)
            is_focused = (i == s.preset_focus_idx and s.focus_area == 'preset' and has_focus)

            bg_colour = s.current_theme['colour_2'] if is_active else s.current_theme['colour_4']
            text_colour = get_contrast_text_color(bg_colour)

            pygame.draw.rect(window, bg_colour, rect, border_radius=12)
            if is_focused:
                pygame.draw.rect(window, (255, 200, 0), rect, 4, border_radius=15)

            text_surf = s.preset_font.render(preset_name, True, text_colour)
            window.blit(text_surf, text_surf.get_rect(center=rect.center))

        # ---------------------------------------------------------
        # 2. DRAW TWO-COLUMN BINDINGS BOXES
        # ---------------------------------------------------------
        for col_idx, col_name in enumerate(s.column_names):
            title = s.column_titles[col_idx]
            x = s.initial_pos[0] + col_idx * s.column_spacing + s.button_size[0] // 2
            y = s.initial_pos[1] - 40
            
            title_surf = s.title_font.render(title, True, s.current_theme['colour_2'])
            window.blit(title_surf, title_surf.get_rect(center=(x, y)))
        
        for col_idx, col_name in enumerate(s.column_names):
            actions = s.columns[col_name]
            
            for row_idx, action_name in enumerate(actions):
                is_selected = (col_idx == s.active_col_idx and row_idx == s.selected_index and s.focus_area == 'bindings')
                is_waiting = (is_selected and s.waiting_for_key)
                
                if is_waiting:
                    bg_colour = (200, 50, 50)
                elif is_selected and has_focus:
                    bg_colour = s.current_theme['colour_2']
                else:
                    bg_colour = s.current_theme['colour_4']

                text_colour = get_contrast_text_color(bg_colour)

                x = s.initial_pos[0] + col_idx * s.column_spacing
                y = s.initial_pos[1] + row_idx * (s.button_size[1] + s.spacing)

                rect = pygame.Rect(x, y, s.button_size[0], s.button_size[1])
                pygame.draw.rect(window, bg_colour, rect, border_radius=12)
                
                # Draw yellow border indicator to clearly show where user is browsing
                if is_selected and has_focus:
                    pygame.draw.rect(window, (255, 200, 0), rect, 4, border_radius=15)

                if is_waiting:
                    prompt_surf = s.value_font.render("PRESS...", True, text_colour)
                    window.blit(prompt_surf, prompt_surf.get_rect(center=rect.center))
                else:
                    # A. Render the action label text on the left side of the panel
                    label_txt = action_name.replace('_', ' ').title()
                    label_surf = s.value_font.render(f"{label_txt}:", True, text_colour)
                    window.blit(label_surf, label_surf.get_rect(midleft=(rect.left + 25, rect.centery)))

                    # B. Pull keyboard codes & calculate active pressed statuses
                    key_code = s.launcher.controlls_data['keyboard'][action_name]
                    pygame_name = pygame.key.name(key_code).lower()
                    
                    base_image_key = s.asset_mapping.get(pygame_name, f"{pygame_name}_button")
                    image_key = f"{base_image_key}_pressed" if pressed_keys[key_code] else base_image_key

                    btn_img = None
                    if image_key in s.launcher.button_images:
                        btn_img = s.launcher.button_images[image_key]
                    elif base_image_key in s.launcher.button_images:
                        btn_img = s.launcher.button_images[base_image_key]

                    # C. Draw button graphics on the right side of the box panel
                    if btn_img:
                        img_rect = btn_img.get_rect(midright=(rect.right - 25, rect.centery))
                        window.blit(btn_img, img_rect.topleft)
                    else:
                        # Clean fallback to capital text string strings if images are missing
                        fallback_text = s.value_font.render(pygame_name.upper(), True, text_colour)
                        window.blit(fallback_text, fallback_text.get_rect(midright=(rect.right - 25, rect.centery)))

    def update_control(s, action_name, new_key):
        s.launcher.controlls_data['keyboard'][action_name] = new_key
        save_data(s.launcher.controlls_data, CONTROLS_DATA_PATH)