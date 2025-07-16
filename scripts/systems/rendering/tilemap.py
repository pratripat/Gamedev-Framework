import pygame

class Tilemap:
    TILE_SIZE = 64
    CHUNK_SIZE = 16
    CHUNK_RES = TILE_SIZE * CHUNK_SIZE

    def __init__(self, layers, tilemaps, resource_manager, exception_layers=[]):
        self.layers = {}       # {layer_id: {chunk_pos: {tile_pos: tile_data}}}
        self.chunk_images = {} # {layer_id: {chunk_pos: image}}

        self.load_layers(layers, tilemaps, resource_manager, exception_layers)
    
    def _get_chunk_pos(self, pos):
        return ((pos[0] // self.CHUNK_RES) * self.CHUNK_RES, (pos[1] // self.CHUNK_RES) * self.CHUNK_RES)

    def load_layers(self, layers, tilemaps, rm, exception_layers):
        for layer_id, tiles in layers.items():
            self.layers[layer_id] = {}

            for tile_data in tiles:
                (
                    tile_pos,
                    _,
                    filepath_index,
                    spritesheet_index,
                    image_scale
                ) = tile_data

                tile_pos = tuple(tile_pos)

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

    def create_chunk_images(self, exception_layers):
        """Pre-renders each chunk into a single Surface."""
        for layer_id in self.layers:
            if layer_id in exception_layers:
                continue
            
            for chunk_pos, tiles in self.layers.get(layer_id, {}).items():
                chunk_rect = None
                if chunk_pos in self.chunk_images:
                    chunk_surface, chunk_rect = self.chunk_images[chunk_pos]
                else:
                    chunk_surface = pygame.Surface((self.CHUNK_RES, self.CHUNK_RES))
                    chunk_surface.set_colorkey((0, 0, 0))  # Set colorkey for transparency                
                    chunk_surface.convert()
                    chunk_rect = chunk_surface.get_rect(topleft=chunk_pos)

                for tile_pos, tile_data in tiles.items():
                    rel_pos = ((tile_pos[0]-chunk_pos[0]), (tile_pos[1]-chunk_pos[1]))
                    chunk_surface.blit(tile_data["image"], rel_pos)
                
                self.chunk_images[chunk_pos] = chunk_surface, chunk_rect
    
    def render(self, surface, camera):
        """Draw visible chunks based on camera view."""
        for chunk_pos, (chunk_image, chunk_rect) in self.chunk_images.items():
            if camera.rect.colliderect(chunk_rect):
                surface.blit(chunk_image, 
                                (chunk_pos[0] - camera.scroll.x, 
                                chunk_pos[1] - camera.scroll.y))
                    