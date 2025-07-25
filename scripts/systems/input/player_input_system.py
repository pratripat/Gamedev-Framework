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

        event_manager.subscribe(GameSceneEvents.DEATH, self.on_death)
    
    def dash(self):
        pass

    def spawn_bomb(self, cm, em, anim_handler, event_manager):
        spawn_bomb(
            self.entity_id, 
            cm, 
            em, 
            anim_handler, 
            event_manager, 
            data = {
                "pos": cm.get(self.entity_id, Position).vec
            }
        )

    def shoot(self, event_manager):
        event_manager.emit(GameSceneEvents.SHOOT, entity_id=self.entity_id)

    def on_move(self, direction, held=True):
        self.held[direction] = held
    
    def on_death(self, entity_id):
        if self.entity_id == entity_id:
            self.disable_movement = True

    def update(self, component_manager):
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
        