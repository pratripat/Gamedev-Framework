import json, pygame, os, glob
from ..rendering.tilemap import Tilemap
from ...components.physics import Position
from ...components.ai import AIComponent
from ...components.animation import RenderComponent
from ...components.render_effect import YSortRender
from ..core.collision_grid import CollisionGrid

class Level:
    def __init__(self, ctx):
        self.ctx = ctx
        self.tilemap = None
        self.collision_grid = None

        self.collidables = ["wall", "water"]
    
    def load(self, path, component_manager, entity_factory, entity_manager, render_system):
        data = json.load(open(path, "r"))

        layers = data["layers"]
        tilemaps = data["tilemaps"]
        # loading tilemap
        self.tilemap = Tilemap(layers, tilemaps, self.ctx.resource_manager, exception_layers=["player", "enemies", "foliage", "destructibles"])

        # Generate Grass on the RenderSystem's instance
        if hasattr(render_system, 'grass_system'):
            render_system.grass_system.generate_grass(self.tilemap.layers)

        # Build Static Quadtree for walls and water
        from ...utils import Quadtree
        min_x, min_y, max_x, max_y = self.tilemap.world_bounds
        # Root rect covers the entire level with a bit of padding
        root_rect = (min_x - 100, min_y - 100, (max_x - min_x) + 200, (max_y - min_y) + 200)
        self.static_quadtree = Quadtree(0, root_rect)

        # Create collision boxes per collidable layer
        self.collision_grid = []
        for layer_id in self.collidables:
            layer_data = layers.get(layer_id, [])
            tiles = layer_data.get("tiles", []) if isinstance(layer_data, dict) else layer_data
            
            cg = CollisionGrid(tiles)
            # We no longer create ECS entities for every single static tile.
            # Instead, the static_quadtree handles their collisions.
            self.collision_grid.append((layer_id, cg))
            
            from ...utils import TILE_SIZE
            for tile in tiles:
                tpos = tuple(tile[0])
                rect = pygame.Rect(tpos[0], tpos[1], TILE_SIZE, TILE_SIZE)
                # Unique ID per tile: (layer, position)
                self.static_quadtree.insert((layer_id, tpos), rect)

        # Auto-generate water animation frames (tileable Worley overlay) and build chunk-based water animations
        try:
            from ...utils.water_animator import generate_tileable_worley_frames, load_water_frames
            import hashlib
            import glob

            if "water" in self.tilemap.layers and any(self.tilemap.layers["water"].values()):
                from ...utils import TILE_SIZE
                
                # Parameters for "Dark Bluish" noise
                NUM_FRAMES = 12
                CELLS = 4
                BASE_COLOR = (2, 8, 15)
                HIGHLIGHT = (30, 90, 180) 
                INTENSITY = 0.8

                worley_frames = None
                
                if not worley_frames:
                    # Generate a deterministic seed from the level path so results are stable
                    seed_hash = int(hashlib.md5(path.encode('utf-8')).hexdigest(), 16) % 100000
                    print(f"[LEVEL] Generating dark bluish water frames (seed={seed_hash})")
                    worley_frames = generate_tileable_worley_frames(
                        size=TILE_SIZE, 
                        num_frames=NUM_FRAMES, 
                        cells=CELLS, 
                        base_color=BASE_COLOR, 
                        highlight_color=HIGHLIGHT, 
                        intensity=INTENSITY, 
                        seed=seed_hash, 
                        mode='negative'
                    )

                # Pass the tile-sized frames to tilemap; tilemap will composite them per-chunk (tiled) so tiles align
                self.tilemap.set_water_frames(worley_frames, fps=6, intensity=INTENSITY)
        except Exception as e:
            # Numpy may be missing or import failed; fall back to static water tiles
            import traceback
            print(f"[LEVEL] Water animator not available: {e}")
            traceback.print_exc()

        # player loading
        player = None
        layer_data = layers.get("player", {})
        if isinstance(layer_data, dict):
            player_data = layer_data.get("tiles", [])
        else:
            player_data = layer_data

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
        layer_data = layers.get("enemies", [])
        if isinstance(layer_data, dict):
            enemies_data = layer_data.get("tiles", [])
        else:
            enemies_data = layer_data

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
        
        # destructibles loading
        layer_data = layers.get("destructibles", [])
        if isinstance(layer_data, dict):
            destructibles_data = layer_data.get("tiles", [])
        else:
            destructibles_data = layer_data

        if destructibles_data:
            for tile_pos, _, _, _, _ in destructibles_data:
                entity_factory.create_destructible(
                    pos=tile_pos,
                    component_manager=component_manager,
                    entity_manager=entity_manager,
                    event_manager=self.ctx.event_manager,
                    animation_handler=self.ctx.animation_handler,
                    input_system=self.ctx.input_system,
                    resource_manager=self.ctx.resource_manager
                )

        # foliage loading
        layer_data = layers.get("foliage", [])
        if isinstance(layer_data, dict):
            foliage_data = layer_data.get("tiles", [])
        else:
            foliage_data = layer_data

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
                    render_effect_system = render_system.render_effect_system,
                    image = image
                )
            
        return player

    def render_tilemap(self, surface, camera):
        self.tilemap.render(surface, camera)
