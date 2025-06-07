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
    
    # placeholer for velocity
    def _clamp(self):
        pass 


class Position(Vector2Component):
    def __init__(self, x=0, y=0):
        super().__init__(x, y)

class Velocity(Vector2Component):
    def __init__(self, x=0, y=0, fixed_speed=5):
        super().__init__(x, y)
        self.fixed_speed = fixed_speed
    
    def _clamp(self):
        # If the velocity vector is zero, do nothing
        if self._vec == pygame.Vector2(0, 0):
            return
        
        # Clamp the velocity to the maximum speed
        if self._vec.length() != self.fixed_speed:
            self._vec.scale_to_length(self.fixed_speed)
        
        # threshold
        # Ensure that the velocity is not zero
        # if self._vec.length() < 0.01:
        #     self._vec = pygame.Vector2(0, 0)