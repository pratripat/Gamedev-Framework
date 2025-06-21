import pygame
from ...components.physics import Velocity
from ..animation.animation_state_machine import AnimationStateMachine
from ...components.render_effects import SquashEffect

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
    
    def shoot(self, component_manager, event_manager):
        # component_manager.get(self.entity_id, AnimationStateMachine).set_animation("shoot")
        if not component_manager.get(self.entity_id, SquashEffect):
            component_manager.add(self.entity_id, SquashEffect(
                start_scale=pygame.Vector2(1, 1),
                target_scale=pygame.Vector2(0.5, 1),
                duration=0.34
            ))
        event_manager.emit(GameSceneEvents.SHOOT, entity_id=self.entity_id)

    def on_move(self, direction, held=True):
        self.held[direction] = held
    
    def on_death(self, entity_id):
        if self.entity_id == entity_id:
            self.disable_movement = True

    def update(self, physics_component_manager):
        if self.disable_movement:
            return
        
        dir = pygame.Vector2(0, 0)
        if self.held["up"]: dir.y -= 1
        if self.held["down"]: dir.y += 1
        if self.held["left"]: dir.x -= 1
        if self.held["right"]: dir.x += 1

        if dir.length_squared() > 0: dir = dir.normalize()

        vel = physics_component_manager.get(self.entity_id, Velocity)
        vel.vec = dir * vel.speed # setting the velocity based on direction and speed
        