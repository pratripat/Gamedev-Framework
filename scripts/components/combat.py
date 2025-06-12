import pygame
from ..utils import GameSceneEvents
from ..systems.animation_state_machine import AnimationStateMachine

class WeaponComponent:
    def __init__(self, cooldown, shoot_fn, projectile_data):
        self.cooldown = cooldown
        self.shoot_fn = shoot_fn
        self.projectile_data = projectile_data

        self.time = 0
        self.shot = False

    @property
    def can_shoot(self):
        return not self.shot

class HitBoxComponent:
    def __init__(self, entity_id, offset, size, shape, layer: int, mask: int):
        self.entity_id = entity_id
        self.offset = offset
        self.size = size
        self.shape = shape
        self.layer = layer
        self.mask = mask

class HurtBoxComponent:
    def __init__(self, entity_id, offset, size, shape, layer: int):
        self.entity_id = entity_id
        self.offset = offset
        self.size = size
        self.shape = shape
        self.layer = layer

class HealthComponent:
    iframetimer = 1/6
    def __init__(self, entity_id, max_health, event_manager, component_manager):
        self.entity_id = entity_id
        self.health = self.max_health = max_health
        self.invincibility_timer = 0
        self.event_manager = event_manager
        self.component_manager = component_manager

        self.effects = []

        event_manager.subscribe(GameSceneEvents.DAMAGE, self.take_damage)

    def take_damage(self, entity_id, damage, effects):
        if entity_id != self.entity_id:
            return
        
        if self.invincibility_timer > 0:
            # Still invincible, ignore damage
            return
        
        self.health -= damage
        self.effects = effects

        # TEMP
        # set animation to hit
        self.component_manager.get(self.entity_id, AnimationStateMachine).set_animation("damage")

        self.invincibility_timer = self.iframetimer
        if self.health <= 0:
            self.health = 0
            # Trigger death logic here, e.g., event_manager.publish("entity_died", self.entity_id)
            self.event_manager.emit(GameSceneEvents.DEATH, entity_id=self.entity_id)
        

