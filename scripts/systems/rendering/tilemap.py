import pygame
import os
from ...utils import TILE_SIZE, CHUNK_SIZE

class Tilemap:
    TILE_SIZE = TILE_SIZE
    CHUNK_SIZE = CHUNK_SIZE
    CHUNK_RES = TILE_SIZE * CHUNK_SIZE

    def __init__(self, layers, tilemaps, resource_manager, exception_layers=[], ysort_layers=["wall"]):
        self.layers = {}       # {layer_id: {chunk_pos: {tile_pos: tile_data}}}
        self.chunk_images = {} # {layer_id: {chunk_pos: image}}
        self.layer_order = list(layers.keys())
        self.ysort_layers = ysort_layers

        # Water animation state
        self.water_frames = None
        self.water_frame_index = 0
        self.water_frame_timer = 0.0
        self.WATER_FPS = 8

        self.load_layers(layers, tilemaps, resource_manager, exception_layers)
    
    def _get_chunk_pos(self, pos):
        # Return integer chunk top-left coordinate in pixels
        cx = int((int(pos[0]) // self.CHUNK_RES) * self.CHUNK_RES)
        cy = int((int(pos[1]) // self.CHUNK_RES) * self.CHUNK_RES)
        return (cx, cy)

    def load_layers(self, layers, tilemaps, rm, exception_layers):
        for layer_id, layer_data in layers.items():
            self.layers[layer_id] = {}

            # Handle both old format (list of tiles) and new format (dict with 'tiles' and 'autotile_config')
            if isinstance(layer_data, dict):
                tiles = layer_data.get("tiles", [])
            else:
                tiles = layer_data

            for tile_data in tiles:
                (
                    tile_pos,
                    _,
                    filepath_index,
                    spritesheet_index,
                    image_scale
                ) = tile_data

                # Ensure tile positions are integer pixel coordinates
                tile_pos = tuple(map(int, tile_pos))

                filepath = list(tilemaps.keys())[filepath_index]

                image = None
                if spritesheet_index != None:
                    image = (
                        rm.get_spritesheet(filepath, index=spritesheet_index, scale=image_scale) or 
                        rm.get_tilemap(filepath, index=spritesheet_index, scale=image_scale)
                    )
                else:
                    image = rm.get_image(filepath, scale=image_scale)

                if image is None:
                    image = pygame.Surface((self.TILE_SIZE, self.TILE_SIZE))
                    image.set_colorkey((0, 0, 0))
                    image.convert()
                    print('[TILEMAP] Image not found:', filepath)

                chunk_pos = self._get_chunk_pos(tile_pos)
                if chunk_pos not in self.layers[layer_id]:
                    self.layers[layer_id][chunk_pos] = {}
                
                self.layers[layer_id][chunk_pos][tile_pos] = {
                    "image": image,
                    "filepath": filepath,
                    "rect": pygame.Rect(tile_pos[0], tile_pos[1], self.TILE_SIZE, self.TILE_SIZE),
                    "spritesheet_index": spritesheet_index,
                    "image_scale": image_scale
                }
            
        self.create_chunk_images(exception_layers)

    def update(self, dt):
        if self.water_frames:
            self.water_frame_timer += dt
            if self.water_frame_timer >= 1 / self.WATER_FPS:
                self.water_frame_timer = 0
                self.water_frame_index = (self.water_frame_index + 1) % len(self.water_frames)

    def set_water_frames(self, frames, fps: int = 8, intensity: float = 0.6):
        """
        Set pre-baked water tile frames and prepare masked variants for each unique water tile image.
        """
        self.WATER_FPS = fps
        self.water_frame_index = 0
        self.water_frame_timer = 0.0
        self.water_intensity = intensity

        self.water_frames = frames
        self.water_num_frames = len(frames)
        
        # Prepare per-image masked animation frames to avoid edges/grass pixels
        self._prepare_masked_water_frames()

        print(f"[TILEMAP] Set water frames: {self.water_num_frames} frames, prepared masked variants")

    def _prepare_masked_water_frames(self):
        """Pre-calculate masked animation frames for unique water tiles with selective side erosion."""
        unique_images = {} # id(img) -> img
        water_layer = self.layers.get("water", {})
        
        # Build a set of all water tile world positions for quick neighbor checking
        self.water_tile_positions = set()
        for chunk_pos, tiles in water_layer.items():
            for tile_pos in tiles.keys():
                self.water_tile_positions.add(tile_pos)

        for chunk in water_layer.values():
            for tile in chunk.values():
                img = tile.get("image")
                if img:
                    unique_images[id(img)] = img
        
        self.water_frames_map = {} # (img_id, edge_bits) -> [frames...]
        
        try:
            import numpy as np
            for img_id, img in unique_images.items():
                # Base water mask: pixels that are clearly blue-ish
                arr = pygame.surfarray.array3d(img)
                blue = arr[:, :, 2].astype(np.int16)
                red = arr[:, :, 0].astype(np.int16)
                green = arr[:, :, 1].astype(np.int16)
                
                # Stricter water detection
                base_mask = (blue > red + 15) & (blue > green + 15) & (blue > 40)
                
                # Pre-calculate all 16 possible edge configurations (4 bits: T, R, B, L)
                for bits in range(16):
                    mask = base_mask.copy()
                    # Erode 3 pixels ONLY on the sides that are marked as edges
                    # bits: 1=Top, 2=Right, 4=Bottom, 8=Left
                    for _ in range(3):
                        eroded = mask.copy()
                        if bits & 1: # Top (Y=0) -> shift DOWN (+Y, axis=1)
                            shifted = np.roll(mask, shift=1, axis=1); shifted[:, 0] = False; eroded &= shifted
                        if bits & 2: # Right (X=W-1) -> shift LEFT (-X, axis=0)
                            shifted = np.roll(mask, shift=-1, axis=0); shifted[-1, :] = False; eroded &= shifted
                        if bits & 4: # Bottom (Y=H-1) -> shift UP (-Y, axis=1)
                            shifted = np.roll(mask, shift=-1, axis=1); shifted[:, -1] = False; eroded &= shifted
                        if bits & 8: # Left (X=0) -> shift RIGHT (+X, axis=0)
                            shifted = np.roll(mask, shift=1, axis=0); shifted[0, :] = False; eroded &= shifted
                        mask = eroded
                    
                    mask_float = mask.astype(np.float32)
                    masked_list = []
                    for f in self.water_frames:
                        f_arr = pygame.surfarray.array3d(f).astype(np.float32)
                        masked_f = f_arr * mask_float[:, :, np.newaxis]
                        
                        out_surf = pygame.Surface(f.get_size()).convert()
                        pygame.surfarray.blit_array(out_surf, masked_f.astype(np.uint8))
                        out_surf.set_colorkey((0,0,0))
                        masked_list.append(out_surf)
                    
                    self.water_frames_map[(img_id, bits)] = masked_list
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[TILEMAP] Failed to prepare masked water frames: {e}")
            self.water_frames_map = {}

    def create_chunk_images(self, exception_layers):
        """Pre-renders each chunk into a single Surface."""
        for layer_id in self.layers:
            # Skip exception layers and water (water is animated and rendered per-tile)
            if layer_id in exception_layers or layer_id == "water":
                continue
            
            if layer_id not in self.chunk_images:
                self.chunk_images[layer_id] = {}

            for chunk_pos, tiles in self.layers.get(layer_id, {}).items():
                chunk_surface = pygame.Surface((self.CHUNK_RES, self.CHUNK_RES))
                chunk_surface.set_colorkey((0, 0, 0))  # Set colorkey for transparency                
                chunk_surface.convert()
                chunk_rect = chunk_surface.get_rect(topleft=chunk_pos)

                for tile_pos, tile_data in tiles.items():
                    rel_pos = ((tile_pos[0]-chunk_pos[0]), (tile_pos[1]-chunk_pos[1]))
                    chunk_surface.blit(tile_data["image"], rel_pos)
                
                self.chunk_images[layer_id][chunk_pos] = chunk_surface, chunk_rect
    
    def render(self, surface, camera):
        """Draw visible chunks based on camera view."""
        for layer_id in self.layer_order:
            if layer_id == "water":
                self._render_water(surface, camera)
                continue
            
            # Skip layers that are Y-Sorted with entities
            if layer_id in self.ysort_layers:
                continue

            if layer_id not in self.chunk_images:
                continue
            chunks = self.chunk_images[layer_id]
            for chunk_pos, (chunk_image, chunk_rect) in chunks.items():
                if camera.rect.colliderect(chunk_rect):
                    surface.blit(chunk_image, 
                                    (int(round(chunk_pos[0] - camera.scroll.x)), 
                                    int(round(chunk_pos[1] - camera.scroll.y))))

    def _render_water(self, surface, camera):
        """Render water layer per-tile with selective edge erosion masking."""
        water_layer = self.layers.get("water", {})
        
        for chunk_pos, tiles in water_layer.items():
            # Quick visibility check for the whole chunk
            chunk_rect = pygame.Rect(chunk_pos[0], chunk_pos[1], self.CHUNK_RES, self.CHUNK_RES)
            if not camera.rect.colliderect(chunk_rect):
                continue
            
            for tile_pos, tile_data in tiles.items():
                tile_rect = tile_data["rect"]
                if not camera.rect.colliderect(tile_rect):
                    continue
                
                blit_pos = (
                    int(round(tile_pos[0] - camera.scroll.x)), 
                    int(round(tile_pos[1] - camera.scroll.y))
                )
                
                # 1. Render base tile image
                base_img = tile_data.get("image")
                if base_img:
                    surface.blit(base_img, blit_pos)
                
                # 2. Render pre-masked animation overlay
                if self.water_frames_map:
                    # Calculate edge bits: 1=Top, 2=Right, 4=Bottom, 8=Left
                    # We check if a neighbor exists in the water layer
                    bits = 0
                    if (tile_pos[0], tile_pos[1] - self.TILE_SIZE) not in self.water_tile_positions: bits |= 1
                    if (tile_pos[0] + self.TILE_SIZE, tile_pos[1]) not in self.water_tile_positions: bits |= 2
                    if (tile_pos[0], tile_pos[1] + self.TILE_SIZE) not in self.water_tile_positions: bits |= 4
                    if (tile_pos[0] - self.TILE_SIZE, tile_pos[1]) not in self.water_tile_positions: bits |= 8
                    
                    img_id = id(base_img)
                    frames = self.water_frames_map.get((img_id, bits))
                    if frames:
                        frame = frames[self.water_frame_index % len(frames)]
                        surface.blit(frame, blit_pos, special_flags=pygame.BLEND_RGB_ADD)
                elif self.water_frames:
                    # Fallback to simple blit if map failed
                    frame = self.water_frames[self.water_frame_index % len(self.water_frames)]
                    surface.blit(frame, blit_pos, special_flags=pygame.BLEND_RGB_ADD)
    
    def get_ysort_items(self, camera_rect):
        """Returns a list of tiles from ysort_layers that are within camera_rect."""
        items = [] # (sort_y, surface, pos)
        for layer_id in self.ysort_layers:
            if layer_id not in self.layers:
                continue
            
            for chunk_pos, tiles in self.layers[layer_id].items():
                # Quick chunk visibility check
                chunk_rect = pygame.Rect(chunk_pos[0], chunk_pos[1], self.CHUNK_RES, self.CHUNK_RES)
                if not camera_rect.colliderect(chunk_rect):
                    continue
                
                for tile_pos, tile_data in tiles.items():
                    if camera_rect.colliderect(tile_data["rect"]):
                        # Standard Y-sorting: sort by bottom edge of the tile
                        sort_y = tile_pos[1] + self.TILE_SIZE
                        items.append((sort_y, "tile", tile_data["image"], tile_pos))
        return items
                    