import pygame
from ...components.physics import Position, Velocity
from ...components.combat import WeaponComponent
from ...components.tags import PlayerTagComponent

from ...utils import CollisionLayer, GameSceneEvents

class WeaponSystem:
    def __init__(self, component_manager, entity_manager, camera, event_manager, resource_manager):
        self.component_manager = component_manager
        self.entity_manager = entity_manager
        self.resource_manager = resource_manager
        self.camera = camera

        event_manager.subscribe(GameSceneEvents.SHOOT, self.on_shoot)
        event_manager.subscribe(GameSceneEvents.DEATH, self._disable_weapon_comp)

    def _disable_weapon_comp(self, entity_id):
        weapon_comp = self.component_manager.get(entity_id, WeaponComponent)
        if weapon_comp:
            weapon_comp.disabled = True
    
    def on_shoot(self, entity_id):
        weapon_component = self.component_manager.get(entity_id, WeaponComponent)
        if weapon_component.disabled:
            return
        
        if weapon_component.can_shoot:
            shoot_pos = self.component_manager.get(entity_id, Position).vec.copy()
            realistic_vel = self.component_manager.get(entity_id, Velocity).realistic_vel

            projectile_data = weapon_component.projectile_data.copy()

            # checks if player shot
            if self.component_manager.get(entity_id, PlayerTagComponent):
                target_pos = pygame.mouse.get_pos() # mouse position

                projectile_data['start_pos'] = shoot_pos
                projectile_data['target_pos'] = target_pos + self.camera.scroll

                projectile_data['layer'] = CollisionLayer.PLAYER
                projectile_data['mask'] = CollisionLayer.create_mask(CollisionLayer.ENEMY)

                # making the proj
                projectiles = weapon_component.shoot_fn(entity_id, self.component_manager, self.entity_manager, self.resource_manager, projectile_data)
                # making sure all the projs have the same vel as that of the entity
                for proj_id in projectiles:
                    proj_vel = self.component_manager.get(proj_id, Velocity).vec
                    proj_vel += realistic_vel
                    proj_vel = proj_vel.normalize()
                    proj_vel *= projectile_data['speed']

            # enemy is shooting
            else:
                # print(f'[WEAPON SYSTEM] Entity: {entity_id} has shot... (DEBUG)')
                
                target_pos = pygame.Vector2(1, 0) + shoot_pos # default target position
                if projectile_data['towards_player']:
                    player_pos = self.component_manager.get(self.entity_manager.player_id, Position)
                    if player_pos:
                        target_pos = player_pos.vec.copy()
                
                projectile_data['start_pos'] = shoot_pos
                projectile_data['target_pos'] = target_pos

                projectile_data['layer'] = CollisionLayer.ENEMY
                projectile_data['mask'] = CollisionLayer.create_mask(CollisionLayer.PLAYER)

                weapon_component.shoot_fn(entity_id, self.component_manager, self.entity_manager, self.resource_manager, projectile_data)

            weapon_component.shot = True
        
    def update(self, dt):
        for entity_id in self.component_manager.get_entities_with(WeaponComponent):
            weapon = self.component_manager.get(entity_id, WeaponComponent)

            if weapon.shot:
                weapon.time += dt
            
            if weapon.time >= weapon.cooldown:
                weapon.time = 0
                weapon.shot = False