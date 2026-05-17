#IMPORTING LIBRARIES
import pygame

# IMPORTING FILES
from settings import get_contrast_text_color


#A GENERIC BUTTON CLASS
class GenericButton():
    def __init__(s, game, size, pos, text, text_size = 40, text_colour = (0,0,0), colour = (255, 0, 0), action = None, sound = None):

        s.game = game
        s.action = action
        s.sound = sound

        s.is_selected = False

        s.image = pygame.Surface(size, pygame.SRCALPHA)
        s.image.fill(colour)
        s.base_image = s.image.copy()

        s.rect = s.image.get_rect(center=pos)

        s.font = pygame.font.Font(None, text_size)
        text_surf = s.font.render(text, True, text_colour)

        text_rect = text_surf.get_rect(center=(size[0] // 2, size[1] // 2))
        s.image.blit(text_surf, text_rect)
        s.base_image.blit(text_surf, text_rect)


    # =========================
    # KEYBOARD ACTIVATION
    # =========================
    def activate(s):

        if s.sound:
            s.game.audio_manager.play_sound(s.sound)

        if s.action:
            s.action()


    def update(s, delta_time):
        pass


    def draw(s, window):

        img = s.base_image.copy()

        if s.is_selected:
            pygame.draw.rect(img,(255,230,120),img.get_rect(),4)

        window.blit(img, s.rect)


    def handling_events(s, events):

        mouse_pos = s.game.get_scaled_mouse_pos()
        mouse_press = pygame.mouse.get_just_pressed()[0]

        hovered = s.rect.collidepoint(mouse_pos)

        if hovered:
            s.image.set_alpha(120)
        else:
            s.image.set_alpha(255)

        if hovered and mouse_press:
            s.activate()

#A BUTTON THAT HAS AN IMAGE
class ImageAudioButton(GenericButton):
    def __init__(s, game, pos, image, hover_image, action=None, sound=None,
                 text=None, text_size=40, text_colour=(0, 0, 0), font=None, 
                 wait_for_sound_to_end=False):

        s.game = game
        s.action = action
        s.sound = sound
        s.wait_for_sound_to_end = wait_for_sound_to_end
        s.channel = None
        s.waiting_for_audio = False
        s.is_selected = False

        s.font = pygame.font.Font(font, text_size) if font else pygame.font.Font(None, text_size)

        s.image_normal = image.copy()
        s.image_hover = hover_image.copy()

        if text:
            text_surf = s.font.render(text, True, text_colour)
            text_rect = text_surf.get_rect(center=(s.image_normal.get_width() // 2, s.image_normal.get_height() // 2))
            s.image_normal.blit(text_surf, text_rect)
            s.image_hover.blit(text_surf, text_rect)

        s.image = s.image_normal
        s.rect = s.image.get_rect(center=pos)

    def handling_events(s, events):
        if s.waiting_for_audio: return

        mouse_pos = s.game.get_scaled_mouse_pos()
        
        hovered = s.rect.collidepoint(mouse_pos)

        if hovered or s.is_selected:
            s.image = s.image_hover
        else:
            s.image = s.image_normal

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if s.rect.collidepoint(mouse_pos):
                    s.press()

    def update(s, delta_time):
        if s.waiting_for_audio:
            if s.channel is None or not s.channel.get_busy():
                s.waiting_for_audio = False
                if s.action:
                    s.action()

    def draw(s, window):
        window.blit(s.image, s.rect)

    #METHOD FOR PRESSING BUTTON WITH KEYBOARD CONTROLLS
    def press(s):
        if s.waiting_for_audio:
            return

        if s.sound:
            s.channel = s.game.audio_manager.play_sound(s.sound)

        if s.sound and s.wait_for_sound_to_end:
            s.waiting_for_audio = True
        elif s.action:
            s.action()

#A BUTTON THAT PLAYS A SOUND AND WAITS FOR IT TO FINISH BEFORE EXECUTING THE ACTION
class AudioButton(GenericButton):
    def __init__(s, *args, **kwargs):

        #INITIALIZING THE GENERIC BUTTON
        super().__init__(*args, **kwargs)
        s.channel = None
        s.is_waiting = False

    #METHOD FOR UPDATING THE CLASS
    def update(s, delta_time):
        if s.is_waiting:
            if s.channel is None or not s.channel.get_busy():
                if s.action:
                    s.action()
                s.is_waiting = False
                s.channel = None

    def handling_events(s, events):
        mouse_pos = s.game.get_scaled_mouse_pos()
        mouse_press = pygame.mouse.get_just_pressed()[0]

        if s.rect.collidepoint(mouse_pos):
            s.image.set_alpha(100)
        else:
            s.image.set_alpha(255)

        if s.rect.collidepoint(mouse_pos) and mouse_press:
            if not s.is_waiting:
                if s.sound:
                    s.channel = s.game.audio_manager.play_sound(s.sound)
                    s.is_waiting = True
                else:
                    if s.action: s.action()

#A TOGGLE BUTTON
class GenericToggleButton:
    def __init__(s, game, size, pos, text, text_size=40, active_colour=(0,255,0), inactive_colour=(255,0,0), action=None):

        s.game = game
        s.size = size
        s.pos = pos
        s.text = text
        s.text_size = text_size
        s.action = action

        s.active_colour = active_colour
        s.inactive_colour = inactive_colour
        s.use_theme = False

        s.is_on = False
        s.is_selected = False

        s.font = pygame.font.Font(None, s.text_size)

        s.update_appearance()

    def set_theme_colours(s, use_theme=True):
        """Enable dynamic theme-based colours from launcher theme data."""
        s.use_theme = use_theme

    def get_current_colours(s):
        """Get current colours, either from theme or static values."""
        if s.use_theme and hasattr(s.game, 'theme_data'):
            from settings import THEME_LIBRARY
            theme = THEME_LIBRARY[s.game.theme_data['current_theme']]
            return theme['colour_2'], theme['colour_4']
        return s.active_colour, s.inactive_colour

    def update_appearance(s):

        s.image = pygame.Surface(s.size, pygame.SRCALPHA)

        active_colour, inactive_colour = s.get_current_colours()
        current_colour = active_colour if s.is_on else inactive_colour
        s.image.fill(current_colour)

        s.rect = s.image.get_rect(center=s.pos)

        text_colour = get_contrast_text_color(current_colour)
        text_surf = s.font.render(s.text, True, text_colour)
        text_rect = text_surf.get_rect(center=(s.size[0]//2, s.size[1]//2))

        s.image.blit(text_surf, text_rect)


    def activate(s):
        s.toggle()


    def draw(s, window):

        img = s.image.copy()

        if s.is_selected:
            pygame.draw.rect(img,(255,230,120),img.get_rect(),4)

        window.blit(img, s.rect)


    def update(s, delta_time):
        if s.use_theme:
            s.update_appearance()


    def handling_events(s, events):

        mouse_pos = s.game.get_scaled_mouse_pos()

        hovered = s.rect.collidepoint(mouse_pos)

        if hovered:
            s.image.set_alpha(180)
        else:
            s.image.set_alpha(255)

        for event in events:

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and hovered:
                    s.toggle()


    def toggle(s):

        s.is_on = not s.is_on

        s.update_appearance()

        if s.action:
            s.action()

class ImageToggleButton:
    def __init__(s, game, pos, idle_img, hover_img, active_img, highlight_img=None, text="", font_path=None, text_size=40, action=None):
        s.game = game
        s.pos = pos
        s.action = action
        
        # Przechowywanie obrazków
        s.idle_img = idle_img
        s.hover_img = hover_img
        s.active_img = active_img
        s.highlight_img = highlight_img
        
        s.is_on = False
        s.is_hovered = False
        s.is_selected = False
        
        # Tekst i czcionka
        s.text = text
        # Jeśli nie podasz font_path, użyje domyślnego fontu Pygame
        s.font = pygame.font.Font(font_path, text_size)
        
        # Ustawienie rect na podstawie jednego z obrazków
        s.image = s.idle_img
        s.rect = s.image.get_rect(center=s.pos)
        
        # Przygotowanie powierzchni tekstu (renderujemy raz dla wydajności)
        # Zakładam kolor czarny (0,0,0), możesz go zmienić w parametrach
        s.text_surf = s.font.render(s.text, True, (0, 0, 0))
        s.text_rect = s.text_surf.get_rect(center=(s.rect.width // 2, s.rect.height // 2))

    def handling_events(s, events):
        mouse_pos = s.game.get_scaled_mouse_pos()
        s.is_hovered = s.rect.collidepoint(mouse_pos)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and s.is_hovered:
                    s.toggle()

    def toggle(s):
        s.is_on = not s.is_on
        if s.action:
            s.action()

    def update(s, delta_time):
        if s.is_on:
            s.image = s.active_img
        elif s.is_hovered or s.is_selected:
            s.image = s.hover_img
        else:
            s.image = s.idle_img

    def draw(s, window):
        if s.is_selected and s.highlight_img:
            hi_rect = s.highlight_img.get_rect(center=s.rect.center)
            window.blit(s.highlight_img, hi_rect)

        window.blit(s.image, s.rect)

        # Draw text on top (centered inside the image)
        text_pos = (s.rect.x + s.text_rect.x, s.rect.y + s.text_rect.y)
        window.blit(s.text_surf, text_pos)
