import math, pygame
from ...utils import TILE_SIZE
from ...components.physics import Position, CollisionComponent

class CollisionGrid:
    def __init__(self, walls, tile_size=TILE_SIZE):
        self.grid = []
        self.offset = (0, 0)
        self.tile_size = tile_size

        self.fill_grid(walls)

    def fill_grid(self, walls):
        positions = []
        min_pos = pygame.math.Vector2([math.inf, math.inf])
        max_pos = pygame.math.Vector2([-math.inf, -math.inf])
        
        for wall in walls:
            pos = wall[0]

            min_pos.x = min(min_pos.x, pos[0])
            min_pos.y = min(min_pos.y, pos[1])
            max_pos.x = max(max_pos.x, pos[0])
            max_pos.y = max(max_pos.y, pos[1])

            pos = pygame.math.Vector2(pos)

            positions.append(pos)
        
        positions = [pos - min_pos for pos in positions]
        max_pos -= min_pos

        self.grid = [[0 for _ in range(math.ceil(max_pos.x // self.tile_size)+1)] for _ in range(math.ceil(max_pos.y // self.tile_size)+1)]

        for pos in positions:
            self.grid[math.ceil(pos[1] // self.tile_size)][math.ceil(pos[0] // self.tile_size)] = 1

        self.offset = min_pos

    def merge_collision_grids(self):
        rows = len(self.grid)
        cols = len(self.grid[0]) if rows > 0 else 0

        visited = [[False for _ in range(cols)] for _ in range(rows)]
        rects = []

        for y in range(rows):
            for x in range(cols):
                if self.grid[y][x] == 1 and not visited[y][x]:
                    # Start a new rectangle
                    width = 0
                    while x + width < cols and self.grid[y][x + width] == 1 and not visited[y][x + width]:
                        width += 1
                    
                    height = 1
                    done = False
                    while not done and (y + height) < rows:
                        for dx in range(width):
                            if self.grid[y + height][x + dx] != 1 or visited[y + height][x + dx]:
                                done = True
                                break
                        
                        if not done:
                            height += 1
                    
                    # Mark the rectangle as visited
                    for dy in range(height):
                        for dx in range(width):
                            visited[y + dy][x + dx] = True
                        
                    
                    # Create the rectangle
                    rect = pygame.Rect(
                        x * self.tile_size,
                        y * self.tile_size,
                        width * self.tile_size,
                        height * self.tile_size                        
                    )

                    rects.append(rect)
        
        return rects
    
    def create_collision_boxes(self, entity_manager, component_manager):
        collision_rects = self.merge_collision_grids()

        for rect in collision_rects:    
            entity_id = entity_manager.create_entity()
            component_manager.add(
                entity_id,
                Position(
                    entity_id=entity_id,
                    x=self.offset.x + rect.x + rect.width // 2,
                    y=self.offset.y + rect.y + rect.height // 2
                ),
                CollisionComponent(
                    entity_id=entity_id,
                    offset=(0, 0),
                    size=(rect.width, rect.height),
                    solid=True,
                    center=True
                )
            )

            # print("[COLLISION_GRID] Created collision box:", rect, "for entity", entity_id)