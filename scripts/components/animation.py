import pygame

class RenderComponent:
    def __init__(self, entity_id, surface, offset=(0,0), center=False):
        self.entity_id = entity_id
        self.surface = surface
        self.offset = pygame.Vector2(offset)
        
        if center:
            self.offset -= pygame.Vector2(surface.get_size()) / 2
    
class AnimationComponent:
    def __init__(self, entity_id, entity, animation_id, animation_handler, event_manager, offset=(0,0), center=False, entity_type=None):
        self.animation_handler = animation_handler
        self.event_manager = event_manager
        self.entity_id = entity_id
        self.entity_name = entity
        self.entity_type = entity_type # chess_piece, foilage
        self.offset = pygame.Vector2(offset)
        self.animation_id = None

        self.set_animation(animation_id)

        if center:
            self.offset -= pygame.Vector2(self.animation.image.get_size()) / 2

    def set_animation(self, animation_id):
        """
        Sets the current animation to the specified animation ID.
        
        :param animation_id: The ID of the animation to set.
        """
        if self.animation_id == animation_id: return

        self.animation_id = animation_id
        self.animation = self.animation_handler.get_animation(self.entity_name + "_" + animation_id)

        if self.entity_name == 'black_rook': print(self.animation.current_image.get_size())
    
    def update(self, dt):
        self.animation.run(self.event_manager, self.entity_id, dt)

    @property
    def current_image(self):
        """
        Returns the current image of the animation.
        
        :return: The current image of the animation.
        """
        return self.animation.current_image