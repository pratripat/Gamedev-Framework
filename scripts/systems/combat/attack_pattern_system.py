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
            if apc.disabled:
                continue

            pattern = apc.current
            pattern.shoot_timer += dt
            pattern.phase_timer += dt

            # time to shoot within this pattern
            if pattern.shoot_timer >= pattern.cooldown:
                pattern.shoot_timer = 0
                self._fire(eid, pattern)

            # time to move to next pattern
            if pattern.phase_timer >= pattern.duration:
                pattern.phase_timer = 0
                pattern.shoot_timer = 0
                apc.advance()

    def _fire(self, eid, pattern):
        pos = self.component_manager.get(eid, Position).vec.copy()
        data = pattern.projectile_data.copy()

        target_pos = pygame.Vector2(1, 0) + pos
        if data.get("towards_player"):
            player_pos = self.component_manager.get(self.entity_manager.player_id, Position)
            if player_pos:
                target_pos = player_pos.vec.copy()

        data["start_pos"] = pos
        data["target_pos"] = target_pos
        data["layer"] = CollisionLayer.ENEMY
        data["mask"] = CollisionLayer.create_mask(CollisionLayer.PLAYER)

        pattern.shoot_fn(eid, self.component_manager, self.entity_manager, self.resource_manager, data)