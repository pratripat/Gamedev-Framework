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
        effective_scale = scale * SCALE

        # Handle potential absolute paths from level data by making them relative to project root
        if path and os.path.isabs(path):
            if not os.path.exists(path):
                # Try to find 'data/' in the path and use that as relative
                if 'data/' in path:
                    path = path[path.find('data/'):]
                else:
                    # Just take the filename as a last resort? No, better to use the relative part
                    path = os.path.basename(path)

        # Cache key includes color_swap if provided
        key_base = (path, effective_scale)
        if color_swap:
            key = (path, effective_scale, tuple(color_swap))
        else:
            key = key_base

        if key in self.images:
            return self.images[key]

        # If not in cache, load or get from base cache
        if (path, 1) not in self.images:
            image = load_image(path)
            if not (path or image):
                return None    
            # store original unscaled under key (path, 1)
            self.images[(path, 1)] = image
        
        original_image = self.images[(path, 1)]

        # Determine the base scaled image (without color swap yet)
        if effective_scale != 1:
            if key_base not in self.images:
                self.images[key_base] = pygame.transform.scale(
                    original_image,
                    (int(original_image.get_width() * effective_scale), int(original_image.get_height() * effective_scale))
                )
            base_scaled = self.images[key_base]
        else:
            base_scaled = original_image

        # Apply color swap if requested
        if color_swap:
            # Blue colors to replace in projectile.png
            PROJECTILE_BLUES = [
                (18, 78, 137),  # Dark Blue
                (0, 153, 219),  # Medium Blue
                (44, 232, 245)   # Cyan Blue
            ]
            self.images[key] = swap_color(base_scaled, PROJECTILE_BLUES, color_swap)
            return self.images[key]

        return base_scaled
    
    def get_spritesheet(self, path, index=None, scale=1, **kwargs): 
        effective_scale = scale * SCALE

        # Handle potential absolute paths
        if path and os.path.isabs(path):
            if not os.path.exists(path):
                if 'data/' in path:
                    path = path[path.find('data/'):]
                else:
                    path = os.path.basename(path)

        if path not in self.spritesheets:
            images = load_images_from_spritesheet(path)
            if not (path and len(images)):
                return None
            
            self.spritesheets[(path, 1)] = images

        if effective_scale != 1:
            key = (path, effective_scale)
            if key not in self.spritesheets:
                self.spritesheets[key] = [
                    pygame.transform.scale(image, (int(image.get_width() * effective_scale), int(image.get_height() * effective_scale)))
                    for image in self.spritesheets[(path, 1)]
                ]
            return self.spritesheets[key][index] if index != None else self.spritesheets[key]

        return self.spritesheets[(path, 1)][index] if index != None else self.spritesheets[(path, 1)]
    
    def get_tilemap(self, path, index=None, scale=1, **kwargs):
        effective_scale = scale * SCALE

        # Handle potential absolute paths
        if path and os.path.isabs(path):
            if not os.path.exists(path):
                if 'data/' in path:
                    path = path[path.find('data/'):]
                else:
                    path = os.path.basename(path)

        if path and path not in self.tilemaps:
            from ...utils import TILE_SIZE
            images = load_images_from_tilemap(path, tile_size=TILE_SIZE)
            if not (path and len(images)):
                return None

            self.tilemaps[(path, 1)] = images

        if effective_scale != 1:
            key = (path, effective_scale)
            if key not in self.tilemaps:
                self.tilemaps[key] = [
                    pygame.transform.scale(image, (int(image.get_width() * effective_scale), int(image.get_height() * effective_scale)))
                    for image in self.tilemaps[(path, 1)]
                ]
            return self.tilemaps[key][index] if index != None else self.tilemaps[key]
        
        return self.tilemaps[(path, 1)][index] if index != None else self.tilemaps[(path, 1)]
    
    # def get_sound(self, path):
    #     if path not in self.sounds:
    #         self.sounds[path] = load_sound(path)
    #     return self.sounds[path]
