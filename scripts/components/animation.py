import pygame
from ..utils import normalize_scale

class RenderComponent:
    def __init__(self, entity_id, surface=None, offset=(0,0), center=False):
        self.entity_id = entity_id
        self.original_surface = self.surface = surface
        self.offset = pygame.Vector2(offset)
        
        if surface is None:
            self.surface = pygame.Surface((32,32))
            self.surface.fill("white")

        if center:
            self.offset -= pygame.Vector2(self.surface.get_size()) / 2
        
    def resize_scale(self, scale):
        scale = normalize_scale(scale)

        if scale[0] == 1 and scale[1] == 1:
            return
        new_size = (
            int(self.original_surface.get_width() * scale[0]),
            int(self.original_surface.get_height() * scale[1])
        )

        self.surface = pygame.transform.scale(self.original_surface, new_size)

class AnimationComponent:
    def __init__(self, entity_id, entity, animation_id, animation_handler, event_manager, offset=(0,0), center=False, entity_type=None):
        self.animation_handler = animation_handler
        self.event_manager = event_manager
        self.entity_id = entity_id
        self.entity_name = entity
        self.entity_type = entity_type # chess_piece, foilage
        self.offset = pygame.Vector2(offset)
        self.center = center
        self.animation_id = None

        self.set_animation(animation_id)

        if center:
            # self.offset -= pygame.Vector2(self.animation.image.get_size()) / 2
            self.animation.set_center(True)

    def set_animation(self, animation_id):
        """
        Sets the current animation to the specified animation ID.
        
        :param animation_id: The ID of the animation to set.
        """
        if self.animation_id == animation_id: return

        self.animation_id = animation_id
        self.animation = self.animation_handler.get_animation(self.entity_name + "_" + animation_id)
        if self.center:
            self.animation.set_center(True)
    
    def update(self, dt):
        self.animation.run(self.event_manager, self.entity_id, dt)
    
    def resize_scale(self, scale):
        self.animation.change_scale(scale)

    @property
    def current_image(self):
        """
        Returns the current image of the animation.
        
        :return: The current image of the animation.
        """
        return self.animation.current_image