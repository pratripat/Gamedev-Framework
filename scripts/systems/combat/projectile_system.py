from ...components.projectile import ProjectileComponent

class ProjectileSystem:
    def update(self, component_manager, fps, dt):
        for entity_id in component_manager.get_entities_with(ProjectileComponent):
            projectile = component_manager.get(entity_id, ProjectileComponent)

            projectile.lifetime -= dt / fps
            if projectile.lifetime <= 0:
                component_manager.remove_all(entity_id)
            