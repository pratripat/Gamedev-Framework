from .ecs.component_manager import Position, Velocity

class PhysicsEngine:
    def __init__(self, component_manager):
        self.component_manager = component_manager

    def update(self, dt):
        # Update all entities with Position and Velocity components
        for entity in self.component_manager.get_entities_with(Position, Velocity):
            position = self.component_manager.get(entity, Position)
            velocity = self.component_manager.get(entity, Velocity)

            # Update position based on velocity
            position.x += velocity.x * dt
            position.y += velocity.y * dt