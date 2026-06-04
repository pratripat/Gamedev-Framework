import pygame
from ...components.physics import Velocity, Position
from ...weapons.bullet_patterns import spawn_bomb

from ...utils import GameSceneEvents

class PlayerInputSystem:
    def __init__(self, entity_id, event_manager):
        """
        Initializes a player with a given entity ID.

        :param entity_id: The unique identifier for the player entity.
        """
        self.entity_id = entity_id
        self.held = {
            "up": False,
            "down": False,
            "left": False,
            "right": False
        }
        self.disable_movement = False

        # Bomb cooldown state
        self.bomb_cooldown = 3.0  # seconds
        self.bomb_timer = 0.0
        self.active_bomb_id = None

        self.event_manager = event_manager
        event_manager.subscribe(GameSceneEvents.DEATH, self.on_death)
        # Listen for bomb burst events to clear active bomb
        try:
            event_manager.subscribe('bomb_burst', self._on_bomb_burst)
        except Exception:
            pass
    
    def dash(self):
        pass

    def _on_bomb_burst(self, entity_id, **kwargs):
        # Clear active bomb if it matches
        if self.active_bomb_id == entity_id:
            self.active_bomb_id = None

    def spawn_bomb(self, cm, em, anim_handler, event_manager):
        # Only spawn if cooldown elapsed and no active bomb
        if self.bomb_timer > 0 or self.active_bomb_id is not None:
            return None

        bomb_id = spawn_bomb(
            self.entity_id, 
            cm, 
            em, 
            anim_handler, 
            event_manager, 
            data = {
                "pos": cm.get(self.entity_id, Position).vec,
                "timer": 0.75,
                "radius": 150
            }
        )

        # start cooldown and track active bomb
        if bomb_id is not None:
            self.bomb_timer = self.bomb_cooldown
            self.active_bomb_id = bomb_id

        return bomb_id

    def shoot(self, event_manager):
        event_manager.emit(GameSceneEvents.SHOOT, entity_id=self.entity_id)

    def on_move(self, direction, held=True):
        self.held[direction] = held
    
    def on_death(self, entity_id):
        if self.entity_id == entity_id:
            self.disable_movement = True

    def update(self, component_manager, dt):
        # Update bomb cooldown timer
        if self.bomb_timer > 0:
            self.bomb_timer -= dt
            if self.bomb_timer < 0:
                self.bomb_timer = 0

        if self.disable_movement:
            return
        
        dir = pygame.Vector2(0, 0)
        if self.held["up"]: dir.y -= 1
        if self.held["down"]: dir.y += 1
        if self.held["left"]: dir.x -= 1
        if self.held["right"]: dir.x += 1

        if dir.length_squared() > 0: dir = dir.normalize()

        vel = component_manager.get(self.entity_id, Velocity)
        vel.vec = dir * vel.speed # setting the velocity based on direction and speed
        