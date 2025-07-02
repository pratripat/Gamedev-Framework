import pygame
from ...components.physics import Position
from ...utils import CENTER

class Camera:
    def __init__(self):
        self.target_entity_id = None
        self.scroll = pygame.Vector2(0,0)

        self.zoom = 1

    def update(self, dt, component_manager, lerp=False, lerp_speed=15, mouse=None, mouse_ratio=0.5):
        if self.target_entity_id is None: return

        desired_pos = self.scroll.copy()

        target_pos = component_manager.get(self.target_entity_id, Position)
        if target_pos:
            desired_pos = target_pos.vec - CENTER

        # follow mouse
        if mouse:
            desired_pos += (pygame.Vector2(mouse) - CENTER) * mouse_ratio

        # lerp
        if lerp: 
            self.scroll += (desired_pos - self.scroll) * lerp_speed * dt
        else: 
            self.scroll = desired_pos
    
    def set_target(self, entity_id):
        self.target_entity_id = entity_id

    def set_zoom(self, zoom: float):
        self.zoom = max(0.1, zoom)
    

