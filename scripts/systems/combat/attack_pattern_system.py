import pygame
from ...components.combat import AttackPatternComponent
from ...components.physics import Position
from ...utils import CollisionLayer

class AttackPatternSystem:
    def __init__(self, component_manager, entity_manager, resource_manager):
        self.component_manager = component_manager
        self.entity_manager = entity_manager
        self.resource_manager = resource_manager

    def update(self, dt, projectile_system=None):
        self.projectile_system = projectile_system
        for eid in self.component_manager.get_entities_with(AttackPatternComponent):
            apc = self.component_manager.get(eid, AttackPatternComponent)
            if apc.disabled or not apc.active:
                continue

            pattern = apc.current

            # Warmup phase: telegraph before first shot
            if pattern.warmup > 0 and not pattern.warmed:
                pattern.shoot_timer += dt
                if pattern.shoot_timer >= pattern.warmup:
                    pattern.warmed = True
                    pattern.shoot_timer = 0
                continue  # skip firing during warmup

            pattern.shoot_timer += dt
            if pattern.duration is not None:
                pattern.phase_timer += dt

            # time to shoot within this pattern
            if pattern.shoot_timer >= pattern.cooldown:
                pattern.shoot_timer = 0
                self._fire(eid, pattern)

            # time to move to next pattern
            if pattern.duration is not None and pattern.phase_timer >= pattern.duration:
                pattern.phase_timer = 0
                pattern.shoot_timer = 0
                apc.advance()

    def _fire(self, eid, pattern):
        pos = self.component_manager.get(eid, Position)
        if not pos:
            return

        data = pattern.projectile_data.copy()
        data["start_pos"] = pos.vec.copy()
        data["layer"] = CollisionLayer.ENEMY
        data["mask"] = CollisionLayer.create_mask(CollisionLayer.PLAYER)

        if data.get("towards_player"):
            player_pos = self.component_manager.get(self.entity_manager.player_id, Position)
            data["target_pos"] = player_pos.vec.copy() if player_pos else pos.vec + pygame.Vector2(1, 0)
        else:
            data["target_pos"] = pos.vec + pygame.Vector2(1, 0)

        # Inject player entity ID for homing modifiers
        mods = data.get("modifiers")
        if mods and mods.get("homing_strength", 0) > 0:
            mods["homing_target_id"] = self.entity_manager.player_id

        pattern.shoot_fn(eid, self.component_manager, self.entity_manager, self.resource_manager, data, getattr(self, "projectile_system", None))