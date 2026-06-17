import pygame
from ...utils import Quadtree, INITIAL_WINDOW_SIZE, GameSceneEvents, collision_occured
from ...components.combat import HurtBoxComponent, HitBoxComponent, HealthComponent
from ...components.physics import Position
from ...components.projectile import ProjectileComponent
from ...components.tags import PlayerTagComponent

class HitBoxSystem:
    def can_hit(self, hitbox: HitBoxComponent, hurtbox: HurtBoxComponent) -> bool:
        return (hitbox.mask & hurtbox.layer) != 0

    def update(self, event_manager, component_manager, entity_list, scroll):
        quadtree = Quadtree(0, (*scroll, *INITIAL_WINDOW_SIZE))

        # Alias dicts for speed
        hurtbox_dict = component_manager._components.get(HurtBoxComponent, {})
        hitbox_dict = component_manager._components.get(HitBoxComponent, {})
        pos_dict = component_manager._components.get(Position, {})
        player_tag_dict = component_manager._components.get(PlayerTagComponent, {})
        health_dict = component_manager._components.get(HealthComponent, {})

        # insert all hitboxes to qt
        for entity_id in entity_list:
            hurtbox = hurtbox_dict.get(entity_id)
            pos_comp = pos_dict.get(entity_id)
            if not hurtbox or not pos_comp or hurtbox.disabled:
                continue

            pos = pos_comp.vec

            # Check if the entity's health has an invincibility timer greater than 0
            is_player = player_tag_dict.get(entity_id)
            health = health_dict.get(entity_id)
            if is_player and health and health.invincibility_timer > 0:
                continue  # Skip collision handling for invincible entities
        
            rect = pygame.Rect(*(pos + hurtbox.offset), *hurtbox.size)
            quadtree.insert(entity_id, rect)
        
        # for each hitbox, retrieve nearby hurtboxes
        for attacker in entity_list:
            hitbox = hitbox_dict.get(attacker)
            pos_comp_a = pos_dict.get(attacker)
            if not hitbox or not pos_comp_a or hitbox.disabled:
                continue

            pos_a = pos_comp_a.vec

            hitbox_rect = pygame.Rect(*(pos_a + hitbox.offset), *hitbox.size)
            nearby_hurtboxes = []

            quadtree.retrieve(nearby_hurtboxes, hitbox_rect)

            seen = set()
            for defender, hurtbox_rect in nearby_hurtboxes:
                if defender in seen:
                    continue
                seen.add(defender)
                
                if attacker == defender:
                    continue

                hurtbox = hurtbox_dict.get(defender)
                if not hurtbox:
                    continue

                if not self.can_hit(hitbox, hurtbox):
                    continue

                pos_b_comp = pos_dict.get(defender)
                if not pos_b_comp:
                    continue
                pos_b = pos_b_comp.vec

                # TEMP
                # if hitbox_rect.colliderect(hurtbox_rect):

                # Check for collision between hitbox and hurtbox
                if collision_occured(hitbox, hitbox_rect, hurtbox, hurtbox_rect):
                    # print(f'[HIT BOX SYSTEM] {attacker} hit {defender} (DEBUG)')
                    
                    projectile = component_manager.get(attacker, ProjectileComponent)
                    if projectile:
                        if defender in projectile.hits:
                            continue
                        projectile.hits.add(defender)
                        
                        # If the attacker is a projectile, emit a damage event with the projectile's data
                        event_manager.emit(GameSceneEvents.DAMAGE, entity_id=defender, proj_id=attacker, damage=projectile.damage, effects=projectile.effects)
                    else:
                        # Otherwise, emit a generic damage event
                        # print(f'[HIT BOX SYSTEM] Non projectile type has damaged entity {defender} (DEBUG)')
                        pass