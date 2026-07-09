import pygame, math
from ...components.combat import AttackPatternComponent
from ...components.physics import Position, Velocity
from ...components.ai import AIComponent
from ...utils import CollisionLayer

class AttackPatternSystem:
    def __init__(self, component_manager, entity_manager, resource_manager):
        self.component_manager = component_manager
        self.entity_manager = entity_manager
        self.resource_manager = resource_manager
        self._telegraph_surface = None
        self._telegraph_cache = {}
        self._telegraph_items = []

    def update(self, dt, projectile_system=None, game_time=0.0):
        self.projectile_system = projectile_system
        self._telegraph_items.clear()
        for eid in self.component_manager.get_entities_with(AttackPatternComponent):
            apc = self.component_manager.get(eid, AttackPatternComponent)
            if apc.disabled or not apc.active:
                continue

            pattern = apc.current

            # ---- Pattern selection on transition ----
            if pattern.shoot_timer == 0 and not pattern.warmed:
                pos = self.component_manager.get(eid, Position)
                player_pos = None
                if pos:
                    player_pos = self.component_manager.get(self.entity_manager.player_id, Position)
                dist = pos.vec.distance_to(player_pos.vec) if (pos and player_pos) else 0
                apc.select_pattern(dist, game_time)
                pattern = apc.current

            # Warmup phase — telegraph + optional dash
            if pattern.warmup > 0 and not pattern.warmed:
                pattern.shoot_timer += dt
                pos = self.component_manager.get(eid, Position)
                if pos:
                    progress = pattern.shoot_timer / pattern.warmup
                    player_pos = self.component_manager.get(self.entity_manager.player_id, Position)
                    if player_pos and pattern.projectile_data.get("towards_player"):
                        target = player_pos.vec
                        # Dash toward player during warmup if dash_speed is set
                        dash_speed = pattern.projectile_data.get("dash_speed") or 0
                        if dash_speed > 0:
                            vel = self.component_manager.get(eid, Velocity)
                            if vel:
                                dir_vec = (target - pos.vec).normalize()
                                vel.vec = dir_vec * dash_speed
                    else:
                        target = pos.vec + pygame.Vector2(1, 0)
                    self._telegraph_items.append((target.x, target.y, progress, pattern.tier, eid))
                if pattern.shoot_timer >= pattern.warmup:
                    # Stop dash after warmup ends
                    dash_speed = pattern.projectile_data.get("dash_speed") or 0
                    if dash_speed > 0:
                        vel = self.component_manager.get(eid, Velocity)
                        if vel:
                            vel.vec = (0, 0)
                    pattern.warmed = True
                    pattern.shoot_timer = 0
                continue

            pattern.shoot_timer += dt
            if pattern.duration is not None:
                pattern.phase_timer += dt

            if pattern.shoot_timer >= pattern.cooldown:
                pattern.shoot_timer = 0
                self._fire(eid, pattern)

            if pattern.duration is not None and pattern.phase_timer >= pattern.duration:
                pattern.phase_timer = 0
                pattern.shoot_timer = 0
                pattern.warmed = False

    def render_telegraphs(self, surface, camera):
        if not self._telegraph_items:
            return
        scroll = camera.scroll_int
        for tx, ty, progress, tier, eid in self._telegraph_items:
            sx = int(tx - scroll.x)
            sy = int(ty - scroll.y)
            # Tier-based sizing
            r = { "light": 12, "heavy": 20, "signature": 30 }.get(tier, 12)
            # Puling ring
            alpha = int(80 + 175 * abs(math.sin(progress * math.pi * 3)))
            color_map = { "light": (200, 200, 200), "heavy": (255, 180, 50), "signature": (255, 50, 50) }
            color = color_map.get(tier, (200, 200, 200))
            surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, alpha), (r, r), r, 2)
            # Inner crosshair grows with progress
            inner_r = int(r * progress)
            if inner_r > 2:
                pygame.draw.circle(surf, (*color, alpha//2), (r, r), inner_r, 1)
            # Signature tier gets an extra outer ring
            if tier == "signature":
                outer_r = r + 6
                pygame.draw.circle(surf, (255, 50, 50, alpha//3), (r, r), outer_r, 1)
            surface.blit(surf, (sx - r, sy - r))

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