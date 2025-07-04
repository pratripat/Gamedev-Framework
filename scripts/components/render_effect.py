import pygame

class RenderEffectComponent:
    def __init__(self):
        self.scale = pygame.Vector2(1, 1) # for squash/stretch
        self.alpha = None                 # for transparency
        self.tint = None                  # for color tint
        self.blink = False                # for flickering
        self.effect_timers = {}           # active timers {'squash': 0}
        self.effect_data = {}             # active data {'squash': {'start_scale': [x, y], 'target_scale': [x2, y2], 'duration': ,return_back: bool}}
        self.disabled = False
    