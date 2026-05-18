import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, THEME_LIBRARY


class NavigationTutorial:
    def __init__(self, launcher):
        self.launcher = launcher
        self.theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        
        self.width = int(WINDOW_WIDTH - 300)
        self.height = 750
        
        self.target_x = WINDOW_WIDTH - self.width - 40
        self.target_y = WINDOW_HEIGHT - self.height - 150
        self.x = self.target_x
        self.y = WINDOW_HEIGHT
        self.speed = 800
        self.state = 'entering' if not self.launcher.game_library_data.get('navigation_tutorial_shown', False) else 'hidden'

        self.title_font = pygame.font.SysFont(None, 100, bold=True)
        self.body_font = pygame.font.SysFont(None, 60)
        self.action_font = pygame.font.SysFont(None, 60, bold=True)

        # Map pygame.key.name strings to your exact launcher.button_images keys
        self.asset_mapping = {
            'up': 'up_arrow_button',
            'down': 'down_arrow_button',
            'left': 'left_arrow_button',
            'right': 'right_arrow_button',
            'return': 'enter_button',
            'tab': 'tab_button',
            'action_a': 'r_button',
            'action_b': 'e_button',
        }

    def is_active(self):
        return self.state in ('entering', 'visible')

    def handle_input(self, events):
        if self.state != 'visible':
            return False

        current_key = None
        for event in events:
            if event.type == pygame.KEYDOWN:
                current_key = event.key
                break 

        if current_key is None:
            return False

        controls = self.launcher.controlls_data['keyboard']
        
        if current_key == pygame.K_RETURN or current_key == controls.get('action_a'):
            self.dismiss()
            return True

        return False

    def dismiss(self):
        if self.state != 'exiting':
            self.state = 'exiting'
            self.launcher.game_library_data['navigation_tutorial_shown'] = True
            self.launcher.save()

    def update(self, delta_time):
        if self.state == 'entering':
            self.y = max(self.target_y, self.y - self.speed * delta_time)
            if self.y <= self.target_y:
                self.y = self.target_y
                self.state = 'visible'
        elif self.state == 'exiting':
            self.y += self.speed * delta_time
            if self.y >= WINDOW_HEIGHT:
                self.y = WINDOW_HEIGHT
                self.state = 'hidden'

    def draw(self, window):
        if self.state == 'hidden':
            return

        theme = THEME_LIBRARY[self.launcher.theme_data['current_theme']]
        x, y = int(self.x), int(self.y)
        w, h = self.width, self.height
        padding = 20

        # 1. Main Window Surface (Opaque Background)
        overlay = pygame.Surface((w, h))
        overlay.fill((18, 20, 32))  
        
        # Inner highlight and thicker border
        pygame.draw.rect(overlay, (theme['colour_1']), overlay.get_rect(), border_radius=20)
        pygame.draw.rect(overlay, pygame.Color(theme['colour_2']), overlay.get_rect(), border_radius=20, width=10)

        # 2. Title & Horizontal Divider
        title = self.title_font.render('Navigation Help', True, pygame.Color(theme['colour_2']))
        title_rect = title.get_rect(center=(overlay.get_width() // 2, padding + title.get_height() // 2+10))
        overlay.blit(title, title_rect)
        
        # Draw a sleek horizontal line under the title
        line_y = title_rect.bottom + 20
        pygame.draw.line(overlay, pygame.Color(theme['colour_2']), (padding * 4, line_y), (w - padding * 4, line_y), width=2)

        # 3. Get control mappings and real-time keyboard state
        controls = self.launcher.controlls_data['keyboard']
        pressed_keys = pygame.key.get_pressed()
        
        def draw_key(key_val, pos_x, pos_y):
            pygame_name = pygame.key.name(key_val).lower()
            base_image_key = self.asset_mapping.get(pygame_name, f"{pygame_name}_button")
            image_key = f"{base_image_key}_pressed" if pressed_keys[key_val] else base_image_key

            btn_img = None
            if image_key in self.launcher.button_images:
                btn_img = self.launcher.button_images[image_key]
            elif base_image_key in self.launcher.button_images:
                btn_img = self.launcher.button_images[base_image_key]

            if btn_img:
                img_rect = btn_img.get_rect(topleft=(pos_x, pos_y))
                overlay.blit(btn_img, img_rect.topleft)
            else:
                fallback_text = self.action_font.render(pygame_name.upper(), True, pygame.Color(theme['colour_3']))
                overlay.blit(fallback_text, (pos_x, pos_y))

        # --- Grid & Layout Variables ---
        start_y = line_y + 60
        col1_x = padding + 200
        col2_x = padding + 900
        
        # --- Solid Vertical Divider between columns ---
        divider_x = (col1_x + col2_x) // 2 + 220
        pygame.draw.line(overlay, (40, 44, 68), (divider_x, start_y), (divider_x, h - padding * 5), width=5)

        # --- COLUMN 1: Movement Keys (Inverted-T layout) ---
        move_label = self.body_font.render("Move:", True, pygame.Color('#D7D7E0'))
        overlay.blit(move_label, (col1_x, start_y))

        grid_step = 150  
        arrows_start_y = start_y + 35
        
        # Top Row (Up)
        draw_key(controls['up'], col1_x + grid_step, arrows_start_y)
        
        # Bottom Row (Left, Down, Right)
        draw_key(controls['left'], col1_x, arrows_start_y + grid_step)
        draw_key(controls['down'], col1_x + grid_step, arrows_start_y + grid_step)
        draw_key(controls['right'], col1_x + (grid_step * 2), arrows_start_y + grid_step)

        # --- COLUMN 2: Action Keys (Vertical layout) ---
        action_layout = [
            ("Sidebar", controls['options']),
            ("Select", controls['action_a']),
            ("Back", controls['action_b'])
        ]

        current_action_y = start_y
        for label_text, key_val in action_layout:
            # Action Text Label
            label_surf = self.body_font.render(f"{label_text}:", True, pygame.Color('#D7D7E0'))
            overlay.blit(label_surf, (col2_x, current_action_y + 40)) 
            
            # Action Button
            draw_key(key_val, col2_x + 250, current_action_y)
            current_action_y += 130

        # 4. Dismiss Hint Button (Bottom Right)
        dismiss_img_key = 'enter_button_pressed' if pressed_keys[pygame.K_RETURN] else 'enter_button'
        
        if dismiss_img_key in self.launcher.button_images:
            dismiss_img = self.launcher.button_images[dismiss_img_key]
            d_rect = dismiss_img.get_rect(bottomright=(w - padding - 10, h - padding - 10))
            overlay.blit(dismiss_img, d_rect.topleft)
        else:
            # Scaled up fallback button to match the 60px font sizes
            button_w, button_h = 160, 60 
            button_rect = pygame.Rect(w - padding - button_w, h - padding - button_h, button_w, button_h)
            pygame.draw.rect(overlay, pygame.Color(theme['colour_3']), button_rect, border_radius=8)
            r_text = self.action_font.render('ENTER', True, pygame.Color(theme['colour_1']))
            r_rect = r_text.get_rect(center=button_rect.center)
            overlay.blit(r_text, r_rect)

        # Final Blit onto Main Window
        window.blit(overlay, (x, y))