#IMPORTING LIBRARIES
import pygame

#CLASS FOR INHERITANCE | A BASIC STATE
class BaseState( ):

    def __init__(s, launcher):

        s.launcher = launcher
        s.system = launcher.system

    def handling_events(s):
        '''Player input'''

    def update(s, delta_time):
        '''Updating the current state'''

    def draw(s, window):
        '''Drawing the current states graphics'''