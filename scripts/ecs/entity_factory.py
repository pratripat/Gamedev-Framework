#components
from ..components.physics import Position, Velocity, CollisionComponent
from ..components.animation import AnimationComponent, RenderComponent
from ..components.combat import WeaponComponent, HitBoxComponent, HurtBoxComponent, HealthComponent
from ..components.tags import PlayerTagComponent, EnemyTagComponent
from .component_manager import ComponentManager

from ..utils import CollisionShape, CollisionLayer, load_image

import json

class EntityFactory:
    def __init__(self):
        self.data = json.load(open("data/config/entities.json", "r"))

    def create_player(self, component_manager, entity_manager, event_manager, animation_handler, input_system):
        player = entity_manager.create_entity(player=True)

        # Add components to the player entity
        player_component_data = self.data["player"]

        self.add_components_to_entity(player, player_component_data, component_manager, entity_manager, event_manager, animation_handler, input_system)

        return player

    def add_components_to_entity(self, entity_id, entity_data, component_manager, entity_manager, event_manager, animation_handler, input_system):
        for component_name, component_data in entity_data.items():
            if component_name == "PlayerTagComponent":
                comp = PlayerTagComponent()
            elif component_name == "EnemyTagComponent":
                comp = EnemyTagComponent()
            elif component_name == "Position":
                comp = Position(entity_id, **component_data)
            elif component_name == "Velocity":
                comp = Velocity(entity_id, **component_data)
            elif component_name == "AnimationComponent":
                comp = AnimationComponent(
                    entity_id,
                    entity =  component_data["entity"],
                    animation_id =  component_data["animation_id"],
                    animation_handler = animation_handler,
                    event_manager = event_manager,
                    center = component_data.get("center", True),
                    entity_type = component_data.get("entity_type", "chess_piece")
                )
            elif component_name == "RenderComponent":
                comp = RenderComponent(
                    entity_id,
                    surface = load_image(component_data["image_file"]),
                    offset = (component_data["offset_x"], component_data["offset_y"]),
                    center = component_data.get("center", True)
                )
            elif component_name == "HurtBoxComponent":
                comp = HurtBoxComponent(
                    entity_id,
                    offset = (component_data["offset_x"], component_data["offset_y"]),
                    size = (component_data["width"], component_data["height"]),
                    shape = CollisionShape.RECT,
                    layer = CollisionLayer.PLAYER,
                    center = component_data.get("center", True)
                )
            elif component_name == "HealthComponent":
                comp = HealthComponent(
                    entity_id,
                    max_health = component_data["max_health"],
                    event_manager = event_manager,
                    component_manager = component_manager
                )
            elif component_name == "CollisionComponent":
                comp = CollisionComponent(
                    entity_id,
                    offset = (component_data["offset_x"], component_data["offset_y"]),
                    size = (component_data["width"], component_data["height"]),
                    solid = component_data.get("solid", True),
                    center = component_data.get("center", True)
                )
            
            component_manager.add(entity_id, comp)