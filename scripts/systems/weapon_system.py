import pygame
from ..components.physics import Position, Velocity
from ..components.combat import WeaponComponent
from ..components.tags import PlayerTagComponent

from ..utils import CollisionLayer, GameSceneEvents

class WeaponSystem:
    def __init__(self, component_manager, entity_manager, camera, event_manager):
        self.component_manager = component_manager
        self.entity_manager = entity_manager
        self.camera = camera

        event_manager.subscribe(GameSceneEvents.SHOOT, self.on_shoot)
    
    def on_shoot(self, entity_id):
        weapon_component = self.component_manager.get(entity_id, WeaponComponent)
        if weapon_component.can_shoot:
            shoot_pos = self.component_manager.get(entity_id, Position).vec.copy()
            vel = self.component_manager.get(entity_id, Velocity).vec

            projectile_data = weapon_component.projectile_data.copy()

            # checks if player shot
            if self.component_manager.get(entity_id, PlayerTagComponent):
                target_pos = pygame.mouse.get_pos() # mouse position

                projectile_data['start_pos'] = shoot_pos
                projectile_data['target_pos'] = target_pos + self.camera.scroll

                projectile_data['layer'] = CollisionLayer.PLAYER
                projectile_data['mask'] = CollisionLayer.create_mask(CollisionLayer.ENEMY)

                # making the proj
                projectiles = weapon_component.shoot_fn(entity_id, self.component_manager, self.entity_manager, projectile_data)
                # making sure all the projs have the same vel as that of the entity
                for proj_id in projectiles:
                    proj_vel = self.component_manager.get(proj_id, Velocity).vec
                    proj_vel += vel
            
            # enemy is shooting
            else:
                # print(f'[WEAPON SYSTEM] Entity: {entity_id} has shot... (DEBUG)')
                
                target_pos = pygame.Vector2(1, 0) + shoot_pos # default target position
                if projectile_data['towards_player']:
                    target_pos = self.component_manager.get(self.entity_manager.player_id, Position).vec.copy()
                
                projectile_data['start_pos'] = shoot_pos
                projectile_data['target_pos'] = target_pos

                projectile_data['layer'] = CollisionLayer.ENEMY
                projectile_data['mask'] = CollisionLayer.create_mask(CollisionLayer.PLAYER)

                weapon_component.shoot_fn(entity_id, self.component_manager, self.entity_manager, projectile_data)

            weapon_component.shot = True
        
    def update(self, fps, dt):
        for entity_id in self.component_manager.get_entities_with(WeaponComponent):
            weapon = self.component_manager.get(entity_id, WeaponComponent)

            if weapon.shot:
                weapon.time += dt / fps
            
            if weapon.time >= weapon.cooldown:
                weapon.time = 0
                weapon.shot = False