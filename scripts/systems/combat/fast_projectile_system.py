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
        'hits', 'source_entity', 'hits_dashing_player'
    ]
    def __init__(self):
        self.active = False
        self.hits = set()
        self.effects = []
        self.hits_dashing_player = False

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
        
    def spawn(self, source_entity, x, y, vx, vy, speed, damage, effects, bounce, penetration, lifetime, size, layer, mask, image, pulse_radius, pulse_speed, pulse_color, particle_rate, hits_dashing_player=False):
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
        
        self.active_indices.append(idx)
        return p

    def update(self, dt, fps, static_quadtree, dynamic_quadtree, hurtbox_dict, pos_dict, col_dict, particle_system=None, is_dashing=False, player_id=None, camera_center=None):
        movement_scale = fps if (fps and fps > 0) else 60.0
        alive_indices = []

        active_hurtboxes = []
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

        for idx in self.active_indices:
            p = self.projectiles[idx]
            
            if camera_center:
                dx = p.x - camera_center.x
                dy = p.y - camera_center.y
                if dx*dx + dy*dy > 2250000: # 1500px radius
                    p.active = False
                    self.free_indices.append(idx)
                    continue

            p.lifetime -= dt
            if p.lifetime <= 0:
                p.active = False
                self.free_indices.append(idx)
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

            # Move horizontally with sub-frame steps to prevent phasing
            old_x = p.x
            p.x += p.vx * dt * movement_scale
            
            # Use two check points for fast bullets: mid and end
            checks = [(old_x + (p.x - old_x) * 0.5, py), (p.x, py)]
            
            destroyed = False
            for cx, cy in checks:
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
                            p.active = False; self.free_indices.append(idx); destroyed = True; break
                if destroyed: break
            
            if destroyed: continue

            # Move vertically with sub-frame steps
            old_y = p.y
            p.y += p.vy * dt * movement_scale
            checks = [(p.x, old_y + (p.y - old_y) * 0.5), (p.x, p.y)]
            
            for cx, cy in checks:
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
                            p.active = False; self.free_indices.append(idx); destroyed = True; break
                if destroyed: break

            if not destroyed:
                alive_indices.append(idx)
        
        self.active_indices = alive_indices

    def collect_render_items(self, camera):
        scroll_int_x, scroll_int_y = camera.scroll_int.x, camera.scroll_int.y
        items = []; screen_rect = camera.rect
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
