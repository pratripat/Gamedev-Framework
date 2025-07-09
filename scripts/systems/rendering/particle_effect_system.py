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
            self.cm.add(eid, Particle(lifetime=0), Position(0, 0), Velocity(0, 0))
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

    def update(self, dt):
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

            pos.x += vel.x * dt
            pos.y += vel.y * dt

            if particle.fade:
                alpha = 255 * (1 - particle.age / particle.lifetime)
                particle.color.a = max(0, int(alpha))

    def render(self, screen, scroll):
        for eid in self.cm.get_entities_with(Particle, Position):
            particle = self.cm.get(eid, Particle)
            pos = self.cm.get(eid, Position)

            size = particle.size

            particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, particle.color, (size, size), size)

            screen.blit(particle_surf, (pos.x - scroll.x - size, pos.y - scroll.y - size))
