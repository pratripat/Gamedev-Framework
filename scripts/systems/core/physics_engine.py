import pygame

from scripts.components.tags import EnemyTagComponent
from scripts.ecs.component_manager import ComponentManager
from ...components.physics import KnockbackComponent, Position, Velocity
from ...components.physics import CollisionComponent
from ...components.projectile import ProjectileComponent
from ...utils import Quadtree, INITIAL_WINDOW_SIZE, GameSceneEvents, get_unit_direction_towards

class PhysicsEngine:
    def __init__(self, component_manager: ComponentManager, event_manager):
        self.component_manager = component_manager
        self.event_manager = event_manager

        self.event_manager.subscribe(GameSceneEvents.DAMAGE, self._knockback)
    
    def _knockback(self, entity_id, proj_id, **kwargs):
        # Knockback only if the entity that got hit is a enemy
        if self.component_manager.get(entity_id, EnemyTagComponent):
            proj_vel = get_unit_direction_towards(pygame.Vector2(0, 0), self.component_manager.get(proj_id, Velocity).vec)
            self.component_manager.add(
                entity_id,
                KnockbackComponent(proj_vel, 5, duration=0.2)
            )

    def update(self, scroll, fps, dt):
        """
        Update physics using a time delta in seconds (dt). Movement is computed using velocities in units/sec.
        The fps parameter is kept for compatibility with other systems but is NOT used for movement math.
        """
        quadtree = Quadtree(0, (*scroll, *INITIAL_WINDOW_SIZE))

        # Determine multiplier to preserve previous frame-based speeds.
        # If fps is available use it, otherwise fallback to 60 (reasonable default).
        scale = fps if (fps and fps > 0) else 60.0

        # Update all entities with Position and Velocity components
        for entity in self.component_manager.get_entities_with(Position, Velocity):
            position = self.component_manager.get(entity, Position)
            velocity = self.component_manager.get(entity, Velocity)

            # Update position based on velocity when there's no collision component
            collision_component = self.component_manager.get(entity, CollisionComponent)
            if not collision_component:
                # Treat velocity.vec as units-per-frame previously; to convert to units/sec multiply by scale
                # Then multiply by dt (seconds) to get actual displacement.
                position += velocity.vec * dt * scale
                velocity.realistic_vel = velocity.vec.copy()  # realistic_vel mirrors the desired velocity

        # Insert solid collision rects into quadtree for collision checks
        for entity in self.component_manager.get_entities_with(CollisionComponent, Position):
            position = self.component_manager.get(entity, Position)
            collision_component = self.component_manager.get(entity, CollisionComponent)
            rect = pygame.Rect(*(position.vec + collision_component.offset), *collision_component.size)
            quadtree.insert(entity, rect)

        # Handle collisions for non-solid components
        for non_solid_component_entity in self.component_manager.get_entities_with(CollisionComponent):
            non_solid_component = self.component_manager.get(non_solid_component_entity, CollisionComponent)
            if non_solid_component.solid:
                continue

            # Skip projectiles; ProjectileSystem handles their movement/collisions for bullet-hell accuracy
            if self.component_manager.get(non_solid_component_entity, ProjectileComponent):
                continue

            pos = self.component_manager.get(non_solid_component_entity, Position)
            vel = self.component_manager.get(non_solid_component_entity, Velocity)
            rect = pygame.FRect(*(pos.vec + non_solid_component.offset), *non_solid_component.size)

            # Apply knockback if present
            kbc = self.component_manager.get(non_solid_component_entity, KnockbackComponent)
            if kbc:
                vel.vec = kbc.update(dt)
                if kbc.duration <= 0:
                    self.component_manager.remove(non_solid_component_entity, KnockbackComponent)

            collisions = {"top": False, "right": False, "bottom": False, "left": False}

            vel.realistic_vel = vel.vec.copy()

            # Move horizontally using seconds-based dt and scale to match previous behavior
            rect.x += vel.x * dt * scale

            colliding_entities = []
            quadtree.retrieve(colliding_entities, rect)
            for entity, colliding_rect in colliding_entities:
                if entity == non_solid_component_entity:
                    continue

                colliding_component = self.component_manager.get(entity, CollisionComponent)
                if not colliding_component or not colliding_component.solid:
                    continue

                # Check for collision
                if rect.colliderect(colliding_rect):
                    if vel.x > 0:
                        rect.right = colliding_rect.left
                        collisions["right"] = True
                    elif vel.x < 0:
                        rect.left = colliding_rect.right
                        collisions["left"] = True
                    else:
                        vel.realistic_vel.x = 0

            # Move vertically using seconds-based dt and scale to match previous behavior
            rect.y += vel.y * dt * scale

            colliding_entities = []
            quadtree.retrieve(colliding_entities, rect)
            for entity, colliding_rect in colliding_entities:
                if entity == non_solid_component_entity:
                    continue

                colliding_component = self.component_manager.get(entity, CollisionComponent)
                if not colliding_component or not colliding_component.solid:
                    continue

                # Check for collision
                if rect.colliderect(colliding_rect):
                    if vel.y > 0:
                        rect.bottom = colliding_rect.top
                        collisions["bottom"] = True
                    elif vel.y < 0:
                        rect.top = colliding_rect.bottom
                        collisions["top"] = True
                    else:
                        vel.realistic_vel.y = 0

            if any(collisions.values()):
                self.event_manager.emit(GameSceneEvents.COLLISION, entity_id=non_solid_component_entity, collisions=collisions)

            pos.vec.update(pygame.Vector2(rect.topleft) - non_solid_component.offset)
