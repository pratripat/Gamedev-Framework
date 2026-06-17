import pygame
import os
from ...utils import load_image, load_images_from_spritesheet, load_images_from_tilemap, SCALE, swap_color #, load_sound

class ResourceManager: 
    def __init__(self):
        self.images = {}       # (path, effective_scale) or (path, effective_scale, target_color)
        self.spritesheets = {} # (path, effective_scale)
        self.tilemaps = {}     # (path, effective_scale)
        self.sound = {}
    
    def get_image(self, path, scale=1, color_swap=None, **kwargs):
        # Apply global SCALE multiplicatively so every asset respects one global scale
        effective_scale = round(scale * SCALE, 3)

        # Handle potential absolute paths from level data by making them relative to project root
        if path and os.path.isabs(path):
            if not os.path.exists(path):
                if 'data/' in path:
                    path = path[path.find('data/'):]
                else:
                    path = os.path.basename(path)

        # Cache key base
        key_base = (path, float(effective_scale))
        if color_swap:
            key = (path, float(effective_scale), tuple(color_swap))
        else:
            key = key_base

        if key in self.images:
            return self.images[key]

        if (path, 1.0) not in self.images:
            image = load_image(path)
            if not (path or image):
                return None    
            self.images[(path, 1.0)] = image
        
        original_image = self.images[(path, 1.0)]

        if effective_scale != 1.0:
            if key_base not in self.images:
                self.images[key_base] = pygame.transform.scale(
                    original_image,
                    (int(original_image.get_width() * effective_scale), int(original_image.get_height() * effective_scale))
                )
            base_scaled = self.images[key_base]
        else:
            base_scaled = original_image

        if color_swap:
            PROJECTILE_BLUES = [(18, 78, 137), (0, 153, 219), (44, 232, 245)]
            self.images[key] = swap_color(base_scaled, PROJECTILE_BLUES, color_swap)
            return self.images[key]

        return base_scaled
    
    def get_spritesheet(self, path, index=None, scale=1, **kwargs): 
        effective_scale = round(scale * SCALE, 3)

        if path and os.path.isabs(path):
            if not os.path.exists(path):
                if 'data/' in path: path = path[path.find('data/'):]
                else: path = os.path.basename(path)

        if path and (path, 1.0) not in self.spritesheets:
            images = load_images_from_spritesheet(path)
            if not (path and len(images)): return None
            self.spritesheets[(path, 1.0)] = images

        if effective_scale != 1.0:
            key = (path, float(effective_scale))
            if key not in self.spritesheets:
                self.spritesheets[key] = [
                    pygame.transform.scale(image, (int(image.get_width() * effective_scale), int(image.get_height() * effective_scale)))
                    for image in self.spritesheets[(path, 1.0)]
                ]
            return self.spritesheets[key][index] if index != None else self.spritesheets[key]

        return self.spritesheets[(path, 1.0)][index] if index != None else self.spritesheets[(path, 1.0)]
    
    def get_tilemap(self, path, index=None, scale=1, **kwargs):
        effective_scale = round(scale * SCALE, 3)

        if path and os.path.isabs(path):
            if not os.path.exists(path):
                if 'data/' in path: path = path[path.find('data/'):]
                else: path = os.path.basename(path)

        if path and (path, 1.0) not in self.tilemaps:
            from ...utils import TILE_SIZE
            images = load_images_from_tilemap(path, tile_size=TILE_SIZE)
            if not (path and len(images)): return None
            self.tilemaps[(path, 1.0)] = images

        if effective_scale != 1.0:
            key = (path, float(effective_scale))
            if key not in self.tilemaps:
                self.tilemaps[key] = [
                    pygame.transform.scale(image, (int(image.get_width() * effective_scale), int(image.get_height() * effective_scale)))
                    for image in self.tilemaps[(path, 1.0)]
                ]
            return self.tilemaps[key][index] if index != None else self.tilemaps[key]
        
        return self.tilemaps[(path, 1.0)][index] if index != None else self.tilemaps[(path, 1.0)]
