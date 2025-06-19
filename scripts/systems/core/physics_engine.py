import pygame
from ...components.physics import Position, Velocity
from ...components.physics import CollisionComponent
from ...utils import Quadtree, INTIAL_WINDOW_SIZE

class PhysicsEngine:
    def __init__(self, component_manager):
        self.component_manager = component_manager

    def update(self, scroll, dt):
        quadtree = Quadtree(0, (*scroll, *INTIAL_WINDOW_SIZE))

        # Update all entities with Position and Velocity components
        for entity in self.component_manager.get_entities_with(Position, Velocity):
            position = self.component_manager.get(entity, Position)
            velocity = self.component_manager.get(entity, Velocity)

            # Update position based on velocity
            collision_component = self.component_manager.get(entity, CollisionComponent)
            if not collision_component:
                # Simple movement without collision handling
                position += velocity * dt
                velocity.realistic_vel = velocity.vec.copy() # the vel of the entity is the same as the velocity vector

        for entity in self.component_manager.get_entities_with(CollisionComponent, Position):
            # Append the rect in the quadtree for handling collisions later
            position = self.component_manager.get(entity, Position)
            collision_component = self.component_manager.get(entity, CollisionComponent)
            rect = pygame.Rect(*(position.vec + collision_component.offset), *collision_component.size)
            quadtree.insert(entity, rect)

        # Handle collisions
        for non_solid_component_entity in self.component_manager.get_entities_with(CollisionComponent):
            non_solid_component = self.component_manager.get(non_solid_component_entity, CollisionComponent)
            if non_solid_component.solid:
                continue

            pos = self.component_manager.get(non_solid_component_entity, Position)
            vel = self.component_manager.get(non_solid_component_entity, Velocity)
            rect = pygame.FRect(*(pos.vec + non_solid_component.offset), *non_solid_component.size)

            vel.realistic_vel = vel.vec.copy()

            rect.x += vel.x * dt

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
                    elif vel.x < 0:
                        rect.left = colliding_rect.right
                    else:
                        vel.realistic_vel.x = 0 # the vel of the entity is not the same as the of the desired vel

            rect.y += vel.y * dt

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
                    elif vel.y < 0:
                        rect.top = colliding_rect.bottom
                    else:
                        vel.realistic_vel.y = 0 # the vel of the entity is not the same as the of the desired vel
            
            pos.vec.update(pygame.Vector2(rect.topleft) - non_solid_component.offset)
