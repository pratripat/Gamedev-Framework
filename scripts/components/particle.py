import pygame, random, math
from dataclasses import dataclass, field
from ..utils import EmitterShape, EmitterShapeType, rotate_vector

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
    image: pygame.Surface = None     # Optional custom image for this particle
    
    # Environmental physics
    sway: bool = False               # Horizontal sine-wave sway
    gravity: float = 0.0             # Constant downward force
    wind_factor: float = 0.0         # How much the global wind affects horizontal speed

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

    def emit(self, particle_system, origin_pos):
        p = particle_system.emit_particle()
        if p is None:
            return  # pool exhausted

        spawn_x, spawn_y = self.get_random_position_within_shape(self.shape, origin_pos[0], origin_pos[1])
        pc = self.particle_config

        p.x = spawn_x
        p.y = spawn_y

        # Velocity Logic
        if pc.vel > 0:
            if pc.direction:
                base_angle = math.atan2(pc.direction.y, pc.direction.x)
                spread_rad = math.radians(pc.spread)
                angle = base_angle + random.uniform(-spread_rad/2, spread_rad/2)
                speed = random.uniform(pc.vel * 0.8, pc.vel * 1.4)
                p.vx = math.cos(angle) * speed
                p.vy = math.sin(angle) * speed
            elif self.shape.type == EmitterShapeType.CIRCLE:
                dx = spawn_x - origin_pos[0]
                dy = spawn_y - origin_pos[1]
                sq_len = dx*dx + dy*dy
                if sq_len > 0.0001:
                    length = math.sqrt(sq_len)
                    speed = random.uniform(pc.vel * 0.8, pc.vel * 1.4)
                    p.vx = (dx / length) * speed
                    p.vy = (dy / length) * speed
                else:
                    angle = random.uniform(0, math.pi * 2)
                    v = random.uniform(pc.vel * 0.8, pc.vel * 1.4)
                    p.vx = math.cos(angle) * v
                    p.vy = math.sin(angle) * v
            else:
                angle = random.uniform(0, math.pi * 2)
                v = random.uniform(pc.vel * 0.8, pc.vel * 1.4)
                p.vx = math.cos(angle) * v
                p.vy = math.sin(angle) * v
        else:
            p.vx = 0
            p.vy = 0

        p.age = 0
        p.lifetime = random.uniform(pc.lifetime * 0.5, pc.lifetime * 1.5)
        
        p.r = pc.color[0]
        p.g = pc.color[1]
        p.b = pc.color[2]
        p.a = pc.color[3] if len(pc.color) > 3 else 255
        
        p.size = random.uniform(pc.size*0.8, pc.size*1.2)
        p.fade = pc.fade
        p.flicker_colors = pc.flicker_colors
        p.flicker_speed = pc.flicker_speed
        p.oscillate_size = pc.oscillate_size
        p.friction = pc.friction
        p.shrink = pc.shrink
        p.image = pc.image
        
        p.sway = pc.sway
        p.gravity = pc.gravity
        p.wind_factor = pc.wind_factor

        self.particle_counter += 1

