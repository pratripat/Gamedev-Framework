#components
from ..components.physics import Position, Velocity, CollisionComponent
from ..components.animation import AnimationComponent, RenderComponent
from ..components.combat import WeaponComponent, HitBoxComponent, HurtBoxComponent, HealthComponent
from ..components.tags import PlayerTagComponent, EnemyTagComponent
from .component_manager import ComponentManager

from ..systems.animation.animation_state_machine import AnimationStateMachine
from ..weapons.bullet_patterns import SHOOT_FUNCTIONS

from ..utils import CollisionShape, CollisionLayer, load_image

import json, copy

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
        "Position": lambda eid, data, ctx: Position(entity_id=eid, **data),
        "Velocity": lambda eid, data, ctx: Velocity(entity_id=eid, **data),
        "RenderComponent": lambda eid, data, ctx: RenderComponent(
            entity_id=eid,
            surface=load_image(data["image_file"]),
            offset=(data["offset_x"], data["offset_y"]),
            center=data.get("center", True)
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
        "CollisionComponent": lambda eid, data, ctx: CollisionComponent(
            entity_id=eid,
            offset=(data["offset_x"], data["offset_y"]),
            size=(data["width"], data["height"]),
            solid=data.get("solid", False),
            center=data.get("center", False)
        )
    }

    def __init__(self):
        self.data = json.load(open("data/config/entities.json", "r"))

    def create_player(self, component_manager, entity_manager, event_manager, animation_handler, input_system):
        player = entity_manager.create_entity(player=True)

        # Add components to the player entity
        player_component_data = self.data["player"]

        self.add_components_to_entity(player, player_component_data, component_manager, entity_manager, event_manager, animation_handler, input_system, player=True)

        return player

    def create_enemy(self, component_manager, entity_manager, event_manager, animation_handler, input_system, chess_piece_type="pawn"):
        enemy = entity_manager.create_entity()

        # Add components to the enemy entity
        enemy_component_data = self.data["enemy_" + chess_piece_type]

        self.add_components_to_entity(enemy, enemy_component_data, component_manager, entity_manager, event_manager, animation_handler, input_system)

        return enemy

    def add_components_to_entity(self, entity_id, entity_data, component_manager, entity_manager, event_manager, animation_handler, input_system, player=False):
        ctx = {
            "component_manager": component_manager,
            "entity_manager": entity_manager,
            "event_manager": event_manager,
            "animation_handler": animation_handler,
            "input_system": input_system,
            "player": player
        }
        
        for component_name, component_data in entity_data.items():
            builder = self.COMPONENT_BUILDERS.get(component_name)
            if builder:
                comp = builder(entity_id, component_data, ctx)
                component_manager.add(entity_id, comp)
            else:
                print(f"[ENTITY FACTORY] No builder found for component '{component_name}' in entity '{entity_id}' with data: {component_data}")