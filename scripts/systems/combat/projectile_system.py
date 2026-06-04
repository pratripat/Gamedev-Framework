import pygame
from ...components.projectile import ProjectileComponent
from ...components.physics import Velocity, Position, CollisionComponent
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

    def update(self, dt, fps=None):
        # Build quadtree of solid collision rects for efficient queries
        quadtree = Quadtree(0, (0, 0, *INITIAL_WINDOW_SIZE))
        for entity in self.component_manager.get_entities_with(CollisionComponent, Position):
            comp = self.component_manager.get(entity, CollisionComponent)
            pos = self.component_manager.get(entity, Position)
            if comp and comp.solid and pos:
                rect = pygame.Rect(*(pos.vec + comp.offset), *comp.size)
                quadtree.insert(entity, rect)

        # Movement scale: use fps if available to restore previous per-frame speeds
        movement_scale = fps if (fps and fps > 0) else 60.0

        for entity_id in list(self.component_manager.get_entities_with(ProjectileComponent)):
            projectile = self.component_manager.get(entity_id, ProjectileComponent)
            pos_comp = self.component_manager.get(entity_id, Position)
            vel = self.component_manager.get(entity_id, Velocity)
            col = self.component_manager.get(entity_id, CollisionComponent)

            if not projectile or not pos_comp or not vel or not col:
                continue

            # lifetime
            projectile.lifetime -= dt
            if projectile.lifetime <= 0:
                self.component_manager.remove_all(entity_id)
                continue

            # Prepare movement rect
            rect = pygame.FRect(*(pos_comp.vec + col.offset), *col.size)

            collided = False
            collisions = {"top": False, "right": False, "bottom": False, "left": False}

            # Move horizontally (restore per-frame behaviour using movement_scale)
            rect.x += vel.x * dt * movement_scale
            nearby = []
            quadtree.retrieve(nearby, rect)
            for other_entity, other_rect in nearby:
                if other_entity == entity_id:
                    continue
                other_comp = self.component_manager.get(other_entity, CollisionComponent)
                # Skip non-solid and collision boxes that don't block projectiles (e.g., water)
                if not other_comp or not other_comp.solid or not getattr(other_comp, "blocks_projectiles", True):
                    continue

                if rect.colliderect(other_rect):
                    if vel.x > 0:
                        rect.right = other_rect.left
                        collisions["right"] = True
                    elif vel.x < 0:
                        rect.left = other_rect.right
                        collisions["left"] = True

                    collided = True
                    # Handle bounce/kill
                    if projectile.data.get("bounce", 0) > 0:
                        projectile.data["bounce"] -= 1
                        vel.x *= -1
                    else:
                        self.component_manager.remove_all(entity_id)
                        collided = True
                        break
            # If Position component no longer exists, the projectile was removed
            if not self.component_manager.get(entity_id, Position):
                continue

            # Move vertically (restore per-frame behaviour using movement_scale)
            rect.y += vel.y * dt * movement_scale
            nearby = []
            quadtree.retrieve(nearby, rect)
            for other_entity, other_rect in nearby:
                if other_entity == entity_id:
                    continue
                other_comp = self.component_manager.get(other_entity, CollisionComponent)
                # Skip non-solid and collision boxes that don't block projectiles (e.g., water)
                if not other_comp or not other_comp.solid or not getattr(other_comp, "blocks_projectiles", True):
                    continue

                if rect.colliderect(other_rect):
                    if vel.y > 0:
                        rect.bottom = other_rect.top
                        collisions["bottom"] = True
                    elif vel.y < 0:
                        rect.top = other_rect.bottom
                        collisions["top"] = True

                    collided = True
                    if projectile.data.get("bounce", 0) > 0:
                        projectile.data["bounce"] -= 1
                        vel.y *= -1
                    else:
                        self.component_manager.remove_all(entity_id)
                        collided = True
                        break

            # If Position component no longer exists, the projectile was removed
            if not self.component_manager.get(entity_id, Position):
                continue

            # Apply final position
            pos_comp.vec.update(pygame.Vector2(rect.topleft) - col.offset)

            # Optionally, emit collision event for other systems if needed
            if any(collisions.values()):
                try:
                    self.event_manager.emit(GameSceneEvents.COLLISION, entity_id=entity_id, collisions=collisions)
                except Exception:
                    pass
