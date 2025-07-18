import pygame
from dataclasses import dataclass
from typing import Tuple
from ..components.tags import PlayerTagComponent, EnemyTagComponent

class RenderEffectComponent:
    def __init__(self):
        self.scale = pygame.Vector2(1, 1) # for squash/stretch
        self.alpha = None                 # for transparency
        self.tint = None                  # for color tint
        self.blink = False                # for flickering
        self.effect_timers = {}           # active timers {'squash': 0}
        self.effect_data = {}             # active data {'squash': {'start_scale': [x, y], 'target_scale': [x2, y2], 'duration': ,return_back: bool}}
        self.disabled = False
    
@dataclass
class YSortRender:
    entity_id: int
    offset: Tuple[int, int] = (0, 0)  # Y-sorting pivot offset (usually toward character's feet)

class ShadowComponent:
    def __init__(self, entity_id, surface, offset=(0, 0), alpha=128, center=False):
        self.entity_id: int = entity_id
        self.surface: pygame.Surface = surface  # Shadow surface
        self.offset: Tuple[int, int] = offset
        self.alpha: int = alpha  # Default shadow transparency
        self.center: bool = center  # Center the shadow under the entity

        if center:
            self.offset = (self.offset[0] - (surface.get_width() // 2),
                           self.offset[1] - (surface.get_height() // 2))
    
class ProximityFadeComponent:
    def __init__(self, targets, min_dist_squared, max_dist_squared, alpha_range=(0, 255)):
        self.targets = targets
        self.min_dist_squared = min_dist_squared
        self.max_dist_squared = max_dist_squared
        self.alpha_range = alpha_range
        self.current_alpha = alpha_range[1]

        for i, target in enumerate(self.targets):
            self.targets[i] = PlayerTagComponent if target == "player" else EnemyTagComponent if target == "enemy" else target
