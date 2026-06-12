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
    # New effects for death particles
    flicker_colors: list = None # List of Colors to alternate between
    flicker_speed: float = 0.0
    oscillate_size: bool = False
    friction: float = 1.0
    shrink: bool = False

@dataclass
class ParticleConfig:
    vel: float = 4.0
    lifetime: float = 2.0
    color: pygame.Color = field(default_factory=lambda: pygame.Color(255, 255, 255))
    size: float = 6.0
    fade: bool = True
    flicker_colors: list = None
    flicker_speed: float = 0.0
    oscillate_size: bool = False
    friction: float = 1.0
    shrink: bool = False
    direction: pygame.Vector2 = None # Optional: bias direction
    spread: float = 45.0             # Degrees of spread around direction

@dataclass
class ParticleEmitter:
    rate: float
    duration: float
    loop: bool = True
    active: bool = True
    particle_config: ParticleConfig = field(default_factory=ParticleConfig)
    shape: EmitterShape = field(default_factory=lambda: EmitterShape(EmitterShapeType.POINT))
    max_particles: int = 1000
    
    elapsed: float = 0.0
    time_since_emit: float = 0.0
    particle_counter: int = 0

    def get_random_position_within_shape(self, shape, origin_x, origin_y):
        if shape.type == EmitterShapeType.POINT:
            return origin_x, origin_y
        
        elif shape.type == EmitterShapeType.RECT:
            rx = random.uniform(shape.rect.left, shape.rect.right)
            ry = random.uniform(shape.rect.top, shape.rect.bottom)
            return origin_x + rx, origin_y + ry
            
        elif shape.type == EmitterShapeType.CIRCLE:
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(0, shape.radius)
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

        # Velocity Logic
        if pc.vel > 0:
            if pc.direction:
                # Directional cone
                base_angle = math.atan2(pc.direction.y, pc.direction.x)
                spread_rad = math.radians(pc.spread)
                angle = base_angle + random.uniform(-spread_rad/2, spread_rad/2)
                speed = random.uniform(pc.vel * 0.8, pc.vel * 1.4)
                vel.x = math.cos(angle) * speed
                vel.y = math.sin(angle) * speed
            elif self.shape.type == EmitterShapeType.CIRCLE:
                # Radial burst
                dir_vec = pygame.Vector2(spawn_x - origin_pos[0], spawn_y - origin_pos[1])
                if dir_vec.length_squared() > 0.0001:
                    speed = random.uniform(pc.vel * 0.8, pc.vel * 1.4)
                    vel_vec = dir_vec.normalize() * speed
                    vel.x = vel_vec.x
                    vel.y = vel_vec.y
                else:
                    angle = random.uniform(0, math.pi * 2)
                    v = random.uniform(pc.vel * 0.8, pc.vel * 1.4)
                    vel.x = math.cos(angle) * v
                    vel.y = math.sin(angle) * v
            else:
                # Full random
                angle = random.uniform(0, math.pi * 2)
                v = random.uniform(pc.vel * 0.8, pc.vel * 1.4)
                vel.x = math.cos(angle) * v
                vel.y = math.sin(angle) * v
        else:
            vel.x = 0
            vel.y = 0

        particle.age = 0
        particle.lifetime = random.uniform(pc.lifetime * 0.5, pc.lifetime * 1.5)
        particle.color = pygame.Color(*pc.color)
        particle.size = random.uniform(pc.size*0.8, pc.size*1.2)
        particle.fade = pc.fade
        particle.flicker_colors = pc.flicker_colors
        particle.flicker_speed = pc.flicker_speed
        particle.oscillate_size = pc.oscillate_size
        particle.friction = pc.friction
        particle.shrink = pc.shrink

        self.particle_counter += 1
