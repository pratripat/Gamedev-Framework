import pygame
from ..utils import TILE_SIZE
from ..components.physics import Position, Velocity, CollisionComponent


class RespawnManager:
    """Manages death state, respawn flow, and water-drowning rescue logic.

    GameScene owns the actual respawn orchestration (creating new systems);
    this class handles the per-frame death gate, water detection helpers,
    and the water-drowning rescue raycast/spiral-search logic.
    """

    def __init__(self, level, component_manager, render_system):
        self.level = level
        self.component_manager = component_manager
        self.render_system = render_system

        self.player = None
        self.player_input_system = None

        self.is_dead = False
        self._respawn_key_held = False

    def set_player(self, player, player_input_system):
        self.player = player
        self.player_input_system = player_input_system

    # ------------------------------------------------------------------
    # Death gate
    # ------------------------------------------------------------------

    def update_death_gate(self, dt, on_respawn_callback):
        """Call at the top of update(). Returns True if update should be skipped."""
        if not self.is_dead:
            return False
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r] and not self._respawn_key_held:
            self._respawn_key_held = True
            on_respawn_callback()
        elif not keys[pygame.K_r]:
            self._respawn_key_held = False
        return True

    def reset(self):
        self.is_dead = False
        self._respawn_key_held = False

    # ------------------------------------------------------------------
    # Water helpers
    # ------------------------------------------------------------------

    def is_pos_in_water(self, pos):
        if not self.level or not self.level.tilemap:
            return False
        water_layer = self.level.tilemap.layers.get("water")
        if not water_layer:
            return False
        chunk_pos = (
            int(pos[0] // (self.level.tilemap.CHUNK_SIZE * TILE_SIZE)) * (self.level.tilemap.CHUNK_SIZE * TILE_SIZE),
            int(pos[1] // (self.level.tilemap.CHUNK_SIZE * TILE_SIZE)) * (self.level.tilemap.CHUNK_SIZE * TILE_SIZE)
        )
        chunk = water_layer.get(chunk_pos)
        if chunk:
            for tdata in chunk.values():
                if tdata["rect"].collidepoint(pos[0], pos[1]):
                    return True
        return False

    def any_pos_in_water(self, points):
        if not self.level or not self.level.tilemap:
            return False
        water_layer = self.level.tilemap.layers.get("water")
        if not water_layer:
            return False
        seen_chunks = {}
        for pos in points:
            cx = int(pos[0] // (self.level.tilemap.CHUNK_SIZE * TILE_SIZE)) * (self.level.tilemap.CHUNK_SIZE * TILE_SIZE)
            cy = int(pos[1] // (self.level.tilemap.CHUNK_SIZE * TILE_SIZE)) * (self.level.tilemap.CHUNK_SIZE * TILE_SIZE)
            ck = (cx, cy)
            if ck not in seen_chunks:
                seen_chunks[ck] = water_layer.get(ck)
            chunk = seen_chunks[ck]
            if chunk:
                for tdata in chunk.values():
                    if tdata["rect"].collidepoint(pos[0], pos[1]):
                        return True
        return False

    def count_pos_in_water(self, points):
        if not self.level or not self.level.tilemap:
            return 0
        water_layer = self.level.tilemap.layers.get("water")
        if not water_layer:
            return 0
        count = 0
        seen_chunks = {}
        for pos in points:
            cx = int(pos[0] // (self.level.tilemap.CHUNK_SIZE * TILE_SIZE)) * (self.level.tilemap.CHUNK_SIZE * TILE_SIZE)
            cy = int(pos[1] // (self.level.tilemap.CHUNK_SIZE * TILE_SIZE)) * (self.level.tilemap.CHUNK_SIZE * TILE_SIZE)
            ck = (cx, cy)
            if ck not in seen_chunks:
                seen_chunks[ck] = water_layer.get(ck)
            chunk = seen_chunks[ck]
            if chunk:
                for tdata in chunk.values():
                    if tdata["rect"].collidepoint(pos[0], pos[1]):
                        count += 1
                        break
        return count

    def is_tile_walkable(self, x, y):
        if self.is_pos_in_water((x, y)):
            return False
        tilemap = self.level.tilemap
        chunk_x = int(x // (tilemap.CHUNK_SIZE * TILE_SIZE)) * (tilemap.CHUNK_SIZE * TILE_SIZE)
        chunk_y = int(y // (tilemap.CHUNK_SIZE * TILE_SIZE)) * (tilemap.CHUNK_SIZE * TILE_SIZE)
        chunk_pos = (chunk_x, chunk_y)
        for layer_id in ["grass", "path"]:
            layer = tilemap.layers.get(layer_id)
            if layer and chunk_pos in layer:
                for tpos, tdata in layer[chunk_pos].items():
                    if tdata["rect"].collidepoint(x, y):
                        return True
        return False

    # ------------------------------------------------------------------
    # Water drowning rescue
    # ------------------------------------------------------------------

    def handle_water_check(self, **kwargs):
        eid = kwargs.get('entity_id')
        pos = kwargs.get('pos')
        respawn_pos = kwargs.get('respawn_pos')
        if not pos:
            return

        p_col = self.component_manager.get(eid, CollisionComponent)
        is_touching_water = False

        if p_col:
            left = pos.x + p_col.offset.x
            top = pos.y + p_col.offset.y
            right = left + p_col.size.x
            bottom = top + p_col.size.y
            center_x = left + p_col.size.x / 2.0
            center_y = top + p_col.size.y / 2.0
            points = [
                (center_x, center_y),
                (left + 2, top + 2), (right - 2, top + 2),
                (left + 2, bottom - 2), (right - 2, bottom - 2)
            ]
            if self.any_pos_in_water(points):
                is_touching_water = True
        else:
            if self.is_pos_in_water(pos):
                is_touching_water = True

        if not is_touching_water:
            return

        if respawn_pos and p_col:
            self._raycast_rescue(eid, pos, respawn_pos, p_col)
            return

        self._spiral_rescue(eid, pos)

    def _raycast_rescue(self, eid, pos, respawn_pos, p_col):
        p_pos = self.component_manager.get(eid, Position)
        if not p_pos:
            return
        start_vec = pygame.Vector2(respawn_pos)
        curr_vec = pygame.Vector2(pos.x, pos.y)
        direction = start_vec - curr_vec

        if direction.length_squared() > 0:
            direction_norm = direction.normalize()
            dist = direction.length()
            step = 2.0
            safe_found = False
            test_vec = curr_vec.copy()
            for _ in range(int(dist / step) + 1):
                left = test_vec.x + p_col.offset.x
                top = test_vec.y + p_col.offset.y
                right = left + p_col.size.x
                bottom = top + p_col.size.y
                cx = left + p_col.size.x / 2.0
                cy = top + p_col.size.y / 2.0
                pts = [(cx, cy), (left + 2, top + 2), (right - 2, top + 2),
                       (left + 2, bottom - 2), (right - 2, bottom - 2)]
                if not self.any_pos_in_water(pts):
                    safe_found = True
                    break
                test_vec += direction_norm * step
            if safe_found:
                p_pos.vec.update(test_vec + direction_norm * 2.0)
            else:
                p_pos.vec.update(respawn_pos)
        else:
            p_pos.vec.update(respawn_pos)

        self.render_system.render_effect_system.trigger_flash(eid)
        p_vel = self.component_manager.get(eid, Velocity)
        if p_vel:
            p_vel.vec.update(0, 0)

    def _spiral_rescue(self, eid, pos):
        safe_pos = None
        found = False
        for radius in range(1, 10):
            for dx in range(-radius, radius + 1):
                for dy in [-radius, radius]:
                    if self.is_tile_walkable(pos.x + dx * 32, pos.y + dy * 32):
                        safe_pos = pygame.Vector2(pos.x + dx * 32, pos.y + dy * 32)
                        found = True
                        break
                if found:
                    break
                for dy in range(-radius + 1, radius):
                    for dx in [-radius, radius]:
                        if self.is_tile_walkable(pos.x + dx * 32, pos.y + dy * 32):
                            safe_pos = pygame.Vector2(pos.x + dx * 32, pos.y + dy * 32)
                            found = True
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                break

        if safe_pos:
            p_pos = self.component_manager.get(eid, Position)
            if p_pos:
                dist = pos.distance_to(safe_pos)
                if dist < 16:
                    p_pos.vec.update(safe_pos)
                else:
                    p_pos.vec.update(safe_pos)
                    self.render_system.render_effect_system.trigger_flash(eid)
                    p_vel = self.component_manager.get(eid, Velocity)
                    if p_vel:
                        p_vel.vec.update(0, 0)
