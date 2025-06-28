from .weapon_system import WeaponSystem
from .hitbox_system import HitBoxSystem
from .health_system import HealthSystem
from .projectile_system import ProjectileSystem

class CombatSystem:
    def __init__(self, component_manager, entity_manager, camera, event_manager):
        self.weapon_system = WeaponSystem(component_manager, entity_manager, camera, event_manager)
        self.hitbox_system = HitBoxSystem()
        self.health_system = HealthSystem()
        self.projectile_system = ProjectileSystem(component_manager, event_manager)

    def update(self, event_manager, component_manager, entity_list, scroll, fps, dt):
        self.weapon_system.update(fps, dt)
        self.hitbox_system.update(event_manager, component_manager, entity_list, scroll)
        self.health_system.update(component_manager, fps, dt)

        self.projectile_system.update(fps, dt)