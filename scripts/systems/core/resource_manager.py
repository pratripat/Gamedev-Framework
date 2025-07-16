import pygame
from ...utils import load_image, load_images_from_spritesheet, load_images_from_tilemap #, load_sound

class ResourceManager: 
    def __init__(self):
        self.images = {}       # (path, scale)
        self.spritesheets = {} # (path, scale)
        self.tilemaps = {}     # (path, scale)
        self.sound = {}
    
    def get_image(self, path, scale=1, **kwargs):
        if path not in self.images:
            image = load_image(path)
            if not (path or image):
                return None    
            
            self.images[(path, 1)] = image
        
        original_image = self.images[(path, 1)]

        if scale != 1:
            if (path, scale) not in self.images:
                self.images[(path, scale)] = pygame.transform.scale(original_image, (int(original_image.get_width() * scale), int(original_image.get_height() * scale)))
            return self.images[(path, scale)]

        return original_image
    
    def get_spritesheet(self, path, index=None, scale=1, **kwargs): 
        if path not in self.spritesheets:
            images = load_images_from_spritesheet(path)
            if not (path and len(images)):
                return None
            
            self.spritesheets[(path, 1)] = images

        if scale != 1:
            if (path, scale) not in self.spritesheets:
                self.spritesheets[(path, scale)] = [pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale))) for image in self.spritesheets[(path, 1)]]
            return self.spritesheets[(path, scale)][index] if index != None else self.spritesheets[(path, scale)]

        return self.spritesheets[(path, 1)][index] if index != None else self.spritesheets[(path, 1)]
    
    def get_tilemap(self, path, index=None, scale=1, **kwargs):
        if path and path not in self.tilemaps:
            images = load_images_from_tilemap(path)
            if not (path and len(images)):
                return None

            self.tilemaps[(path, 1)] = images

        if scale != 1:
            if (path, scale) not in self.tilemaps:
                self.tilemaps[(path, scale)] = [pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale))) for image in self.tilemaps[(path, 1)]]
            return self.tilemaps[(path, scale)][index] if index != None else self.tilemaps[(path, scale)]
        
        return self.tilemaps[(path, 1)][index] if index != None else self.tilemaps[(path, 1)]
    
    # def get_sound(self, path):
    #     if path not in self.sounds:
    #         self.sounds[path] = load_sound(path)
    #     return self.sounds[path]
