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
    
    def load(self, path, component_manager, entity_factory, entity_manager, render_effect_system):
        data = json.load(open(path, "r"))

        layers = data["layers"]
        tilemaps = data["tilemaps"]

        # loading tilemap
        self.tilemap = Tilemap(layers, tilemaps, self.ctx.resource_manager, exception_layers=["player", "enemies", "foliage"])

        # Create collision boxes per collidable layer so some layers (like water) can be non-blocking for projectiles
        self.collision_grid = []
        for layer_id in self.collidables:
            layer_collidables = layers.get(layer_id, [])
            cg = CollisionGrid(layer_collidables)
            # water should NOT block projectiles (they fly over it); other layers block projectiles
            blocks_projectiles = False if layer_id == "water" else True
            cg.create_collision_boxes(entity_manager, component_manager, blocks_projectiles=blocks_projectiles)
            self.collision_grid.append((layer_id, cg))

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

                # Optional: Try to load pre-generated frames if they match our needs
                # (Disabled for now to ensure the new dark bluish effect is always applied)
                worley_frames = None
                # gen_dirs = sorted(glob.glob("data/graphics/generated_water_*"))
                # if gen_dirs:
                #     latest_dir = gen_dirs[-1]
                #     worley_frames = load_water_frames(latest_dir, scale=TILE_SIZE/32.0)
                
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
                #         behavior="sniper"  # or "sniper", "patrol", etc.
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
                    render_effect_system = render_effect_system,
                    image = image
                )
            
        return player

    def render_tilemap(self, surface, camera):
        self.tilemap.render(surface, camera)
