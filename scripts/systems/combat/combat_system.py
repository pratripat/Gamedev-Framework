from scripts.systems.combat.attack_pattern_system import AttackPatternSystem
from .weapon_system import WeaponSystem
from .hitbox_system import HitBoxSystem
from .health_system import HealthSystem
from .projectile_system import ProjectileSystem

class CombatSystem:
    def __init__(self, component_manager, entity_manager, camera, event_manager, resource_manager):
        self.weapon_system = WeaponSystem(component_manager, entity_manager, camera, event_manager, resource_manager)
        self.hitbox_system = HitBoxSystem()
        self.health_system = HealthSystem()
        self.projectile_system = ProjectileSystem(component_manager, event_manager)
        self.attack_pattern_system = AttackPatternSystem(component_manager, entity_manager, resource_manager)

    def update(self, event_manager, component_manager, entity_list, scroll, dt, fps=None):
        self.weapon_system.update(dt)
        self.attack_pattern_system.update(dt)
        # Update projectiles first so their positions are ready when hitboxes are checked
        self.projectile_system.update(dt, fps)
        self.hitbox_system.update(event_manager, component_manager, entity_list, scroll)
        self.health_system.update(component_manager, dt)