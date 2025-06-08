import pygame

class Vector2Component:
    def __init__(self, x=0, y=0):
        self._vec = pygame.Vector2(x, y)
    
    def __iadd__(self, other) -> "Vector2Component": # for vec += other
        # handling pygame.Vector2, tuple, list, and Vector2Component
        if isinstance(other, pygame.Vector2):
            self._vec += other
        elif isinstance(other, (tuple, list)):
            self._vec += pygame.Vector2(*other)
        elif isinstance(other, Vector2Component):
            self._vec += other._vec 
        
        self._clamp()

        return self

    def __sub__(self, other):
        if isinstance(other, pygame.Vector2):
            return self._vec - other
        elif isinstance(other, (tuple, list)):
            return self._vec - pygame.Vector2(*other)
        elif isinstance(other, Vector2Component):
            return self._vec - other._vec
        
        raise TypeError(f"[{self.__class__.__name__}] Unsupported type for subtraction: '{type(other)}' (DEBUG)")

    def __mul__(self, scalar): # for vec * scalar
        return self._vec * scalar
    
    def __rmul__(self, scalar): # for scalar * vec
        return self._vec * scalar
    
    def __repr__(self):
        return f"{self.__class__.__name__}: (x={self._vec.x}, y={self._vec.y})"
    
    @property
    def x(self):
        return self._vec.x

    @property
    def y(self):
        return self._vec.y
    
    @x.setter
    def x(self, value):
        self._vec.x = value
        self._clamp()

    @y.setter
    def y(self, value):
        self._vec.y = value
        self._clamp()
    
    @property
    def vec(self):
        return self._vec

    @vec.setter
    def vec(self, value):
        if isinstance(value, pygame.Vector2):
            self._vec = value
        elif isinstance(value, (tuple, list)):
            self._vec = pygame.Vector2(*value)
        elif isinstance(value, Vector2Component):
            self._vec = value._vec
        
        self._clamp()
    
    # placeholer for velocity
    def _clamp(self):
        pass 


class Position(Vector2Component):
    def __init__(self, x=0, y=0):
        super().__init__(x, y)

class Velocity(Vector2Component):
    def __init__(self, x=0, y=0, speed=5):
        super().__init__(x, y)
        self.speed = speed

class RenderComponent:
    def __init__(self, surface, offset=(0,0), center=False):
        """
        Initializes a render component with a surface and an offset.

        :param surface: The surface to render.
        :param offset: The offset from the entity's position.
        """
        self.surface = surface
        self.offset = pygame.Vector2(offset)
        
        if center:
            self.offset -= pygame.Vector2(surface.get_size()) / 2
    
class AnimationComponent:
    def __init__(self, entity, animation_id, animation_handler, offset=(0,0), center=False, entity_type=None):
        self.animation_handler = animation_handler
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

        print(self.animation_id)

        self.animation_id = animation_id
        self.animation = self.animation_handler.get_animation(self.entity_name + "_" + animation_id)
    
    def update(self, dt):
        self.animation.run(dt)

    @property
    def current_image(self):
        """
        Returns the current image of the animation.
        
        :return: The current image of the animation.
        """
        return self.animation.current_image