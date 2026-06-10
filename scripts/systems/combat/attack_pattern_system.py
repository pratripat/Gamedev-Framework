import pygame
from scripts.components.combat import AttackPatternComponent
from scripts.components.physics import Position
from scripts.utils import CollisionLayer

class AttackPatternSystem:
    def __init__(self, component_manager, entity_manager, resource_manager):
        self.component_manager = component_manager
        self.entity_manager = entity_manager
        self.resource_manager = resource_manager

    def update(self, dt):
        for eid in self.component_manager.get_entities_with(AttackPatternComponent):
            apc = self.component_manager.get(eid, AttackPatternComponent)
            if apc.disabled or not apc.active:
                continue

            pattern = apc.current
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

        pattern.shoot_fn(eid, self.component_manager, self.entity_manager, self.resource_manager, data)