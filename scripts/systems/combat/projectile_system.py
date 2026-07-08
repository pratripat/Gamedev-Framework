import pygame
from ...components.projectile import ProjectileComponent
from ...components.physics import Velocity, Position, CollisionComponent
from ...components.combat import HurtBoxComponent, HealthComponent
from ...utils import GameSceneEvents, Quadtree, INITIAL_WINDOW_SIZE, SCALE

class ProjectileSystem:
    def __init__(self, component_manager, event_manager):
        self.component_manager = component_manager
        self.event_manager = event_manager
        # Keep subscriptions for fallback; collisions for projectiles are handled here directly
        event_manager.subscribe(GameSceneEvents.DAMAGE, self._handle_penetration)
    
    def _handle_projectile_collision(self, entity_id, collisions):
        # kept for compatibility but projectiles are handled directly in update()
        proj_comp = self.component_manager.get(entity_id, ProjectileComponent)
        if proj_comp is None:
            return

        if proj_comp.data.get("bounce", 0) > 0:
            proj_comp.data["bounce"] -= 1
            vel = self.component_manager.get(entity_id, Velocity)
            if collisions["left"] or collisions["right"]:
                vel.x *= -1
            if collisions["bottom"] or collisions["top"]:
                vel.y *= -1
        else:
            self.component_manager.remove_all(entity_id)
    
    def _handle_penetration(self, entity_id, proj_id, **data):
        proj_comp = self.component_manager.get(proj_id, ProjectileComponent)
        if proj_comp is None:
            return
        
        if proj_comp.data.get("penetration", 0) > 0:
            proj_comp.data["penetration"] -= 1
        else:
            self.component_manager.remove_all(proj_id)

    def update(self, dt, fps=None, quadtree=None):
        # Alias dictionaries for speed
        col_dict = self.component_manager._components.get(CollisionComponent, {})
        pos_dict = self.component_manager._components.get(Position, {})
        hurtbox_dict = self.component_manager._components.get(HurtBoxComponent, {})
        proj_dict = self.component_manager._components.get(ProjectileComponent, {})
        vel_dict = self.component_manager._components.get(Velocity, {})

        # Build quadtree of solid and water collision rects if not provided
        if quadtree is None:
            from ...utils import VIRTUAL_WINDOW_SIZE, Quadtree
            quadtree = Quadtree(0, (0, 0, *VIRTUAL_WINDOW_SIZE))
            for entity in self.component_manager.get_entities_with(CollisionComponent, Position):
                comp = col_dict.get(entity)
                pos = pos_dict.get(entity)
                if comp and pos:
                    # Include solid (walls) and non-solid (water) for detection
                    # We SKIP characters' collision boxes (feet) for projectiles as requested.
                    if hurtbox_dict.get(entity):
                        continue
                        
                    rect = pygame.Rect(*(pos.vec + comp.offset), *comp.size)
                    quadtree.insert(entity, rect)

        # Movement scale
        movement_scale = fps if (fps and fps > 0) else 60.0

        nearby = []
        for entity_id in list(self.component_manager.get_entities_with(ProjectileComponent)):
            projectile = proj_dict.get(entity_id)
            pos_comp = pos_dict.get(entity_id)
            vel = vel_dict.get(entity_id)
            col = col_dict.get(entity_id)

            if not projectile or not pos_comp or not vel or not col:
                continue

            # lifetime
            projectile.lifetime -= dt
            if projectile.lifetime <= 0:
                self.component_manager.remove_all(entity_id)
                continue

            # Prepare movement rect
            rect = pygame.FRect(*(pos_comp.vec + col.offset), *col.size)
            col_offset = col.offset

            # Move horizontally
            rect.x += vel.x * dt * movement_scale
            nearby.clear()
            quadtree.retrieve(nearby, rect)
            seen_h = set()
            for other_entity, other_rect in nearby:
                if other_entity in seen_h: continue
                seen_h.add(other_entity)
                
                if other_entity == entity_id:
                    continue
                other_comp = col_dict.get(other_entity)
                if not other_comp: continue

                # 1. Water Splash / Pass-Through Detection
                if not getattr(other_comp, "blocks_projectiles", True):
                    if rect.colliderect(other_rect):
                        self.event_manager.emit(
                            GameSceneEvents.WATER_SPLASH,
                            pos=(rect.centerx, rect.centery),
                            vel=vel.vec,
                            size=col.size[0]
                        )
                    continue

                # 2. Solid Wall collision
                if other_comp.solid:
                    if rect.colliderect(other_rect):
                        self.event_manager.emit(
                            GameSceneEvents.PROJECTILE_COLLISION,
                            pos=(rect.centerx, rect.centery),
                            vel=vel.vec,
                            target_type="environment",
                            size=col.size[0]
                        )
                        
                        if projectile.data.get("bounce", 0) > 0:
                            projectile.data["bounce"] -= 1
                            vel.x *= -1
                        else:
                            self.component_manager.remove_all(entity_id)
                            break

            # If Position component no longer exists, the projectile was removed
            if not pos_dict.get(entity_id):
                continue

            # Move vertically
            rect.y += vel.y * dt * movement_scale
            nearby.clear()
            quadtree.retrieve(nearby, rect)
            seen_v = set()
            for other_entity, other_rect in nearby:
                if other_entity in seen_v: continue
                seen_v.add(other_entity)
                
                if other_entity == entity_id:
                    continue
                other_comp = col_dict.get(other_entity)
                if not other_comp: continue

                # 1. Water Splash
                if not getattr(other_comp, "blocks_projectiles", True):
                    if rect.colliderect(other_rect):
                        self.event_manager.emit(
                            GameSceneEvents.WATER_SPLASH,
                            pos=(rect.centerx, rect.centery),
                            vel=vel.vec,
                            size=col.size[0]
                        )
                    continue

                # 2. Solid Wall collision
                if other_comp.solid:
                    if rect.colliderect(other_rect):
                        self.event_manager.emit(
                            GameSceneEvents.PROJECTILE_COLLISION,
                            pos=(rect.centerx, rect.centery),
                            vel=vel.vec,
                            target_type="environment",
                            size=col.size[0]
                        )

                        if projectile.data.get("bounce", 0) > 0:
                            projectile.data["bounce"] -= 1
                            vel.y *= -1
                        else:
                            self.component_manager.remove_all(entity_id)
                            break

            # If Position component no longer exists, the projectile was removed
            if not pos_dict.get(entity_id):
                continue

            # Apply final position
            pos_comp.vec.x = rect.x - col_offset.x
            pos_comp.vec.y = rect.y - col_offset.y
