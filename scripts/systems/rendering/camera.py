import pygame, math, random
from ...components.physics import Position
from ...utils import CENTER, VIRTUAL_WINDOW_SIZE

class Camera:
    def __init__(self):
        self.target_entity_id = None
        self._scroll = pygame.Vector2(0,0)
        self.shake_offset = pygame.Vector2(0,0)
        self.shake_timer = 0.0
        self.shake_intensity = 0.0
        self._scratch = pygame.Vector2(0, 0)
        self._cached_scroll = pygame.Vector2(0, 0)
        self._cached_scroll_int = pygame.Vector2(0, 0)
        self._cached_center = pygame.Vector2(0, 0)
        self._cached_rect = pygame.Rect(0, 0, *VIRTUAL_WINDOW_SIZE)

        self.zoom = 1

    @property
    def scroll(self):
        return self._cached_scroll

    @property
    def scroll_int(self):
        return self._cached_scroll_int

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
            desired_pos.x += (mouse[0] - CENTER.x) * mouse_ratio
            desired_pos.y += (mouse[1] - CENTER.y) * mouse_ratio

        # lerp
        if lerp: 
            alpha = 1 - math.exp(-lerp_speed * dt)
            self._scroll += (desired_pos - self._scroll) * alpha
        else: 
            self._scroll = desired_pos
            
        if self.shake_timer > 0:
            self.shake_timer -= dt
            self.shake_offset.update(
                random.uniform(-self.shake_intensity, self.shake_intensity),
                random.uniform(-self.shake_intensity, self.shake_intensity)
            )
        else:
            self.shake_offset.update(0, 0)
            self.shake_intensity = 0.0

        self._cached_scroll.update(self._scroll)
        self._cached_scroll += self.shake_offset
        self._cached_scroll_int.update(int(self._cached_scroll.x), int(self._cached_scroll.y))
        self._cached_center.update(self._cached_scroll)
        self._cached_center += CENTER
        self._cached_rect.topleft = self._cached_scroll_int

    def set_target(self, entity_id):
        self.target_entity_id = entity_id

    def set_zoom(self, zoom: float):
        self.zoom = max(0.1, zoom)

    @property
    def rect(self):
        return self._cached_rect
    
    @property
    def center(self):
        return self._cached_center
    

