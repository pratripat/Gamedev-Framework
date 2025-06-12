from ..systems.weapon_system import WeaponSystem
from ..systems.hitbox_system import HitBoxSystem
from ..systems.health_system import HealthSystem

class CombatSystem:
    def __init__(self, physics_component_manager, entity_manager, camera, event_manager):
        self.weapon_system = WeaponSystem(physics_component_manager, entity_manager, camera, event_manager)
        self.hitbox_system = HitBoxSystem()
        self.health_system = HealthSystem()

    def update(self, event_manager, component_manager, entity_list, scroll, fps, dt):
        self.weapon_system.update(fps, dt)
        self.hitbox_system.update(event_manager, component_manager, entity_list, scroll)
        self.health_system.update(component_manager, fps, dt)