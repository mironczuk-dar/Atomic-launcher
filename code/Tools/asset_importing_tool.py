#IMPORTING LIBRARIES
import pygame
from os import walk
from os.path import join

#FUNCTION FOR IMPORTING AN IMAGE
def import_image(*path, alpha = True, format = '.png'):
    full_path = join(*path) + f'{format}'
    return pygame.image.load(full_path).convert_alpha() if alpha else pygame.image.load(full_path).convert()