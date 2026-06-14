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

    def update(self, dt, fps, quadtree, hurtbox_dict, pos_dict, col_dict, particle_system=None, is_dashing=False, player_id=None):
        movement_scale = fps if (fps and fps > 0) else 60.0
        alive_indices = []

        for idx in self.active_indices:
            p = self.projectiles[idx]
            
            p.lifetime -= dt
            if p.lifetime <= 0:
                p.active = False
                self.free_indices.append(idx)
                continue

            hit_entity = False
            for target_eid, hurtbox in hurtbox_dict.items():
                if target_eid in p.hits or target_eid == p.source_entity or hurtbox.disabled:
                    continue
                if not (p.mask & hurtbox.layer):
                    continue
                
                # Check for dashing dodge
                if target_eid == player_id and is_dashing and not p.hits_dashing_player:
                    continue
                    
                target_pos_comp = pos_dict.get(target_eid)
                if not target_pos_comp:
                    continue
                target_pos = target_pos_comp.vec
                
                # Check collision
                p_rect = pygame.Rect(p.x - p.size/2, p.y - p.size/2, p.size, p.size)
                h_rect = pygame.Rect(*(target_pos + hurtbox.offset), *hurtbox.size)
                
                # simple rect-rect for now, or circle-rect
                from ...utils import circle_rect_collision
                class MockHitbox: pass
                mh = MockHitbox()
                mh.size = (p.size, p.size)
                if circle_rect_collision(mh, p_rect, h_rect):
                    p.hits.add(target_eid)
                    self.event_manager.emit(GameSceneEvents.DAMAGE, entity_id=target_eid, proj_id=idx, damage=p.damage, effects=p.effects)
                    if p.penetration > 0:
                        p.penetration -= 1
                    else:
                        p.active = False
                        self.free_indices.append(idx)
                        hit_entity = True
                        break
            
            if hit_entity:
                continue

            # Emit particles
            if particle_system and p.particle_rate > 0:
                p.particle_timer += dt
                emit_count = int(p.particle_timer * p.particle_rate)
                if emit_count > 0:
                    p.particle_timer -= emit_count / p.particle_rate
                    # Emit directly to particle system
                    for _ in range(emit_count):
                        particle_system.emit_fast_particle(
                            x=p.x, y=p.y,
                            vx=0, vy=0,
                            lifetime=0.5,
                            r=p.pulse_color[0], g=p.pulse_color[1], b=p.pulse_color[2], a=255,
                            size=p.size * 0.2,
                            fade=True, shrink=True, friction=1.0
                        )

            # Update pulses
            p.pulse_time += dt

            # Move horizontally
            p.x += p.vx * dt * movement_scale
            self._temp_rect.x = p.x - p.size/2
            self._temp_rect.y = p.y - p.size/2
            self._temp_rect.width = p.size
            self._temp_rect.height = p.size
            
            hits_h = []
            if quadtree:
                quadtree.retrieve(hits_h, self._temp_rect)
            
            destroyed = False
            seen_h = set()
            for other_entity, other_rect in hits_h:
                if other_entity in seen_h: continue
                seen_h.add(other_entity)
                
                if other_entity == p.source_entity:
                    continue
                other_comp = col_dict.get(other_entity)
                if not other_comp: continue

                if not getattr(other_comp, "blocks_projectiles", True):
                    if self._temp_rect.colliderect(other_rect):
                        self.event_manager.emit(GameSceneEvents.WATER_SPLASH, pos=pygame.Vector2(p.x, p.y), vel=pygame.Vector2(p.vx, p.vy), size=p.size)
                    continue

                if other_comp.solid and self._temp_rect.colliderect(other_rect):
                    self.event_manager.emit(GameSceneEvents.PROJECTILE_COLLISION, pos=pygame.Vector2(p.x, p.y), vel=pygame.Vector2(p.vx, p.vy), target_type="environment", size=p.size)
                    if p.bounce > 0:
                        p.bounce -= 1
                        p.vx *= -1
                        p.x += p.vx * dt * movement_scale # bounce back a bit
                    else:
                        p.active = False
                        self.free_indices.append(idx)
                        destroyed = True
                        break
            
            if destroyed:
                continue

            # Move vertically
            p.y += p.vy * dt * movement_scale
            self._temp_rect.y = p.y - p.size/2
            
            hits_v = []
            if quadtree:
                quadtree.retrieve(hits_v, self._temp_rect)
            
            seen_v = set()
            for other_entity, other_rect in hits_v:
                if other_entity in seen_v: continue
                seen_v.add(other_entity)
                
                if other_entity == p.source_entity:
                    continue
                other_comp = col_dict.get(other_entity)
                if not other_comp: continue

                if not getattr(other_comp, "blocks_projectiles", True):
                    if self._temp_rect.colliderect(other_rect):
                        self.event_manager.emit(GameSceneEvents.WATER_SPLASH, pos=pygame.Vector2(p.x, p.y), vel=pygame.Vector2(p.vx, p.vy), size=p.size)
                    continue

                if other_comp.solid and self._temp_rect.colliderect(other_rect):
                    self.event_manager.emit(GameSceneEvents.PROJECTILE_COLLISION, pos=pygame.Vector2(p.x, p.y), vel=pygame.Vector2(p.vx, p.vy), target_type="environment", size=p.size)
                    if p.bounce > 0:
                        p.bounce -= 1
                        p.vy *= -1
                        p.y += p.vy * dt * movement_scale # bounce back a bit
                    else:
                        p.active = False
                        self.free_indices.append(idx)
                        destroyed = True
                        break

            if not destroyed:
                alive_indices.append(idx)
        
        self.active_indices = alive_indices

    def collect_render_items(self, camera):
        scroll_int_x = camera.scroll_int.x
        scroll_int_y = camera.scroll_int.y
        items = []
        for idx in self.active_indices:
            p = self.projectiles[idx]
            
            px = p.x - scroll_int_x
            py = p.y - scroll_int_y
            
            # Pulse
            if p.pulse_radius > 0:
                pulse_val = (math.sin(p.pulse_time * p.pulse_speed) + 1) / 2
                dynamic_radius = p.pulse_radius * (0.8 + 0.4 * pulse_val)
                pulse_surf = pygame.Surface((dynamic_radius * 2, dynamic_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(pulse_surf, (*p.pulse_color, 255), (dynamic_radius, dynamic_radius), dynamic_radius)
                items.append((p.y, "sprite", pulse_surf, (px - dynamic_radius, py - dynamic_radius), None, None))
                
            # Main sprite
            if p.image:
                w, h = p.image.get_size()
                items.append((p.y, "sprite", p.image, (px - w/2, py - h/2), None, None))
                
        return items
