import pygame, math, random
from ...components.physics import Position
from ...utils import CENTER, INITIAL_WINDOW_SIZE, VIRTUAL_WINDOW_SIZE

class Camera:
    def __init__(self):
        self.target_entity_id = None
        self._scroll = pygame.Vector2(0,0)
        self.shake_offset = pygame.Vector2(0,0)
        self.shake_timer = 0.0
        self.shake_intensity = 0.0

        self.zoom = 1

    @property
    def scroll(self):
        return self._scroll + self.shake_offset

    def trigger_shake(self, intensity: float, duration: float):
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_timer = max(self.shake_timer, duration)

    def update(self, dt, component_manager, lerp=False, lerp_speed=15, mouse=None, mouse_ratio=0.5):
        if self.target_entity_id is None: return

        desired_pos = self._scroll.copy()

        target_pos = component_manager.get(self.target_entity_id, Position)
        if target_pos:
            desired_pos = target_pos.vec - CENTER

        # follow mouse
        if mouse:
            desired_pos += (pygame.Vector2(mouse) - CENTER) * mouse_ratio

        # lerp
        if lerp: 
            alpha = 1 - math.exp(-lerp_speed * dt)
            self._scroll += (desired_pos - self._scroll) * alpha
        else: 
            self._scroll = desired_pos
            
        if self.shake_timer > 0:
            self.shake_timer -= dt
            self.shake_offset = pygame.Vector2(
                random.uniform(-self.shake_intensity, self.shake_intensity),
                random.uniform(-self.shake_intensity, self.shake_intensity)
            )
        else:
            self.shake_offset = pygame.Vector2(0, 0)
            self.shake_intensity = 0.0
    
    def set_target(self, entity_id):
        self.target_entity_id = entity_id

    def set_zoom(self, zoom: float):
        self.zoom = max(0.1, zoom)
    
    @property
    def rect(self):
        # We now render to a half-sized virtual surface, so culling should match that
        return pygame.Rect(*self.scroll, *VIRTUAL_WINDOW_SIZE)
    

