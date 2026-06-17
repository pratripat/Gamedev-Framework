import pygame

from ...components.particle import ParticleEmitter, Particle
from ...components.physics import Position, Velocity

class ParticlePool:
    def __init__(self, component_manager, entity_manager, capacity=100):
        self.pool = []
        self.cm = component_manager

        for _ in range(capacity):
            eid = entity_manager.create_entity()
            self.pool.append(eid)
            self.cm.add(eid, Particle(lifetime=0), Position(eid, 0, 0), Velocity(eid, 0, 0))
            self.deactivate(eid)

    def get(self) -> int:
        return self.pool.pop() if self.pool else None

    def release(self, eid: int):
        self.deactivate(eid)
        self.pool.append(eid)

    def deactivate(self, eid: int):
        particle = self.cm.get(eid, Particle)
        if particle:
            particle.age = float("inf")

class ParticleEffectSystem:
    def __init__(self, component_manager, entity_manager, capacity=100):
        self.cm = component_manager
        self.pool = ParticlePool(component_manager, entity_manager, capacity)

    def update(self, dt, tilemap=None, camera_rect=None):
        # build collision quadtree if tilemap provided
        quadtree = None
        if tilemap and camera_rect:
            from ...utils import Quadtree
            quadtree = Quadtree(0, camera_rect)
            # Only include solid tiles in current view
            ysort_tiles = tilemap.get_ysort_items(camera_rect)
            for ty, ttype, surf, pos in ysort_tiles:
                # We assume ysort tiles like walls are solid
                tr = pygame.Rect(*pos, tilemap.TILE_SIZE, tilemap.TILE_SIZE)
                quadtree.insert(None, tr) # None as eid for static tiles

        # Emit particles
        for eid in self.cm.get_entities_with(ParticleEmitter, Position):
            emitter = self.cm.get(eid, ParticleEmitter)
            pos = self.cm.get(eid, Position).vec

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
                    emitter.emit(self.cm, self.pool, pos)

        # Update particle movement & lifetime
        for eid in self.cm.get_entities_with(Particle, Velocity, Position):
            particle = self.cm.get(eid, Particle)
            pos = self.cm.get(eid, Position)
            vel = self.cm.get(eid, Velocity)

            particle.age += dt
            if particle.age >= particle.lifetime:
                self.pool.release(eid)
                continue

            # Friction
            if particle.friction < 1.0:
                vel.x *= (particle.friction ** (dt * 60.0))
                vel.y *= (particle.friction ** (dt * 60.0))

            # Move with collision if quadtree available
            new_x = pos.x + vel.x * dt
            if quadtree:
                # Check horizontal
                rect_h = pygame.Rect(new_x - particle.size, pos.y - particle.size, int(particle.size*2), int(particle.size*2))
                hits = []
                quadtree.retrieve(hits, rect_h)
                collided_h = False
                for _, tr in hits:
                    if rect_h.colliderect(tr):
                        vel.x *= -0.5 # Bounce and lose energy
                        collided_h = True
                        break
                if not collided_h: pos.x = new_x
            else:
                pos.x = new_x

            new_y = pos.y + vel.y * dt
            if quadtree:
                # Check vertical
                rect_v = pygame.Rect(pos.x - particle.size, new_y - particle.size, int(particle.size*2), int(particle.size*2))
                hits = []
                quadtree.retrieve(hits, rect_v)
                collided_v = False
                for _, tr in hits:
                    if rect_v.colliderect(tr):
                        vel.y *= -0.5 # Bounce and lose energy
                        collided_v = True
                        break
                if not collided_v: pos.y = new_y
            else:
                pos.y = new_y

            if particle.fade:
                alpha = 255 * (1 - particle.age / particle.lifetime)
                particle.color.a = max(0, int(alpha))

            # Handle color flickering
            if particle.flicker_colors:
                idx = int(particle.age * particle.flicker_speed) % len(particle.flicker_colors)
                particle.color = pygame.Color(*particle.flicker_colors[idx])
                if particle.fade:
                    particle.color.a = max(0, int(255 * (1 - particle.age / particle.lifetime)))
