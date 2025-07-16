import json, pygame
from ..rendering.tilemap import Tilemap
from ...components.physics import Position
from ...components.ai import AIComponent
from ...components.animation import RenderComponent
from ...components.render_effect import YSortRender

class Level:
    def __init__(self, ctx):
        self.ctx = ctx
    
    def load(self, path, component_manager, entity_factory, entity_manager):
        data = json.load(open(path, "r"))

        layers = data["layers"]
        tilemaps = data["tilemaps"]

        # loading tilemap
        self.tilemap = Tilemap(layers, tilemaps, self.ctx.resource_manager, exception_layers=["player", "enemies", "foliage"])

        # player loading
        player = None
        player_data = layers.get("player", {})
        if player_data:
            tile_pos = player_data[0][0]
            player = entity_factory.create_player(
                pos = tile_pos,
                component_manager = component_manager,
                entity_manager = entity_manager,
                event_manager = self.ctx.event_manager,
                animation_handler = self.ctx.animation_handler,
                input_system = self.ctx.input_system,
                resource_manager = self.ctx.resource_manager
            )
        
        # enemies loading
        enemies_data = layers.get("enemies", [])
        if enemies_data:
            for tile_pos, _, _, spritesheet_index, _ in enemies_data:
                enemy = entity_factory.create_enemy(
                    pos = tile_pos,
                    component_manager = component_manager,
                    entity_manager = entity_manager,
                    event_manager = self.ctx.event_manager,
                    animation_handler = self.ctx.animation_handler,
                    input_system = self.ctx.input_system,
                    resource_manager = self.ctx.resource_manager,
                    chess_piece_type = ['pawn', 'rook', 'knight', 'bishop'][spritesheet_index]
                )

                # component_manager.add(
                #     enemy, 
                #     AIComponent(
                #         entity_id=enemy,
                #         behavior="chase"  # or "sniper", "patrol", etc.
                #     )
                # )
        
        # foliage loading
        foliage_data = layers.get("foliage", [])
        if foliage_data:
            for tile_pos, _, _, spritesheet_index, scale in foliage_data:
                image = self.ctx.resource_manager.get_spritesheet("data/graphics/spritesheets/foliage.png", index=spritesheet_index, scale=scale)
                foliage = entity_factory.create_foliage(
                    pos = tile_pos,
                    component_manager = component_manager,
                    entity_manager = entity_manager,
                    event_manager = self.ctx.event_manager,
                    animation_handler = self.ctx.animation_handler,
                    input_system = self.ctx.input_system,
                    resource_manager = self.ctx.resource_manager,
                    image = image
                )
            
        return player

    def render_tilemap(self, surface, camera):
        self.tilemap.render(surface, camera)
