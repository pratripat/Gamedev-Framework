import pygame
import math

from ...components.particle import ParticleEmitter
from ...components.physics import Position

class FastParticle:
    __slots__ = [
        'active', 'x', 'y', 'vx', 'vy', 'age', 'lifetime', 
        'r', 'g', 'b', 'a', 'size', 'fade', 
        'flicker_colors', 'flicker_speed', 'oscillate_size', 
        'friction', 'shrink', 'image',
        'sway', 'gravity', 'wind_factor'
    ]
    def __init__(self):
        self.active = False
        self.image = None
        self.sway = False
        self.gravity = 0.0
        self.wind_factor = 0.0

class ParticleEffectSystem:
    def __init__(self, component_manager, entity_manager, capacity=4000):
        self.cm = component_manager
        self.capacity = capacity
        self.particles = [FastParticle() for _ in range(capacity)]
        self.active_indices = []
        self.free_indices = list(range(capacity))
        self._temp_rect = pygame.Rect(0, 0, 0, 0)
        self._temp_hits = []
        self._particle_cache = {}
        self.wind_system = None
        
    def emit_particle(self):
        if not self.free_indices:
            return None
        idx = self.free_indices.pop()
        p = self.particles[idx]
        p.active = True
        self.active_indices.append(idx)
        return p

    def emit_fast_particle(self, x, y, vx, vy, lifetime, r, g, b, a, size, fade, shrink, friction, sway=False, gravity=0.0, wind_factor=0.0):
        p = self.emit_particle()
        if p:
            p.x = x
            p.y = y
            p.vx = vx
            p.vy = vy
            p.lifetime = lifetime
            p.age = 0
            p.r = r
            p.g = g
            p.b = b
            p.a = a
            p.size = size
            p.fade = fade
            p.shrink = shrink
            p.friction = friction
            p.flicker_colors = None
            p.oscillate_size = False
            p.image = None
            p.sway = sway
            p.gravity = gravity
            p.wind_factor = wind_factor
            
    def update(self, dt, quadtree=None, camera_rect=None):
        # Emit particles
        for eid in self.cm.get_entities_with(ParticleEmitter, Position):
            emitter = self.cm.get(eid, ParticleEmitter)
            pos = self.cm.get(eid, Position).vec
            
            # Culling: Only emit if emitter is near screen
            if camera_rect:
                if not camera_rect.inflate(400, 400).collidepoint(pos.x, pos.y):
                    continue

            if not emitter.active:
                continue

            emitter.elapsed += dt
            emitter.time_since_emit += dt

            if emitter.elapsed > emitter.duration:
                if emitter.loop:
                    emitter.elapsed = 0
                else:
                    emitter.active = False
                    self.cm.remove_all(eid)
                    continue

            particles_to_emit = int(emitter.time_since_emit * emitter.rate)
            if particles_to_emit > 0:
                emitter.time_since_emit -= particles_to_emit / emitter.rate

                for _ in range(min(particles_to_emit, emitter.max_particles)):
                    emitter.emit(self, pos)

        # Update particle movement & lifetime
        alive_indices = []
        for idx in self.active_indices:
            p = self.particles[idx]
            
            # Culling: Only update if particle is near screen
            if camera_rect:
                if not camera_rect.inflate(300, 300).collidepoint(p.x, p.y):
                    # Still keep it alive but don't move it for this frame
                    # (Wait, if we don't update age, it lives forever offscreen. 
                    # If we don't update pos, it stays still. 
                    # Better: If it's too far, just kill it or update age only.)
                    p.age += dt
                    if p.age >= p.lifetime:
                        p.active = False
                        self.free_indices.append(idx)
                        continue
                    alive_indices.append(idx)
                    continue

            p.age += dt
            if p.age >= p.lifetime:
                p.active = False
                self.free_indices.append(idx)
                continue

            # Friction
            if p.friction < 1.0:
                p.vx *= (p.friction ** (dt * 60.0))
                p.vy *= (p.friction ** (dt * 60.0))

            # Environmental Physics (Leaves, Dust, etc)
            # 1. Gravity (Downwards)
            if p.gravity != 0:
                p.vy += p.gravity * dt

            # 2. Wind & Sway
            # Dynamic Wind: directly affect VX based on wind magnitude change
            if p.wind_factor != 0 and self.wind_system:
                # We apply wind as a force directly to VX
                p.vx += self.wind_system.magnitude_x * p.wind_factor * dt
            
            current_vx = p.vx
            if p.sway:
                # Horizontal sine-wave sway (added only to temporary render pos to preserve base VX)
                current_vx += math.sin(p.age * 5.0) * 15.0

            # Move with collision if quadtree available
            new_x = p.x + current_vx * dt
            if quadtree:
                self._temp_rect.x = int(new_x - p.size)
                self._temp_rect.y = int(p.y - p.size)
                self._temp_rect.width = int(p.size*2)
                self._temp_rect.height = int(p.size*2)
                self._temp_hits.clear()
                quadtree.retrieve(self._temp_hits, self._temp_rect)
                collided_h = False
                for _, tr in self._temp_hits:
                    if self._temp_rect.colliderect(tr):
                        p.vx *= -0.5 # Bounce and lose energy
                        collided_h = True
                        break
                if not collided_h: p.x = new_x
            else:
                p.x = new_x

            new_y = p.y + p.vy * dt
            if quadtree:
                self._temp_rect.x = int(p.x - p.size)
                self._temp_rect.y = int(new_y - p.size)
                self._temp_hits.clear()
                quadtree.retrieve(self._temp_hits, self._temp_rect)
                collided_v = False
                for _, tr in self._temp_hits:
                    if self._temp_rect.colliderect(tr):
                        p.vy *= -0.5 # Bounce and lose energy
                        collided_v = True
                        break
                if not collided_v: p.y = new_y
            else:
                p.y = new_y

            if p.fade:
                alpha = 255 * (1 - p.age / p.lifetime)
                p.a = max(0, int(alpha))

            # Handle color flickering
            if p.flicker_colors:
                f_idx = int(p.age * p.flicker_speed) % len(p.flicker_colors)
                new_color = p.flicker_colors[f_idx]
                p.r, p.g, p.b = new_color[0], new_color[1], new_color[2]
                if p.fade:
                    p.a = max(0, int(255 * (1 - p.age / p.lifetime)))
            
            alive_indices.append(idx)
            
        self.active_indices = alive_indices

    def collect_render_items(self, camera):
        scroll_int_x = camera.scroll_int.x
        scroll_int_y = camera.scroll_int.y
        items = []
        screen_rect = camera.rect
        
        for idx in self.active_indices:
            p = self.particles[idx]
            
            # PERFORMANCE: Strict visibility culling for particles
            if not screen_rect.inflate(64, 64).collidepoint(p.x, p.y):
                continue
            
            size = p.size
            if p.shrink:
                size *= max(0.0, 1.0 - (p.age / p.lifetime))
            elif p.oscillate_size:
                size *= (0.8 + 0.4 * abs(math.sin(p.age * 15.0)))
            
            if size > 0:
                isize = int(size)
                if p.image:
                    cache_key = (id(p.image), p.a, isize)
                    p_surf = self._particle_cache.get(cache_key)
                    if p_surf is None:
                        p_surf = p.image.copy()
                        if p.a < 255:
                            p_surf.set_alpha(p.a)
                        target_w = isize * 2
                        target_h = isize * 2
                        if p_surf.get_width() != target_w or p_surf.get_height() != target_h:
                            p_surf = pygame.transform.scale(p_surf, (target_w, target_h))
                        self._particle_cache[cache_key] = p_surf
                else:
                    cache_key = (p.r, p.g, p.b, p.a, isize)
                    p_surf = self._particle_cache.get(cache_key)
                    if p_surf is None:
                        p_surf = pygame.Surface((isize * 2, isize * 2), pygame.SRCALPHA)
                        pygame.draw.circle(p_surf, (p.r, p.g, p.b, p.a), (isize, isize), isize)
                        self._particle_cache[cache_key] = p_surf

                x = math.floor(p.x) - scroll_int_x - size
                y = math.floor(p.y) - scroll_int_y - size
                
                # Performance/Visual: Leaf particles should render ON TOP of trees
                # We add an offset to the sort_y for sway/gravity particles
                sort_y = p.y + 100 if (p.sway or p.gravity > 0) else p.y
                
                # Yield identical signature for ysort_queue to maintain strict visual parity
                items.append((sort_y, "sprite", p_surf, (x, y), None, None))
                
        return items
