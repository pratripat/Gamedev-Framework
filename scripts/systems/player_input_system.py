import pygame
from ..components.physics import Velocity
from .animation_state_machine import AnimationStateMachine

class PlayerInputSystem:
    def __init__(self, entity_id):
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
    
    def shoot(self, component_manager, event_manager):
        component_manager.get(self.entity_id, AnimationStateMachine).set_animation("shoot")
        event_manager.emit("shoot", entity_id=self.entity_id)

    def on_move(self, direction, held=True):
        self.held[direction] = held

    def update(self, physics_component_manager):
        dir = pygame.Vector2(0, 0)
        if self.held["up"]: dir.y -= 1
        if self.held["down"]: dir.y += 1
        if self.held["left"]: dir.x -= 1
        if self.held["right"]: dir.x += 1

        if dir.length_squared() > 0: dir = dir.normalize()

        vel = physics_component_manager.get(self.entity_id, Velocity)
        vel.vec = dir * vel.speed # setting the velocity based on direction and speed
        