import pygame
import os
from ...utils import load_image, load_images_from_spritesheet, load_images_from_tilemap, SCALE #, load_sound

class ResourceManager: 
    def __init__(self):
        self.images = {}       # (path, effective_scale)
        self.spritesheets = {} # (path, effective_scale)
        self.tilemaps = {}     # (path, effective_scale)
        self.sound = {}
    
    def get_image(self, path, scale=1, **kwargs):
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

        if path not in self.images:
            image = load_image(path)
            if not (path or image):
                return None    
            # store original unscaled under key (path, 1)
            self.images[(path, 1)] = image
        
        original_image = self.images[(path, 1)]

        # If effective_scale == 1*SCALE and SCALE==1 then this will be original
        if effective_scale != 1:
            key = (path, effective_scale)
            if key not in self.images:
                self.images[key] = pygame.transform.scale(
                    original_image,
                    (int(original_image.get_width() * effective_scale), int(original_image.get_height() * effective_scale))
                )
            return self.images[key]

        return original_image
    
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
            images = load_images_from_tilemap(path)
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
