#components
from ..components.physics import Position, Velocity, CollisionComponent
from ..components.animation import AnimationComponent, RenderComponent
from ..components.combat import AttackPattern, AttackPatternComponent, WeaponComponent, HitBoxComponent, HurtBoxComponent, HealthComponent
from ..components.tags import PlayerTagComponent, EnemyTagComponent
from ..components.render_effect import YSortRender, ShadowComponent, ProximityFadeComponent, WindAffectedComponent
from ..components.ai import AIComponent
from .component_manager import ComponentManager

from ..systems.animation.animation_state_machine import AnimationStateMachine
from ..weapons.bullet_patterns import SHOOT_FUNCTIONS

from ..utils import CollisionShape, CollisionLayer, get_blob_shadow_surface, SCALE

import json, copy, pygame, random

# function factory for getting cond for transitions
def make_vel_zero_check(entity_id, component_manager, input_system):
    return (lambda eid=entity_id, cm=component_manager: cm.get(eid, Velocity).vec.length_squared() == 0)

def make_anim_finished(entity_id, component_manager, input_system):
    return (lambda eid=entity_id, cm=component_manager: cm.get(eid, AnimationComponent).animation.over)

def make_check_invincibility_timer(entity_id, component_manager, input_system):
    return (lambda eid=entity_id, cm=component_manager: cm.get(eid, HealthComponent).invincibility_timer <= 0)

def make_left_held_release(entity_id, component_manager, input_system):
    return (lambda: input_system.mouse_states["left_held"] == False)

def build_animation_state_machine(eid, data, ctx):
    transitions = copy.deepcopy(data.get("transitions", {}))
    for anim, tdata in transitions.items():
        cond_str = tdata.get("cond")
        if cond_str:
            tdata["cond"] = globals().get("make_" + cond_str, lambda *_: lambda: False)(
                eid, ctx["component_manager"], ctx["input_system"]
            )
    return AnimationStateMachine(
        entity_id=eid,
        component_manager=ctx["component_manager"],
        event_manager=ctx["event_manager"],
        animation_priority_list=data.get("animation_priority_list", []),
        transitions=transitions
    )

class EntityFactory:
    COMPONENT_BUILDERS = {
        "PlayerTagComponent": lambda eid, data, ctx: PlayerTagComponent(),
        "EnemyTagComponent": lambda eid, data, ctx: EnemyTagComponent(),
        "Position": lambda eid, data, ctx: Position(entity_id=eid, x=ctx["pos"][0], y=ctx["pos"][1]),
        "Velocity": lambda eid, data, ctx: Velocity(entity_id=eid, **data),
        "RenderComponent": lambda eid, data, ctx: RenderComponent(
            entity_id=eid,
            surface=(
                ctx.get("image", None) or
                ctx["resource_manager"].get_image(data["image_file"], scale=data.get("image_scale", 1))
            ),
            offset=(data["offset_x"], data["offset_y"]),
            center=data.get("center", True),
            image_file=ctx.get("image_file") or data.get("image_file")
        ),
        "AnimationComponent": lambda eid, data, ctx: AnimationComponent(
            entity_id=eid,
            entity=data["entity"],
            animation_id=data["animation_id"],
            animation_handler=ctx["animation_handler"],
            event_manager=ctx["event_manager"],
            center=data.get("center", True),
            entity_type=data.get("entity_type", "chess_piece")
        ),
        "AnimationStateMachine": build_animation_state_machine,
        "AIComponent": lambda eid, data, ctx: AIComponent(
            entity_id=eid,
            behavior=data["behavior"]
        ),
        "HurtBoxComponent": lambda eid, data, ctx: HurtBoxComponent(
            entity_id=eid,
            offset=(data["offset_x"], data["offset_y"]),
            size=(data["width"], data["height"]),
            shape=CollisionShape.RECT,
            layer=CollisionLayer.PLAYER if ctx.get("player", False) else CollisionLayer.ENEMY,
            center=data.get("center", False)
        ),
        "HealthComponent": lambda eid, data, ctx: HealthComponent(
            entity_id=eid,
            max_health=data["max_health"],
            event_manager=ctx["event_manager"],
            component_manager=ctx["component_manager"]
        ),
        "WeaponComponent": lambda eid, data, ctx: WeaponComponent(
            cooldown=data["cooldown"],
            shoot_fn=SHOOT_FUNCTIONS.get(data["shoot_fn"], None),
            projectile_data=data.get("projectile_data", {})
        ),
        "AttackPatternComponent": lambda eid, data, ctx: AttackPatternComponent(
            patterns=[
                AttackPattern(
                    shoot_fn=SHOOT_FUNCTIONS[p["shoot_fn"]],
                    projectile_data=p["projectile_data"],
                    cooldown=p["cooldown"],
                    duration=p.get("duration", None)
                )
                for p in data["patterns"]
            ],
            loop=data.get("loop", True)
        ),
        "CollisionComponent": lambda eid, data, ctx: CollisionComponent(
            entity_id=eid,
            offset=(data["offset_x"], data["offset_y"]),
            size=(data["width"], data["height"]),
            solid=data.get("solid", False),
            center=data.get("center", False),
            blocks_projectiles=data.get("blocks_projectiles", True)
        ),
        "YSortComponent": lambda eid, data, ctx: YSortRender(
            entity_id=eid,
            offset=(int(data["offset"][0]), int(data["offset"][1])),
        ),
        "ShadowComponent": lambda eid, data, ctx: ShadowComponent(
            entity_id=eid,
            surface=data["surface"],
            offset=(data["offset"][0], data["offset"][1]),
            alpha=data["alpha"],
            center=data["center"]
        ),
        "ProximityFadeComponent": lambda eid, data, ctx: ProximityFadeComponent(
            targets=data["targets"],
            min_dist_squared=data["min_dist"]**2,
            max_dist_squared=data["max_dist"]**2,
            alpha_range=data.get("alpha_range", (0, 255))
        ),

        "WindAffectedComponent": lambda eid, data, ctx: WindAffectedComponent(),
    }

    def __init__(self):
        self.data = json.load(open("data/config/entities.json", "r"))

    def create_player(self, pos, component_manager, entity_manager, event_manager, animation_handler, input_system, resource_manager):
        player = entity_manager.create_entity(player=True)

        # Add components to the player entity
        player_component_data = self.data["player"]

        alpha = 200
        player_component_data["ShadowComponent"] = {
            "surface": get_blob_shadow_surface(alpha=alpha),
            "offset": (0, 18),
            "alpha": alpha,
            "center": True
        }

        self.add_components_to_entity(player, pos, player_component_data, component_manager, entity_manager, event_manager, animation_handler, input_system, resource_manager, player=True)

        return player

    def create_enemy(self, pos, component_manager, entity_manager, event_manager, animation_handler, input_system, resource_manager, chess_piece_type="pawn"):
        enemy = entity_manager.create_entity()

        # Add components to the enemy entity
        enemy_component_data = self.data["enemy_" + chess_piece_type]

        alpha = 200

        enemy_component_data["ShadowComponent"] = {
            "surface": get_blob_shadow_surface(alpha=alpha),
            "offset": (0, 18),
            "alpha": alpha,
            "center": True
        }

        self.add_components_to_entity(enemy, pos, enemy_component_data, component_manager, entity_manager, event_manager, animation_handler, input_system, resource_manager)

        return enemy

    def create_foliage(self, pos, component_manager, entity_manager, event_manager, animation_handler, input_system, resource_manager, render_effect_system, image):
        foliage = entity_manager.create_entity()

        # Add components to the foliage entity
        foliage_component_data = self.data["foliage"]

        self.add_components_to_entity(foliage, pos, foliage_component_data, component_manager, entity_manager, event_manager, animation_handler, input_system, resource_manager, image=image, image_file="data/graphics/spritesheets/foliage.png")

        # Add leaf particle emitter
        from ..components.particle import ParticleEmitter, ParticleConfig, EmitterShape, EmitterShapeType
        
        leaf_color = random.choice([(34, 139, 34), (50, 205, 50), (0, 100, 0)]) # Forest, Lime, Dark Green
        
        component_manager.add(foliage, ParticleEmitter(
            rate=random.uniform(1.0, 2.0), # increased trickle
            duration=9999,
            loop=True,
            particle_config=ParticleConfig(
                vel=random.uniform(5, 15),
                lifetime=random.uniform(4.0, 7.0), # halved lifetime
                color=pygame.Color(*leaf_color),
                size=random.uniform(1.5, 2.6), 
                fade=False,      
                shrink=True,
                friction=0.99,   
                gravity=10.0,    
                sway=True,       
                wind_factor=40.0  # Increased to represent direct velocity contribution
            ),
            # Emit from a random spot in the tree crown
            shape=EmitterShape(EmitterShapeType.CIRCLE, radius=15)
        ))

        render_effect_system.add_proximity_fade_component(foliage)

        return foliage

    def create_entity(self, pos, entity, component_manager, entity_manager, event_manager, animation_handler, input_system, resource_manager):
        """
        Create a generic entity with the given data.
        """
        entity_id = entity_manager.create_entity()

        entity_component_data = self.data.get(entity, {})

        # Add components to the entity
        self.add_components_to_entity(entity_id, pos, entity_component_data, component_manager, entity_manager, event_manager, animation_handler, input_system, resource_manager)

        return entity_id

    def add_components_to_entity(self, entity_id, pos, entity_data, component_manager, entity_manager, event_manager, animation_handler, input_system, resource_manager, player=False, image=None, image_file=None):
        ctx = {
            "pos": pos,
            "component_manager": component_manager,
            "entity_manager": entity_manager,
            "event_manager": event_manager,
            "animation_handler": animation_handler,
            "input_system": input_system,
            "resource_manager": resource_manager,
            "player": player,
            "image": image,
            "image_file": image_file
        }
        
        for component_name, component_data in entity_data.items():
            builder = self.COMPONENT_BUILDERS.get(component_name)
            if builder:
                comp = builder(entity_id, component_data, ctx)
                component_manager.add(entity_id, comp)
            else:
                print(f"[ENTITY FACTORY] No builder found for component '{component_name}' in entity '{entity_id}' with data: {component_data}")

        pos = component_manager.get(entity_id, Position)
        rc = (
            component_manager.get(entity_id, RenderComponent) or
            component_manager.get(entity_id, AnimationComponent)
        )
        if pos and rc:
            img = rc.surface
            pos.x += img.get_width() / 2
            pos.y += img.get_height() / 2
