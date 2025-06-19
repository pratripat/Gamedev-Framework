from ...components.projectile import ProjectileComponent
from ...components.physics import Velocity
from ...utils import GameSceneEvents

class ProjectileSystem:
    def __init__(self, component_manager, event_manager):
        self.component_manager = component_manager
        event_manager.subscribe(GameSceneEvents.COLLISION, self._handle_projectile_collision)
        event_manager.subscribe(GameSceneEvents.DAMAGE, self._handle_penetration)
    
    def _handle_projectile_collision(self, entity_id, collisions):
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

    def update(self, fps, dt):
        for entity_id in self.component_manager.get_entities_with(ProjectileComponent):
            projectile = self.component_manager.get(entity_id, ProjectileComponent)

            projectile.lifetime -= dt / fps
            if projectile.lifetime <= 0:
                self.component_manager.remove_all(entity_id)
            