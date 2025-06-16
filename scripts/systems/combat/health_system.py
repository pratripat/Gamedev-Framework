from ...components.combat import HealthComponent

class HealthSystem:
    def update(self, component_manager, fps, dt):
        for entity_id in component_manager.get_entities_with(HealthComponent):
            health_component = component_manager.get(entity_id, HealthComponent)
            if not health_component:
                continue
            
            # update the health component
            if health_component.invincibility_timer > 0:
                health_component.invincibility_timer -= dt / fps
                if health_component.invincibility_timer < 0:
                    health_component.invincibility_timer = 0