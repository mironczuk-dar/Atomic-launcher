#IMPORTING LIBRARIES
import pygame


#UNIVERSAL KEYBOARD CLASS FOR INPUTTING TEXT (LIKE NAME SELECTION)
class Keyboard:
    def __init__(s, game, pos, size = (400, 300), max_length=12):

        #PASSING IN GAME AS AN ATTRIBUTE
        s.game = game

        #KEYBOARD ATTRIBUTES
        s.max_length = max_length
        s.text = ""
        s.caps = False
        s.shift = False
        s.finished = False

        #KEYBOARD POSITION AND SIZE
        s.pos = pos
        s.size = size
        
        #DEFINING THE LAYOUT OF THE KEYBOARD
        s.layout = [
            ['1','2','3','4','5','6','7','8','9','0'],
            ['Q','W','E','R','T','Y','U','I','O','P'],
            ['CAPS','A','S','D','F','G','H','J','K','L'],
            ['Shift','Z','X','C','V','B','N','M'],
            ['<-','SPACE','DONE']
        ]
        
        #CURRENT POSITION IN THE KEYBOARD GRID
        s.grid_pos = [0, 0]
        s.font = pygame.font.SysFont("Arial", 28)

    #METHOD FOR HANDLING KEYBOARD INPUT
    def handling_events(s, events):
        ctrl = s.game.controlls_data['keyboard']
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                
                #NAVIGATING THE KEYBOARD GRID
                if event.key == ctrl['up']:
                    s.grid_pos[0] = (s.grid_pos[0] - 1) % len(s.layout)
                elif event.key == ctrl['down']:
                    s.grid_pos[0] = (s.grid_pos[0] + 1) % len(s.layout)
                elif event.key == ctrl['left']:
                    s.grid_pos[1] = (s.grid_pos[1] - 1) % len(s.layout[s.grid_pos[0]])
                elif event.key == ctrl['right']:
                    s.grid_pos[1] = (s.grid_pos[1] + 1) % len(s.layout[s.grid_pos[0]])
                
                if s.grid_pos[1] >= len(s.layout[s.grid_pos[0]]):
                    s.grid_pos[1] = len(s.layout[s.grid_pos[0]]) - 1

                if event.key == ctrl['action_a']:
                    char = s.layout[s.grid_pos[0]][s.grid_pos[1]]
                    s.select_char(char)

                if event.key == ctrl['action_b']:
                    s.text = s.text[:-1]

    #METHOD FOR SELECTING A CHARACTER BASED ON THE CURRENT GRID POSITION
    def select_char(s, char):
        if char == '<-':
            s.text = s.text[:-1]

        elif char == 'DONE':
            s.finished = True

        elif char == 'CAPS':
            s.caps = not s.caps

        elif char == 'Shift':
            s.shift = not s.shift

        elif char == 'SPACE':
            if len(s.text) < s.max_length:
                s.text += " "
            s.shift = False

        else:
            if len(s.text) < s.max_length:

                upper = s.caps ^ s.shift

                if upper:
                    s.text += char.upper()
                else:
                    s.text += char.lower()

                s.shift = False

    #METHOD FOR DRAWING THE KEYBOARD
    def draw(s, window):
        x, y = s.pos
        width, height = s.size

        padding = 8
        rows = len(s.layout)
        cell_h = height // rows

        for row_idx, row in enumerate(s.layout):

            #DYNAMICALLY CALCULATING KEY WIDTHS BASED ON THE TYPE OF KEY (SPACE, SHIFT, NORMAL) AND CENTERING THE ROW
            key_widths = []
            total_units = 0

            for key in row:
                if key == "SPACE":
                    units = 4
                elif key in ["DONE"]:
                    units = 2
                elif key in ["<-", "CAPS", "Shift"]:
                    units = 2
                else:
                    units = 1

                key_widths.append(units)
                total_units += units

            unit_w = (width - padding * (len(row) + 1)) / total_units

            #SETTING THE POSITION TO START DRAWING THE ROW SO THAT IT'S CENTERED
            row_pixel_width = sum(unit_w * u for u in key_widths) + padding * (len(row) + 1)
            start_x = x + (width - row_pixel_width) / 2

            current_x = start_x

            for col_idx, key in enumerate(row):

                key_w = unit_w * key_widths[col_idx]
                rect = pygame.Rect(
                    current_x + padding,
                    y + row_idx * cell_h + padding,
                    key_w,
                    cell_h - padding * 2
                )

                is_selected = (s.grid_pos == [row_idx, col_idx])

                #COLOURS FOR DIFFERENT KEY STATES
                if key == "CAPS" and s.caps:
                    bg_color = (0, 120, 255)
                    text_color = (255, 255, 255)

                elif key == "Shift" and s.shift:
                    bg_color = (0, 180, 120)
                    text_color = (255, 255, 255)

                elif is_selected:
                    bg_color = (255, 200, 0)
                    text_color = (0, 0, 0)

                else:
                    bg_color = (40, 40, 40)
                    text_color = (220, 220, 220)

                #DRAWING THE KEY
                pygame.draw.rect(window, bg_color, rect, border_radius=8)
                pygame.draw.rect(window, (120, 120, 120), rect, 2, border_radius=8)

                display_key = key

                if len(key) == 1 and key.isalpha():
                    upper = s.caps ^ s.shift
                    display_key = key.upper() if upper else key.lower()

                txt_surf = s.font.render(display_key, True, text_color)
                txt_rect = txt_surf.get_rect(center=rect.center)
                window.blit(txt_surf, txt_rect)

                current_x += key_w + padding