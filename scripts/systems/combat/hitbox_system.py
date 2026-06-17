import pygame
from ...utils import INITIAL_WINDOW_SIZE, GameSceneEvents, collision_occured
from ...components.combat import HurtBoxComponent, HitBoxComponent, HealthComponent
from ...components.physics import Position, Velocity
from ...components.projectile import ProjectileComponent
from ...components.tags import PlayerTagComponent

class HitBoxSystem:
    def can_hit(self, hitbox: HitBoxComponent, hurtbox: HurtBoxComponent) -> bool:
        return (hitbox.mask & hurtbox.layer) != 0

    def update(self, event_manager, component_manager, scroll, dt=0):
        # Tick generic ECS ProjectileComponent lifetimes (since ProjectileSystem was removed)
        proj_dict = component_manager._components.get(ProjectileComponent, {})
        for eid, proj in list(proj_dict.items()):
            proj.lifetime -= dt
            if proj.lifetime <= 0:
                component_manager.remove(eid, ProjectileComponent)
                if component_manager.get(eid, HitBoxComponent):
                    component_manager.remove(eid, HitBoxComponent)

        # Alias dicts for speed
        hurtbox_dict = component_manager._components.get(HurtBoxComponent, {})
        hitbox_dict = component_manager._components.get(HitBoxComponent, {})
        pos_dict = component_manager._components.get(Position, {})
        player_tag_dict = component_manager._components.get(PlayerTagComponent, {})
        health_dict = component_manager._components.get(HealthComponent, {})

        # Build Pygame-native dictionary for ultra-fast C-level collision detection
        hurtbox_rects = {}
        for entity_id, hurtbox in hurtbox_dict.items():
            if hurtbox.disabled:
                continue
            pos_comp = pos_dict.get(entity_id)
            if not pos_comp:
                continue

            # Check invincibility
            is_player = entity_id in player_tag_dict
            health = health_dict.get(entity_id)
            if is_player and health and health.invincibility_timer > 0:
                continue
        
            pos = pos_comp.vec
            rect = pygame.Rect(pos.x + hurtbox.offset.x, pos.y + hurtbox.offset.y, hurtbox.size[0], hurtbox.size[1])
            hurtbox_rects[entity_id] = rect
        
        if not hurtbox_rects:
            return

        for attacker, hitbox in hitbox_dict.items():
            if hitbox.disabled:
                continue
            pos_comp_a = pos_dict.get(attacker)
            if not pos_comp_a:
                continue

            pos_a = pos_comp_a.vec
            hitbox_rect = pygame.Rect(pos_a.x + hitbox.offset.x, pos_a.y + hitbox.offset.y, hitbox.size[0], hitbox.size[1])

            # C-level broadphase collision
            collisions = hitbox_rect.collidedictall(hurtbox_rects, 1)

            seen = set()
            for defender, hurtbox_rect in collisions:
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

                # Narrow phase
                # For now just emit damage since colliderect is true
                projectile = proj_dict.get(attacker)
                if projectile:
                    if defender in projectile.hits:
                        continue
                    projectile.hits.add(defender)
                    
                    vel_comp = component_manager._components.get(Velocity, {}).get(attacker)
                    proj_vel = vel_comp.vec.copy() if vel_comp else pygame.Vector2(0, 0)
                    event_manager.emit(
                        GameSceneEvents.DAMAGE, 
                        entity_id=defender, 
                        proj_id=attacker, 
                        damage=projectile.damage, 
                        effects=projectile.effects,
                        proj_vel=proj_vel,
                        proj_pos=pos_a.copy()
                    )
                else:
                    # Otherwise, emit a generic damage event
                    # print(f'[HIT BOX SYSTEM] Non projectile type has damaged entity {defender} (DEBUG)')
                    pass