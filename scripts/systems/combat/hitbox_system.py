import pygame
from ...utils import Quadtree, INITIAL_WINDOW_SIZE, GameSceneEvents
from ...components.combat import HurtBoxComponent, HitBoxComponent, HealthComponent
from ...components.physics import Position
from ...components.projectile import ProjectileComponent
from ...components.tags import PlayerTagComponent

class HitBoxSystem:
    def can_hit(self, hitbox: HitBoxComponent, hurtbox: HurtBoxComponent) -> bool:
        return (hitbox.mask & hurtbox.layer) != 0

    def update(self, event_manager, component_manager, entity_list, scroll):
        quadtree = Quadtree(0, (*scroll, *INITIAL_WINDOW_SIZE))

        # insert all hitboxes to qt
        for entity_id in entity_list:
            hurtbox = component_manager.get(entity_id, HurtBoxComponent)
            pos = component_manager.get(entity_id, Position).vec
            if not hurtbox or not pos or hurtbox.disabled:
                continue

            # Check if the entity's health has an invincibility timer greater than 0
            is_player = component_manager.get(entity_id, PlayerTagComponent)
            health = component_manager.get(entity_id, HealthComponent)
            if is_player and health and health.invincibility_timer > 0:
                continue  # Skip collision handling for invincible entities
        
            rect = pygame.Rect(*(pos + hurtbox.offset), *hurtbox.size)
            quadtree.insert(entity_id, rect)
        
        # for each hitbox, retrieve nearby hurtboxes
        for attacker in entity_list:
            hitbox = component_manager.get(attacker, HitBoxComponent)
            pos_a = component_manager.get(attacker, Position).vec
            if not hitbox or not pos_a or hitbox.disabled:
                continue

            hitbox_rect = pygame.Rect(*(pos_a + hitbox.offset), *hitbox.size)
            nearby_hurtboxes = []

            quadtree.retrieve(nearby_hurtboxes, hitbox_rect)

            for defender, hurtbox_rect in nearby_hurtboxes:
                if attacker == defender:
                    continue

                hurtbox = component_manager.get(defender, HurtBoxComponent)
                if not hurtbox:
                    continue

                if not self.can_hit(hitbox, hurtbox):
                    continue

                pos_b = component_manager.get(defender, Position).vec
                if not pos_b:
                    continue
                
                # Check for collision between hitbox and hurtbox
                if hitbox_rect.colliderect(hurtbox_rect):
                    # Handle collision logic here
                    
                    # print(f'[HIT BOX SYSTEM] {attacker} hit {defender} (DEBUG)')
                    
                    projectile = component_manager.get(attacker, ProjectileComponent)
                    if projectile:
                        # If the attacker is a projectile, emit a damage event with the projectile's data
                        event_manager.emit(GameSceneEvents.DAMAGE, entity_id=defender, proj_id=attacker, damage=projectile.damage, effects=projectile.effects)
                    else:
                        # Otherwise, emit a generic damage event
                        # print(f'[HIT BOX SYSTEM] Non projectile type has damaged entity {defender} (DEBUG)')
                        pass