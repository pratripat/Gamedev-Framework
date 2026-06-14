from scripts.systems.combat.attack_pattern_system import AttackPatternSystem
from .weapon_system import WeaponSystem
from .hitbox_system import HitBoxSystem
from .health_system import HealthSystem
from .fast_projectile_system import FastProjectileSystem

from ...components.combat import HurtBoxComponent, HitBoxComponent
from ...components.physics import Position, CollisionComponent

class CombatSystem:
    def __init__(self, component_manager, entity_manager, camera, event_manager, resource_manager):
        self.weapon_system = WeaponSystem(component_manager, entity_manager, camera, event_manager, resource_manager)
        self.hitbox_system = HitBoxSystem()
        self.health_system = HealthSystem()
        self.projectile_system = FastProjectileSystem(event_manager)
        self.attack_pattern_system = AttackPatternSystem(component_manager, entity_manager, resource_manager)

    def update(self, event_manager, component_manager, entity_list, scroll, dt, fps=None, quadtree=None, particle_system=None, is_dashing=False, player_id=None):
        self.weapon_system.update(dt, self.projectile_system)
        self.attack_pattern_system.update(dt, self.projectile_system)
        # Update projectiles first so their positions are ready when hitboxes are checked
        
        hurtbox_dict = component_manager._components.get(HurtBoxComponent, {})
        pos_dict = component_manager._components.get(Position, {})
        col_dict = component_manager._components.get(CollisionComponent, {})
        
        self.projectile_system.update(dt, fps, quadtree, hurtbox_dict, pos_dict, col_dict, particle_system, is_dashing, player_id)
        self.hitbox_system.update(event_manager, component_manager, entity_list, scroll)
        self.health_system.update(component_manager, dt)