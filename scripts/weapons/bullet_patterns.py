import pygame
from ..utils import get_unit_direction_towards, rotate_vector, load_image, CollisionShape, CollisionLayer, EmitterShape, EmitterShapeType
from ..components.physics import Position, Velocity, CollisionComponent
from ..components.animation import RenderComponent, AnimationComponent
from ..components.projectile import ProjectileComponent
from ..components.combat import HitBoxComponent
from ..components.timer import TimerComponent
from ..components.particle import ParticleConfig
from ..systems.rendering.particle_effect_system import ParticleEmitter

def spawn_bomb(eid, cm, em, anim_handler, event_manager, data):
    bomb_id = em.create_entity()

    timer = data.get("timer", 0.75)
    radius = data.get("radius", 150)
    diameter = radius*2
    pos = data.get("pos", (0, 0))

    def on_burst():
        cm.remove(bomb_id, AnimationComponent)
        
        circle_surf = pygame.Surface((diameter, diameter))
        circle_surf.set_colorkey((0, 0, 0))
        pygame.draw.circle(circle_surf, (255, 255, 255), (radius, radius), radius)

        cm.add(
            bomb_id,
            ProjectileComponent(
                bomb_id,
                damage = data.get("damage", 30),
                lifetime = 0.2,
                penetration=100
            ),
            RenderComponent(
                bomb_id,
                surface=circle_surf,
                center=True
            ),
            HitBoxComponent(
                bomb_id,
                offset=(0,0),
                size=(diameter, diameter),
                shape=CollisionShape.CIRCLE,
                layer=CollisionLayer.PROJECTILE,
                mask=CollisionLayer.create_mask(CollisionLayer.ENEMY | CollisionLayer.PLAYER)
            ),
            ParticleEmitter(
                rate=50,
                duration=2,
                loop=False,
                particle_config=ParticleConfig(vel=1, size=radius * 0.25),
                shape=EmitterShape(type=EmitterShapeType.CIRCLE, radius=radius)
            )
        )

    cm.add(
        bomb_id,
        Position(bomb_id, *pos),
        Velocity(bomb_id, 0, 0),
        AnimationComponent(
            bomb_id,
            "bomb",
            "lit",
            animation_handler=anim_handler,
            event_manager=event_manager
        ),
        TimerComponent(
            timer,
            on_burst,
            destroy=True
        )
    )

def spawn_projectile(eid, cm, em, direction, data, position_offset=pygame.Vector2(0,0)):
    pos = data.get("start_pos", pygame.Vector2(0, 0))
    spawn_pos = pos + position_offset

    raw_layer = data.get("layer", CollisionLayer.PROJECTILE)
    layer = raw_layer if isinstance(raw_layer, CollisionLayer) else CollisionLayer(raw_layer)

    raw_mask = data.get("mask", CollisionLayer.create_mask(CollisionLayer.ENEMY, CollisionLayer.PLAYER))
    mask = raw_mask.value if isinstance(raw_mask, CollisionLayer) else raw_mask

    projectile_scale = 15

    proj_id = em.create_entity()
    cm.add(
        proj_id,
        Position(proj_id, spawn_pos.x, spawn_pos.y),
        Velocity(proj_id, direction.x * data["speed"], direction.y * data["speed"], data["speed"]),
        ProjectileComponent(
            source_entity=eid,
            damage=data["damage"],
            effects=data.get("effects", []),
            bounce=data.get("bounce", 0),
            penetration=data.get("penetration", 0)
        ),
        RenderComponent(
            proj_id,
            load_image(data["image_file"], scale=data["size"]),
            center = True
        ),
        HitBoxComponent(
            entity_id=proj_id,
            offset=(0,0),
            size=(data["size"]*projectile_scale, data["size"]*projectile_scale),
            shape=CollisionShape.CIRCLE,
            layer=layer,
            mask=mask
        ),
        CollisionComponent(
            entity_id=proj_id,
            offset=(0, 0),
            size=(data["size"]*projectile_scale, data["size"]*projectile_scale),
            center=True
        )
    )

    # print(f"[DEBUG] Spawned projectile {proj_id} at {spawn_pos} with velocity {direction * data["speed"]}, layer={layer}, mask={mask}")

    return proj_id

def shoot_single(eid, cm, em, data):
    dir = get_unit_direction_towards(data["start_pos"], data["target_pos"])
    return [spawn_projectile(eid, cm, em, dir, data)]

def shoot_spread(eid, cm, em, data):
    dir = get_unit_direction_towards(data["start_pos"], data["target_pos"])
    max_angle = data.get("angle", 15)
    dirs = [rotate_vector(dir, angle) for angle in [-max_angle, 0, max_angle]]
    
    projs = []
    for d in dirs:
        projs.append(spawn_projectile(eid, cm, em, d, data))
    
    return projs

def shoot_radial(eid, cm, em, data):
    dir = pygame.Vector2(1, 0)
    if data.get("on_player", False): dir = get_unit_direction_towards(data["start_pos"], data["target_pos"])
    
    number = data.get("number", 10)

    projs = []
    for i in range(number):
        angle = (360 / number) * i
        d = rotate_vector(dir, angle)

        projs.append(spawn_projectile(eid, cm, em, d, data))
    
    return projs

class SpiralShooter:
    def __init__(self, bullets_per_shot=10, angle_increment=1):
        self.current_angle = 0
        self.bullets_per_shot = bullets_per_shot
        self.angle_increment = angle_increment

    def __call__(self, eid, cm, em, data):
        dir = pygame.Vector2(1, 0)
        dir = rotate_vector(dir, self.current_angle)
        if data.get("on_player", False): dir = get_unit_direction_towards(data["start_pos"], data["target_pos"])
        
        projs = []
        for i in range(self.bullets_per_shot):
            angle = (360 / self.bullets_per_shot) * i
            d = rotate_vector(dir, angle)

            projs.append(spawn_projectile(eid, cm, em, d, data))
        
        self.current_angle += self.angle_increment
        
        return projs
    
SHOOT_FUNCTIONS = {
    "shoot_single": shoot_single,
    "shoot_spread": shoot_spread,
    "shoot_radial": shoot_radial,
    "shoot_radial_spiral": SpiralShooter(bullets_per_shot=10, angle_increment=1)
}