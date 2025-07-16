import pygame, json, os
from enum import Enum, IntFlag, auto
from dataclasses import dataclass

DEFAULT_COLORKEY = (0, 0, 0)
INITIAL_WINDOW_SIZE = (1920, 1002) # (1280, 720)
CENTER = pygame.Vector2(INITIAL_WINDOW_SIZE) * 0.5
ANIMATION_FOLDER = "data/graphics/animations"
SCALE = 2

# Define keybinds for player inputs
class Inputs(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    UP_RELEASE = "up_release"
    DOWN_RELEASE = "down_release"
    LEFT_RELEASE = "left_release"
    RIGHT_RELEASE = "right_release"
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    LEFT_HOLD = "left_hold"
    RIGHT_HOLD = "right_hold"

class CollisionShape(Enum):
    RECT = "rect"
    CIRCLE = "circle"

class CollisionLayer(IntFlag):
    PLAYER = 1
    ENEMY = 2
    PROJECTILE = 4
    ENVIRONMENT = 8
    ALL = PLAYER | ENEMY | PROJECTILE | ENVIRONMENT

    @staticmethod
    def create_mask(*layers):
        """
        Combines multiple CollisionLayer values into a single bitmask.
        """
        mask = CollisionLayer(0)
        for layer in layers:
            mask |= layer
        return mask

class GameSceneEvents(Enum):
    DAMAGE = "damage"
    DEATH = "death"
    SHOOT = "shoot"
    REMOVE_ENTITY = "remove_entity"
    ANIMATION_FINISHED = "animation_finished"
    COLLISION = "collision"

class EnemyState(Enum):
    IDLE = auto()
    PATROL = auto()
    CHASE = auto()
    ATTACK = auto()
    FLEE = auto()
    DEAD = auto()

class EmitterShapeType(Enum):
    POINT = "point"
    RECT = "rect"
    CIRCLE = "circle"

@dataclass
class EmitterShape:
    type: EmitterShapeType
    rect: pygame.Rect = None  # for RECT
    radius: float = 0.0       # for CIRCLE

class Quadtree:
    MAX_OBJECTS = 4
    MAX_LEVELS = 5
    def __init__(self, level, bounds):
        self.level = level
        self.bounds = bounds
        self.objects = []
        self.nodes = [None] * 4 # Four quadrants

    def clear(self):
        self.objects.clear()
        for i in range(4):
            if self.nodes[i]:
                self.nodes[i].clear()
                self.nodes[i] = None
    
    def split(self):
        x, y, w, h = self.bounds
        half_w = w / 2
        half_h = h / 2

        self.nodes[0] = Quadtree(self.level + 1, (x + half_w, y, half_w, half_h))  # Top-right
        self.nodes[1] = Quadtree(self.level + 1, (x, y, half_w, half_h))          # Top-left
        self.nodes[2] = Quadtree(self.level + 1, (x, y + half_h, half_w, half_h))  # Bottom-left
        self.nodes[3] = Quadtree(self.level + 1, (x + half_w, y + half_h, half_w, half_h))  # Bottom-right

    def get_index(self, rect):
        indexes = []
        x, y, w, h = self.bounds
        vertical_mid = x + w / 2
        horizontal_mid = y + h / 2

        top = rect.y < horizontal_mid
        bottom = rect.y + rect.height > horizontal_mid
        left = rect.x < vertical_mid
        right = rect.x + rect.width > vertical_mid

        if top and right: indexes.append(0)
        if top and left: indexes.append(1)
        if bottom and left: indexes.append(2)
        if bottom and right: indexes.append(3)

        return indexes


    def insert(self, entity_id, rect):
        if self.nodes[0] is not None:
            for i in self.get_index(rect):
                self.nodes[i].insert(entity_id, rect)
            return
        
        self.objects.append((entity_id, rect))

        if len(self.objects) > self.MAX_OBJECTS and self.level < self.MAX_LEVELS:
            if self.nodes[0] is None:
                self.split()
            
            for obj in self.objects:
                for i in self.get_index(obj[1]):
                    self.nodes[i].insert(*obj)
            self.objects.clear()
    
    def retrieve(self, return_list: list, rect: pygame.Rect):
        for i in self.get_index(rect):
            if self.nodes[i]:
                self.nodes[i].retrieve(return_list, rect)
        
        for object in self.objects:
            if object not in return_list:
                return_list.append(object)

def normalize_scale(scale):
    if isinstance(scale, (int, float)):
        return [scale, scale]
    elif isinstance(scale, pygame.Vector2):
        return [scale.x, scale.y]
    elif isinstance(scale, (list, tuple)) and len(scale) == 2:
        return list(scale)
    else:
        return [1, 1]  # default safe fallback
    
def circle_rect_collision(component, component_rect, rect):
    center = component_rect.center
    radius = component.size[0] / 2
    radius_sq = radius ** 2

    # Find the closest point on the rect to the circle's center
    closest_x = max(rect.left, min(center[0], rect.right))
    closest_y = max(rect.top, min(center[1], rect.bottom))

    # Compute the distance between the circle's center and this closest point
    dx = center[0] - closest_x
    dy = center[1] - closest_y

    # If the distance is less than or equal to the radius, they collide
    return (dx * dx + dy * dy) <= radius_sq

def circle_circle_collision(comp1, comp1_rect, comp2, comp2_rect):
    center1 = comp1_rect.center
    center2 = comp2_rect.center

    radius1 = comp1.size[0] / 2
    radius2 = comp2.size[0] / 2

    dx = center1[0] - center2[0]
    dy = center1[1] - center2[1]

    return (dx * dx + dy * dy) <= (radius1 + radius2) ** 2

def collision_occured(hitbox, hitbox_rect, hurtbox, hurtbox_rect):
    if hitbox.shape == CollisionShape.RECT and hurtbox.shape == CollisionShape.RECT:
        return hitbox_rect.colliderect(hurtbox_rect)
    elif hitbox.shape == CollisionShape.RECT and hurtbox.shape == CollisionShape.CIRCLE:
        return circle_rect_collision(hurtbox, hurtbox_rect, hitbox_rect)
    elif hitbox.shape == CollisionShape.CIRCLE and hurtbox.shape == CollisionShape.RECT:
        return circle_rect_collision(hitbox, hitbox_rect, hurtbox_rect)
    else:
        return circle_circle_collision(hitbox, hitbox_rect, hurtbox, hurtbox_rect)

# loads an image from a file and applies a colorkey for transparency
def load_image(path, colorkey=DEFAULT_COLORKEY, scale=1):
    """
    Load an image from a file and apply a colorkey for transparency.
    
    :param path: Path to the image file.
    :param colorkey: Color to be treated as transparent.
    :param scale: Scale factor for the image.
    :return: Scaled image with colorkey applied.
    """
    if not os.path.exists(path):
        # raise FileNotFoundError(f"[UTILS] Image file '{path}' does not exist. (DEBUG)")
        print(f"[UTILS] Image file '{path}' does not exist. (DEBUG)")
        return None
    
    image = pygame.image.load(path).convert()
    image.set_colorkey(colorkey)
    
    if scale != 1:
        width, height = image.get_size()
        image = pygame.transform.scale(image, (width * scale, height * scale))
    
    return image

def load_images_from_spritesheet(file_path, colorkey=DEFAULT_COLORKEY, scale=1):
    """
    Load images from a spritesheet file, extracting individual images based on color markers.
    The spritesheet is expected to have specific color markers to define the start and end of images.
    :param file_path: Path to the spritesheet file.
    :param colorkey: Color to be treated as transparent for the images.
    :param scale: Scale factor for the images.
    :return: List of images extracted from the spritesheet.
    """
    # Tries to load the file
    try:
        spritesheet = load_image(file_path, colorkey, scale)
    except Exception as e:
        print(f"[UTILS] Error loading spritesheet '{file_path}': {e} (DEBUG)")
        return []

    rows = []
    images = []

    for y in range(spritesheet.get_height()):
        pixil = spritesheet.get_at((0, y))
        if pixil[2] == 255:
            rows.append(y)

    for row in rows:
        for x in range(spritesheet.get_width()):
            start_position = []
            pixil = spritesheet.get_at((x, row))
            if pixil[0] == 255 and pixil[1] == 255 and pixil[2] == 0:
                start_position = [x+1, row]
                width = height = 0

                for rel_x in range(start_position[0], spritesheet.get_width()):
                    pixil = spritesheet.get_at((rel_x, start_position[1]))
                    if pixil[0] == 255 and pixil[1] == 0 and pixil[2] == 255:
                        width = rel_x - start_position[0]
                        break

                for rel_y in range(start_position[1], spritesheet.get_height()):
                    pixil = spritesheet.get_at((start_position[0], rel_y))
                    if pixil[0] == 255 and pixil[1] == 0 and pixil[2] == 255:
                        height = rel_y - start_position[1]
                        break

                image = pygame.Surface((width, height))
                image.set_colorkey(colorkey)
                image.blit(spritesheet, (-start_position[0], -start_position[1]))
                image.convert()

                if scale != 1:
                    image = pygame.transform.scale(image, (image.get_width()*scale, image.get_height()*scale))

                images.append(image)

    return images

def load_images_from_tilemap(filename, tile_size=32, skip_empty=True):
    """
    Load tile images from a spritesheet, optionally skipping empty tiles.

    :param filepath: Path to the spritesheet image.
    :param tile_size: Width and height of each tile (assumes square tiles).
    :param skip_empty: Whether to skip fully transparent or empty tiles.
    :return: List of Pygame Surfaces, one per non-empty tile.
    """
    spritesheet = pygame.image.load(filename).convert()
    sheet_width, sheet_height = spritesheet.get_size()

    tiles = []
    for y in range(0, sheet_height, tile_size):
        for x in range(0, sheet_width, tile_size):
            tile = pygame.Surface((tile_size, tile_size))
            tile.set_colorkey((0,0,0))
            tile.blit(spritesheet, (0, 0), (x, y, tile_size, tile_size))

            if skip_empty:
                # Check if the tile is completely transparent
                if not pygame.mask.from_surface(tile).count():
                    continue

            tiles.append(tile)

    return tiles

def get_unit_direction_towards(start_pos: pygame.Vector2, end_pos: pygame.Vector2):
    """
    Returns the unit direction vector from start_pos to end_pos.
    
    :param start_pos: Starting position (tuple, list, or pygame.Vector2).
    :param end_pos: Target position (tuple, list, or pygame.Vector2).
    :return: pygame.Vector2 representing the unit direction.
    """
    direction = end_pos - start_pos
    if direction.length() == 0:
        return pygame.Vector2(0, 0)
    return direction.normalize()

def rotate_vector(vector, angle):
    """
    Rotates a vector by a given angle in degrees.

    :param vector: The vector to rotate (tuple, list, or pygame.Vector2).
    :param angle: The angle in degrees to rotate the vector (counter-clockwise).
    :return: A new pygame.Vector2 representing the rotated vector.
    """
    return pygame.Vector2(vector).rotate(angle)