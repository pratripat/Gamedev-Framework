import pygame
import math
from ...utils import GameSceneEvents# , Quadtree, INITIAL_WINDOW_SIZE, SCALE, CollisionShape, collision_occured

class FastProjectile:
    __slots__ = [
        'active', 'x', 'y', 'vx', 'vy', 'speed', 
        'damage', 'effects', 'bounce', 'penetration', 'lifetime',
        'size', 'layer', 'mask', 'image', 'color',
        'pulse_radius', 'pulse_speed', 'pulse_color', 'pulse_time',
        'particle_rate', 'particle_timer',
        'hits', 'source_entity', 'hits_dashing_player',
        # --- projectile modifiers ---
        'accel', 'max_speed', 'turn_rate',
        'homing_strength', 'homing_target_id',
        'wave_amplitude', 'wave_frequency', 'wave_time',
        'trail_interval', 'trail_timer', 'trail_lifetime',
        'delay', 'delay_timer',
        'split_on_death', 'split_count', 'split_speed', 'split_angle_spread',
        'mine_radius', 'mine_delay', 'mine_timer',
        'orbit_radius', 'orbit_speed', 'orbit_angle', 'orbit_center_x', 'orbit_center_y',
        'phase', 'phase_timer',
        'curvature',
    ]
    def __init__(self):
        self.active = False
        self.hits = set()
        self.effects = []
        self.hits_dashing_player = False
        # defaults for modifiers
        self.accel = 0.0
        self.max_speed = 0.0
        self.turn_rate = 0.0
        self.homing_strength = 0.0
        self.homing_target_id = None
        self.wave_amplitude = 0.0
        self.wave_frequency = 0.0
        self.wave_time = 0.0
        self.trail_interval = 0.0
        self.trail_timer = 0.0
        self.trail_lifetime = 0.0
        self.delay = 0.0
        self.delay_timer = 0.0
        self.split_on_death = False
        self.split_count = 0
        self.split_speed = 0.0
        self.split_angle_spread = 0.0
        self.mine_radius = 0.0
        self.mine_delay = 0.0
        self.mine_timer = 0.0
        self.orbit_radius = 0.0
        self.orbit_speed = 0.0
        self.orbit_angle = 0.0
        self.orbit_center_x = 0.0
        self.orbit_center_y = 0.0
        self.phase = 0
        self.phase_timer = 0.0
        self.curvature = 0.0

class FastProjectileSystem:
    def __init__(self, event_manager, capacity=4000):
        self.event_manager = event_manager
        self.capacity = capacity
        self.projectiles = [FastProjectile() for _ in range(capacity)]
        self.active_indices = []
        self.free_indices = list(range(capacity))
        self._temp_rect = pygame.FRect(0, 0, 0, 0)
        self._pulse_cache = {}
        
        # Pre-allocated objects to eliminate per-frame garbage collection
        self._shared_hits = []
        self._shared_seen = set()
        self._shared_vec = pygame.Vector2(0, 0)
        self._shared_vel = pygame.Vector2(0, 0)
        self._active_hurtboxes = []
        self._render_items = []
        
    def spawn(self, source_entity, x, y, vx, vy, speed, damage, effects, bounce, penetration, lifetime, size, layer, mask, image, pulse_radius, pulse_speed, pulse_color, particle_rate, hits_dashing_player=False, modifiers=None):
        if not self.free_indices:
            return None
        idx = self.free_indices.pop()
        p = self.projectiles[idx]
        
        p.active = True
        p.source_entity = source_entity
        p.x = x
        p.y = y
        p.vx = vx
        p.vy = vy
        p.speed = speed
        p.damage = damage
        p.effects = effects
        p.bounce = bounce
        p.penetration = penetration
        p.lifetime = lifetime
        p.size = size
        p.layer = layer
        p.mask = mask
        p.image = image
        p.pulse_radius = pulse_radius
        p.pulse_speed = pulse_speed
        p.pulse_color = pulse_color
        p.pulse_time = 0.0
        p.particle_rate = particle_rate
        p.particle_timer = 0.0
        p.hits.clear()
        p.hits_dashing_player = hits_dashing_player

        # apply modifiers
        p.accel = 0.0
        p.max_speed = 0.0
        p.turn_rate = 0.0
        p.homing_strength = 0.0
        p.homing_target_id = None
        p.wave_amplitude = 0.0
        p.wave_frequency = 0.0
        p.wave_time = 0.0
        p.trail_interval = 0.0
        p.trail_timer = 0.0
        p.trail_lifetime = 0.0
        p.delay = 0.0
        p.delay_timer = 0.0
        p.split_on_death = False
        p.split_count = 0
        p.split_speed = 0.0
        p.split_angle_spread = 0.0
        p.mine_radius = 0.0
        p.mine_delay = 0.0
        p.mine_timer = 0.0
        p.orbit_radius = 0.0
        p.orbit_speed = 0.0
        p.orbit_angle = 0.0
        p.orbit_center_x = 0.0
        p.orbit_center_y = 0.0
        p.phase = 0
        p.phase_timer = 0.0
        p.curvature = 0.0
        if modifiers:
            for k, v in modifiers.items():
                if hasattr(p, k):
                    setattr(p, k, v)
        
        self.active_indices.append(idx)
        return p

    def _apply_modifiers(self, p, dt, movement_scale, pos_dict):
        # Delay: projectile waits before becoming active
        if p.delay > 0:
            p.delay -= dt
            if p.delay > 0:
                return 'delayed'

        # Orbit: projectile circles a center point
        if p.orbit_radius > 0:
            p.orbit_angle += p.orbit_speed * dt
            p.x = p.orbit_center_x + math.cos(p.orbit_angle) * p.orbit_radius
            p.y = p.orbit_center_y + math.sin(p.orbit_angle) * p.orbit_radius
            return 'orbiting'

        # Homing: steer toward target
        if p.homing_strength > 0 and p.homing_target_id is not None:
            target_pos = pos_dict.get(p.homing_target_id)
            if target_pos:
                dx = target_pos.vec.x - p.x
                dy = target_pos.vec.y - p.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 1.0:
                    desired_vx = dx / dist * p.speed
                    desired_vy = dy / dist * p.speed
                    p.vx += (desired_vx - p.vx) * p.homing_strength
                    p.vy += (desired_vy - p.vy) * p.homing_strength

        # Curvature: bend trajectory over time
        if p.curvature != 0.0:
            cur_speed = math.sqrt(p.vx*p.vx + p.vy*p.vy)
            if cur_speed > 0.1:
                perp_x = -p.vy / cur_speed
                perp_y = p.vx / cur_speed
                p.vx += perp_x * p.curvature * dt * movement_scale
                p.vy += perp_y * p.curvature * dt * movement_scale
                new_speed = math.sqrt(p.vx*p.vx + p.vy*p.vy)
                if new_speed > 0.0:
                    p.vx *= cur_speed / new_speed
                    p.vy *= cur_speed / new_speed

        # Acceleration: speed up or slow down over time
        if p.accel != 0.0:
            cur_speed = math.sqrt(p.vx*p.vx + p.vy*p.vy)
            if cur_speed > 0.0:
                factor = 1.0 + p.accel * dt * movement_scale
                if p.max_speed > 0.0 and cur_speed * factor > p.max_speed:
                    factor = p.max_speed / cur_speed
                p.vx *= factor
                p.vy *= factor

        return None

    def _post_move_modifiers(self, p, dt):
        # Wave: perpendicular sine oscillation
        if p.wave_amplitude > 0.0:
            cur_speed = math.sqrt(p.vx*p.vx + p.vy*p.vy)
            if cur_speed > 0.1:
                perp_x = -p.vy / cur_speed
                perp_y = p.vx / cur_speed
                p.wave_time += dt
                offset = math.sin(p.wave_time * p.wave_frequency) * p.wave_amplitude
                p.x += perp_x * offset * dt
                p.y += perp_y * offset * dt

    def _emit_trail(self, p, dt, particle_system):
        if p.trail_interval > 0.0 and particle_system:
            p.trail_timer += dt
            if p.trail_timer >= p.trail_interval:
                p.trail_timer -= p.trail_interval
                particle_system.emit_fast_particle(
                    p.x, p.y, 0, 0, p.trail_lifetime,
                    p.pulse_color[0], p.pulse_color[1], p.pulse_color[2], 150,
                    p.size * 0.3, True, True, 1.0
                )

    def _handle_split(self, p, dt):
        if p.split_on_death and p.split_count > 0:
            angle_step = 360.0 / p.split_count
            base_angle = math.atan2(p.vy, p.vx)
            for i in range(p.split_count):
                angle = base_angle + math.radians(i * angle_step - p.split_angle_spread / 2)
                split_vx = math.cos(angle) * p.split_speed
                split_vy = math.sin(angle) * p.split_speed
                child = self._spawn_raw(
                    p.source_entity, p.x, p.y, split_vx, split_vy, p.split_speed,
                    int(p.damage * 0.5), [], max(0, p.bounce - 1), max(0, p.penetration - 1),
                    p.lifetime * 0.5, p.size * 0.5, p.layer, p.mask, p.image,
                    0, 0, p.pulse_color, 0
                )
                if child is not None:
                    child.homing_strength = p.homing_strength * 0.5
                    child.homing_target_id = p.homing_target_id

    def _spawn_raw(self, source_entity, x, y, vx, vy, speed, damage, effects, bounce, penetration, lifetime, size, layer, mask, image, pulse_radius, pulse_speed, pulse_color, particle_rate, hits_dashing_player=False):
        """Minimal spawn for internal split/chain use without modifier overhead."""
        if not self.free_indices:
            return None
        idx = self.free_indices.pop()
        child = self.projectiles[idx]
        child.active = True
        child.source_entity = source_entity
        child.x = x; child.y = y
        child.vx = vx; child.vy = vy
        child.speed = speed
        child.damage = damage
        child.effects = effects if isinstance(effects, list) else []
        child.bounce = bounce
        child.penetration = penetration
        child.lifetime = lifetime
        child.size = size
        child.layer = layer
        child.mask = mask
        child.image = image
        child.pulse_radius = pulse_radius
        child.pulse_speed = pulse_speed
        child.pulse_color = pulse_color
        child.pulse_time = 0.0
        child.particle_rate = particle_rate
        child.particle_timer = 0.0
        child.hits.clear()
        child.hits_dashing_player = hits_dashing_player
        child.accel = 0.0; child.max_speed = 0.0; child.turn_rate = 0.0
        child.homing_strength = 0.0; child.homing_target_id = None
        child.wave_amplitude = 0.0; child.wave_frequency = 0.0; child.wave_time = 0.0
        child.trail_interval = 0.0; child.trail_timer = 0.0; child.trail_lifetime = 0.0
        child.delay = 0.0; child.delay_timer = 0.0
        child.split_on_death = False; child.split_count = 0
        child.split_speed = 0.0; child.split_angle_spread = 0.0
        child.mine_radius = 0.0; child.mine_delay = 0.0; child.mine_timer = 0.0
        child.orbit_radius = 0.0; child.orbit_speed = 0.0; child.orbit_angle = 0.0
        child.orbit_center_x = 0.0; child.orbit_center_y = 0.0
        child.phase = 0; child.phase_timer = 0.0; child.curvature = 0.0
        self.active_indices.append(idx)
        return child

    def update(self, dt, fps, static_quadtree, dynamic_quadtree, hurtbox_dict, pos_dict, col_dict, particle_system=None, is_dashing=False, player_id=None, camera_center=None):
        movement_scale = fps if (fps and fps > 0) else 60.0

        active_hurtboxes = self._active_hurtboxes
        active_hurtboxes.clear()
        for target_eid, hurtbox in hurtbox_dict.items():
            if hurtbox.disabled: continue
            target_pos_comp = pos_dict.get(target_eid)
            if not target_pos_comp: continue
            
            hx_min = target_pos_comp.vec.x + hurtbox.offset.x
            hy_min = target_pos_comp.vec.y + hurtbox.offset.y
            hx_max = hx_min + hurtbox.size[0]
            hy_max = hy_min + hurtbox.size[1]
            active_hurtboxes.append((target_eid, hurtbox.layer, hx_min, hy_min, hx_max, hy_max))

        hits_list = self._shared_hits
        seen_set = self._shared_seen
        emit_pos = self._shared_vec
        emit_vel = self._shared_vel

        write_ptr = 0
        for read_pos in range(len(self.active_indices)):
            idx = self.active_indices[read_pos]
            p = self.projectiles[idx]
            
            if camera_center:
                dx = p.x - camera_center.x
                dy = p.y - camera_center.y
                if dx*dx + dy*dy > 2250000:
                    p.active = False
                    self.free_indices.append(idx)
                    continue

            p.lifetime -= dt
            if p.lifetime <= 0:
                p.active = False
                self.free_indices.append(idx)
                self._handle_split(p, dt)
                continue

            # ---- MODIFIERS: Pre-movement ----
            mod_result = self._apply_modifiers(p, dt, movement_scale, pos_dict)
            if mod_result == 'delayed':
                self.active_indices[write_ptr] = idx
                write_ptr += 1
                continue
            if mod_result == 'orbiting':
                self.active_indices[write_ptr] = idx
                write_ptr += 1
                continue

            px, py = p.x, p.y
            pr = p.size / 2.0
            px_min, px_max = px - pr, px + pr
            py_min, py_max = py - pr, py + pr
            p_mask = p.mask

            hit_entity = False
            for target_eid, h_layer, hx_min, hy_min, hx_max, hy_max in active_hurtboxes:
                if target_eid in p.hits or target_eid == p.source_entity: continue
                if not (p_mask & h_layer): continue
                if target_eid == player_id and is_dashing and not p.hits_dashing_player: continue
                
                if px_max >= hx_min and px_min <= hx_max and py_max >= hy_min and py_min <= hy_max:
                    test_x = px
                    if px < hx_min: test_x = hx_min
                    elif px > hx_max: test_x = hx_max
                    test_y = py
                    if py < hy_min: test_y = hy_min
                    elif py > hy_max: test_y = hy_max
                    
                    if (px - test_x)**2 + (py - test_y)**2 <= pr**2:
                        p.hits.add(target_eid)
                        emit_pos.update(px, py)
                        emit_vel.update(p.vx, p.vy)
                        self.event_manager.emit(GameSceneEvents.DAMAGE, entity_id=target_eid, proj_id=idx, damage=p.damage, effects=p.effects, proj_vel=emit_vel, proj_pos=emit_pos)
                        if p.penetration > 0: p.penetration -= 1
                        else:
                            p.active = False
                            self.free_indices.append(idx)
                            hit_entity = True
                            self._handle_split(p, dt)
                            break
            
            if hit_entity: continue

            if particle_system and p.particle_rate > 0:
                p.particle_timer += dt
                emit_count = int(p.particle_timer * p.particle_rate)
                if emit_count > 0:
                    p.particle_timer -= emit_count / p.particle_rate
                    for _ in range(emit_count):
                        particle_system.emit_fast_particle(px, py, 0, 0, 0.5, p.pulse_color[0], p.pulse_color[1], p.pulse_color[2], 255, p.size * 0.2, True, True, 1.0)

            p.pulse_time += dt

            # ---- MODIFIERS: Trail ----
            self._emit_trail(p, dt, particle_system)

            old_x = p.x
            p.x += p.vx * dt * movement_scale
            
            destroyed = False
            cx_mid = old_x + (p.x - old_x) * 0.5
            for cx in (cx_mid, p.x):
                cy = py
                self._temp_rect.update(cx - pr, cy - pr, p.size, p.size)
                hits_list.clear()
                if static_quadtree: static_quadtree.retrieve(hits_list, self._temp_rect)
                if dynamic_quadtree: dynamic_quadtree.retrieve(hits_list, self._temp_rect)
                
                seen_set.clear()
                for other_entity, other_rect in hits_list:
                    if other_entity in seen_set or (other_entity is not None and other_entity == p.source_entity): continue
                    seen_set.add(other_entity)
                    
                    layer_id = other_entity[0] if isinstance(other_entity, tuple) else other_entity
                    is_water = (layer_id == "water")
                    is_solid = (layer_id == "wall")
                    if other_entity is not None and not (is_water or is_solid):
                        comp = col_dict.get(other_entity)
                        if comp: is_solid = comp.solid

                    if is_water and self._temp_rect.colliderect(other_rect):
                        emit_pos.update(cx, cy); emit_vel.update(p.vx, p.vy)
                        self.event_manager.emit(GameSceneEvents.WATER_SPLASH, pos=emit_pos, vel=emit_vel, size=p.size)
                        continue

                    if is_solid and self._temp_rect.colliderect(other_rect):
                        emit_pos.update(cx, cy); emit_vel.update(p.vx, p.vy)
                        self.event_manager.emit(GameSceneEvents.PROJECTILE_COLLISION, pos=emit_pos, vel=emit_vel, target_type="environment", size=p.size)
                        if p.bounce > 0:
                            p.bounce -= 1; p.vx *= -1; p.x = cx + p.vx * dt * movement_scale
                        else:
                            p.active = False; self.free_indices.append(idx); self._handle_split(p, dt); destroyed = True; break
                if destroyed: break
            
            if destroyed: continue

            old_y = p.y
            p.y += p.vy * dt * movement_scale
            cy_mid = old_y + (p.y - old_y) * 0.5
            for cy in (cy_mid, p.y):
                cx = p.x
                self._temp_rect.update(cx - pr, cy - pr, p.size, p.size)
                hits_list.clear()
                if static_quadtree: static_quadtree.retrieve(hits_list, self._temp_rect)
                if dynamic_quadtree: dynamic_quadtree.retrieve(hits_list, self._temp_rect)
                
                seen_set.clear()
                for other_entity, other_rect in hits_list:
                    if other_entity in seen_set or (other_entity is not None and other_entity == p.source_entity): continue
                    seen_set.add(other_entity)
                    
                    layer_id = other_entity[0] if isinstance(other_entity, tuple) else other_entity
                    is_water = (layer_id == "water")
                    is_solid = (layer_id == "wall")
                    if other_entity is not None and not (is_water or is_solid):
                        comp = col_dict.get(other_entity)
                        if comp: is_solid = comp.solid

                    if is_water and self._temp_rect.colliderect(other_rect):
                        emit_pos.update(cx, cy); emit_vel.update(p.vx, p.vy)
                        self.event_manager.emit(GameSceneEvents.WATER_SPLASH, pos=emit_pos, vel=emit_vel, size=p.size)
                        continue

                    if is_solid and self._temp_rect.colliderect(other_rect):
                        emit_pos.update(cx, cy); emit_vel.update(p.vx, p.vy)
                        self.event_manager.emit(GameSceneEvents.PROJECTILE_COLLISION, pos=emit_pos, vel=emit_vel, target_type="environment", size=p.size)
                        if p.bounce > 0:
                            p.bounce -= 1; p.vy *= -1; p.y = cy + p.vy * dt * movement_scale
                        else:
                            p.active = False; self.free_indices.append(idx); self._handle_split(p, dt); destroyed = True; break
                if destroyed: break
            if destroyed: continue

            # ---- MODIFIERS: Post-movement ----
            self._post_move_modifiers(p, dt)

            self.active_indices[write_ptr] = idx
            write_ptr += 1
        
        del self.active_indices[write_ptr:]

    def collect_render_items(self, camera):
        scroll_int_x, scroll_int_y = camera.scroll_int.x, camera.scroll_int.y
        items = self._render_items
        items.clear()
        screen_rect = camera.rect
        for idx in self.active_indices:
            p = self.projectiles[idx]
            if not screen_rect.inflate(64, 64).collidepoint(p.x, p.y): continue
            px, py = p.x - scroll_int_x, p.y - scroll_int_y
            if p.pulse_radius > 0:
                pulse_val = (math.sin(p.pulse_time * p.pulse_speed) + 1) / 2
                dr_int = int(p.pulse_radius * (0.8 + 0.4 * pulse_val))
                if dr_int > 0:
                    cache_key = (*p.pulse_color, dr_int)
                    pulse_surf = self._pulse_cache.get(cache_key)
                    if pulse_surf is None:
                        pulse_surf = pygame.Surface((dr_int * 2, dr_int * 2), pygame.SRCALPHA)
                        pygame.draw.circle(pulse_surf, (*p.pulse_color, 255), (dr_int, dr_int), dr_int)
                        self._pulse_cache[cache_key] = pulse_surf
                    items.append((p.y, "sprite", pulse_surf, (px - dr_int, py - dr_int), None, None))
            if p.image:
                w, h = p.image.get_size()
                items.append((p.y, "sprite", p.image, (px - w/2, py - h/2), None, None))
        return items
