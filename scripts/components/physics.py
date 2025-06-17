import pygame

class Vector2Component:
    def __init__(self, entity_id, x=0, y=0):
        self.entity_id = entity_id
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
    def __init__(self, entity_id, x=0, y=0):
        super().__init__(entity_id, x, y)

class Velocity(Vector2Component):
    def __init__(self, entity_id, x=0, y=0, speed=5):
        super().__init__(entity_id, x, y)
        self.speed = speed

class CollisionComponent:
    def __init__(self, entity_id, offset, size, solid=False, center=False):
        self.entity_id = entity_id
        self.offset = pygame.Vector2(offset)
        self.size = pygame.Vector2(size)
        self.solid = solid

        if center:
            self.offset -= self.size / 2