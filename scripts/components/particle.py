import pygame, random, math
from dataclasses import dataclass, field
from ..components.physics import Position, Velocity
from ..utils import EmitterShape, EmitterShapeType, rotate_vector

@dataclass
class Particle:
    lifetime: float
    color: pygame.Color = field(default_factory=lambda: pygame.Color(255, 255, 255))
    age: float = 0.0
    size: float = 1.0
    rotation: float = 0.0
    spin: float = 0.0
    fade: bool = True

@dataclass
class ParticleConfig:
    vel: float = 4.0
    lifetime: float = 2.0
    color: pygame.Color = field(default_factory=lambda: pygame.Color(255, 255, 255))
    size: float = 6.0
    fade: bool = True

@dataclass
class ParticleEmitter:
    rate: float
    duration: float
    loop: bool
    particle_config: ParticleConfig = field(default_factory=lambda: ParticleConfig())
    elapsed: float = 0.0
    time_since_emit: float = 0.0
    max_particles: int = 100
    active: bool = True
    shape: EmitterShape = field(default_factory=lambda: EmitterShape(EmitterShapeType.POINT))
    particle_counter: int = 0

    def get_random_position_within_shape(self, shape: EmitterShape, origin_x: float, origin_y: float):
        if shape.type == EmitterShapeType.POINT:
            return origin_x, origin_y

        elif shape.type == EmitterShapeType.RECT and shape.rect:
            rx = random.uniform(shape.rect.left, shape.rect.right)
            ry = random.uniform(shape.rect.top, shape.rect.bottom)
            return origin_x + rx, origin_y + ry

        elif shape.type == EmitterShapeType.CIRCLE:
            angle = random.uniform(0, 2 * math.pi)
            radius = shape.radius * random.uniform(0, 1)
            rx = origin_x + radius * math.cos(angle)
            ry = origin_y + radius * math.sin(angle)
            return rx, ry

        return origin_x, origin_y

    def emit(self, component_manager, pool, origin_pos):
        eid = pool.get()
        if eid is None:
            return  # pool exhausted

        pos = component_manager.get(eid, Position)
        vel = component_manager.get(eid, Velocity)
        particle = component_manager.get(eid, Particle)

        spawn_x, spawn_y = self.get_random_position_within_shape(self.shape, origin_pos[0], origin_pos[1])

        pc = self.particle_config

        pos.vec = pygame.Vector2(spawn_x, spawn_y)
        vel.x = random.uniform(-pc.vel, pc.vel)
        vel.y = random.uniform(-pc.vel, pc.vel)
        particle.age = 0
        particle.lifetime = random.uniform(pc.lifetime-1, pc.lifetime+1)
        particle.color = pygame.Color(*pc.color)
        particle.size = random.uniform(pc.size*0.8, pc.size*1.2)
        particle.fade = pc.fade

        self.particle_counter += 1