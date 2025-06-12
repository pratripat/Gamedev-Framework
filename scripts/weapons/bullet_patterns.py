import pygame
from ..utils import get_unit_direction_towards, rotate_vector, load_image, CollisionShape, CollisionLayer
from ..components.physics import Position, Velocity
from ..components.animation import RenderComponent, AnimationComponent
from ..components.projectile import ProjectileComponent
from ..components.combat import HitBoxComponent

def spawn_projectile(eid, cm, em, direction, data, position_offset=pygame.Vector2(0,0)):
    pos = data['start_pos']
    spawn_pos = pos + position_offset

    proj_id = em.create_entity()
    cm.add(
        proj_id,
        Position(proj_id, spawn_pos.x, spawn_pos.y),
        Velocity(proj_id, direction.x * data['speed'], direction.y * data['speed']),
        ProjectileComponent(
            source_entity=eid,
            damage=data['damage'],
            effects=data.get('effects', [])
        ),
        RenderComponent(
            proj_id,
            load_image(data['image_file']),
            center = True
        ),
        HitBoxComponent(
            entity_id=proj_id,
            offset=(0,0),
            size=(data['size'], data['size']),
            shape=CollisionShape.CIRCLE,
            layer=data.get('layer', CollisionLayer.PROJECTILE.value),
            mask=data.get('mask', CollisionLayer.create_mask(CollisionLayer.ENEMY))
        )
    )

    return proj_id

def shoot_single(eid, cm, em, data):
    dir = get_unit_direction_towards(data['start_pos'], data['target_pos'])
    return [spawn_projectile(eid, cm, em, dir, data)]

def shoot_spread(eid, cm, em, data):
    dir = get_unit_direction_towards(data['start_pos'], data['target_pos'])
    max_angle = data.get('angle', 15)
    dirs = [rotate_vector(dir, angle) for angle in [-max_angle, 0, max_angle]]
    
    projs = []
    for d in dirs:
        projs.append(spawn_projectile(eid, cm, em, d, data))
    
    return projs

def shoot_radial(eid, cm, em, data):
    dir = pygame.Vector2(1, 0)
    if data.get('on_player', False): dir = get_unit_direction_towards(data['start_pos'], data['target_pos'])
    
    number = data.get('number', 10)

    projs = []
    for i in range(number):
        angle = (360 / number) * i
        d = rotate_vector(dir, angle)

        projs.append(spawn_projectile(eid, cm, em, d, data))
    
    return projs