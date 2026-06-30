import pygame
import math
import random
from ...utils import TILE_SIZE

# Use the exact colors provided in grass_manager.py
COLORS = [(25,60,62), (38,92,66), (62,137,72), (172,234,92)]

def load_grass_images(filename):
    """
    Dedicated loader for the grass spritesheet to prevent breaking standard engine assets.
    This safely uses the row+1 logic required by the grass spritesheet's specific marker format.
    """
    try:
        spritesheet = pygame.image.load(filename)
    except:
        print('[GRASS] file not found...')
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
                start_position = [x+1, row+1] # Custom row+1 offset for grass
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
                image.set_colorkey((0,0,0))
                image.blit(spritesheet, (-start_position[0], -start_position[1]))
                images.append(image)

    return images

def edit_grass_image(image, scale, color, flip):
    """Exact tinting logic from grass_manager.py"""
    image = image.copy()
    image.set_colorkey((255,255,255))
    image = pygame.transform.flip(image, flip, False)
    
    surface = pygame.Surface(image.get_size()).convert()
    surface.fill(color)
    surface.blit(image, (0,0))
    surface.set_colorkey((0,0,0))

    final_surface = pygame.transform.scale(surface, (int(surface.get_width()*scale), int(surface.get_height()*scale)))
    final_surface = final_surface.convert()
    final_surface.set_colorkey((0,0,0)) # Re-apply colorkey after convert!
    return final_surface


class FastGrassBlade:
    __slots__ = ['x', 'y', 'image', 'scale', 'color', 'angle', 'target_angle', 'angle_offset']
    def __init__(self, x, y, image, scale, color, angle_offset):
        self.x = x
        self.y = y
        self.image = image
        self.scale = scale
        self.color = color
        self.angle = 0.0
        self.target_angle = 0.0
        self.angle_offset = angle_offset

class GrassSystem:
    def __init__(self):
        self.blades = []
        self.grass_images = load_grass_images('data/graphics/spritesheets/grass_spritesheet.png')
        if not self.grass_images:
            print("[GRASS] Warning: No grass images loaded.")
        self._render_cache = {}

    def update(self, dt, interactors, wind_mag=0.0, wind_time=0.0, camera_rect=None):
        """
        Updates grass blade physics and handles interactivity with entities/projectiles.
        interactors: list of (x, y, radius, force_multiplier)
        """
        # dt-scaled factor (assuming 60fps base)
        # Slower LERP for smoother, more stable movement
        lerp_factor = 2.0 * 80 * dt
        
        # Inflate camera rect for culling to avoid snapping when scrolling
        update_rect = camera_rect.inflate(128, 128) if camera_rect else None
        
        for blade in self.blades:
            # Spatial Culling: Skip physics and wind updates if far off-screen
            if update_rect and not update_rect.collidepoint(blade.x, blade.y):
                continue
                
            # Reset target_angle every frame to find the "strongest" current push
            max_bend = 0.0
            
            # Collision with interactors
            for ix, iy, irad, iforce in interactors:
                dy = iy - blade.y
                if abs(dy) < 32: # Max height check
                    dx = ix - blade.x
                    dist_sq = dx*dx + dy*dy
                    if dist_sq < irad*irad:
                        # Determine bend strength based on distance (closer = more bend)
                        # This creates a stable "push" instead of a vibrating force
                        dist = math.sqrt(dist_sq)
                        strength = (1.0 - (dist / irad)) * iforce
                        
                        # Bend AWAY from interactor
                        current_push = 70.0 * strength
                        if dx < 0:
                            current_push = -current_push
                        
                        # Keep the strongest push as our target
                        if abs(current_push) > abs(max_bend):
                            max_bend = current_push

            # Calculate Wind Effect
            # Add a phase based on world position so it ripples across the field
            wind_phase = blade.x * 0.01 + blade.y * 0.005
            
            # Base wind sway (up to ~20 degrees)
            wind_sway = wind_mag * 20.0 
            
            # High-frequency ripple for more natural flutter
            wind_ripple = math.sin(wind_time * 2.5 + wind_phase) * 6.0 * abs(wind_mag)
            
            wind_bend = wind_sway + wind_ripple

            # Blend forces: strong physical pushes override wind
            if abs(max_bend) > 10.0:
                blade.target_angle = max_bend
            else:
                # Smoothly blend back to wind if the push is weak/gone
                blade.target_angle = wind_bend
            
            # Smoothly transition current angle to the target
            blade.angle += (blade.target_angle - blade.angle) / 4.0 * lerp_factor

            # Clamp final angle
            blade.angle = max(min(blade.angle, 80), -80)

    def collect_render_items(self, camera):
        scroll_x, scroll_y = camera.scroll_int.x, camera.scroll_int.y
        items = []
        # Pad culling rect slightly to avoid pop-in at screen edges
        screen_rect = camera.rect.inflate(64, 64)
        
        for blade in self.blades:
            # 1. Frustum Culling
            if not screen_rect.collidepoint(blade.x, blade.y):
                continue
            
            # 2. Base angle (quantized to nearest 2 degrees for massive cache hit improvements)
            angle_int = int(round((blade.angle + blade.angle_offset) / 2.0) * 2.0)
            
            # 3. Rotation Caching
            cache_key = (id(blade.image), angle_int)
            surf = self._render_cache.get(cache_key)
            if surf is None:
                surf = pygame.transform.rotate(blade.image, angle_int)
                if len(self._render_cache) > 500:
                    self._render_cache.clear()
                self._render_cache[cache_key] = surf
            
            # 4. Y-Sort Formatting: (sort_y, "sprite", surface, screen_position)
            # Center the image around blade.x, blade.y (pivot is the center)
            draw_x = blade.x - (surf.get_width() / 2) - scroll_x
            draw_y = blade.y - (surf.get_height() / 2) - scroll_y
            
            # Sort by blade.y, which is the base/pivot point
            items.append((blade.y, "sprite", surf, (int(draw_x), int(draw_y))))
            
        return items

    def generate_grass(self, layers):
        """Generates grass data structures in clumps, strictly avoiding ANY occupied tiles."""
        grass_layer = layers.get("grass")
        if not grass_layer or not self.grass_images:
            return

        # 1. Build sets for fast tile-type lookups
        blocked_positions = set()
        grass_positions = set()
        
        for lid, layer_data in layers.items():
            is_grass_layer = "grass" in lid.lower()
            
            # Handle tilemap chunked dict format
            if isinstance(layer_data, dict):
                for chunk_tiles in layer_data.values():
                    for tpos in chunk_tiles.keys():
                        itpos = (int(tpos[0]), int(tpos[1]))
                        if is_grass_layer:
                            grass_positions.add(itpos)
                        else:
                            blocked_positions.add(itpos)
            # Handle raw list format (entities)
            elif isinstance(layer_data, list):
                for t in layer_data:
                    if t and isinstance(t[0], (list, tuple)):
                        itpos = (int(t[0][0]), int(t[0][1]))
                        if is_grass_layer:
                            grass_positions.add(itpos)
                        else:
                            blocked_positions.add(itpos)

        # --- Perlin Noise Implementation ---
        # Deterministic permutation table for coherent noise
        perm = [151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,140,36,103,30,69,142,8,99,37,240,21,10,
                23,190, 6,148,247,120,234,75,0,26,197,62,94,252,219,203,117,35,11,32,57,177,33,88,237,149,56,
                87,174,20,125,136,171,168, 68,175,74,165,71,134,139,48,27,166,77,146,158,231,83,111,229,122,
                60,211,133,230,220,105,92,41,55,46,245,40,244,102,143,54, 65,25,63,161, 1,216,80,73,209,76,
                132,187,208, 89,18,169,200,196,135,130,116,188,159,86,164,100,109,198,173,186, 3,64,52,217,226,
                250,124,123,5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,162,215,171,180,72,1,95,94,
                150,224,154,152,50,205,78,196,155,167,110,178,0,99,24,129,22,249,113,47,39,242,1,228,121,58,
                163,222,21,120,108,12,159,101,100,145,150,115,114,61,75,107,210,131,128,127,10,109,10,19,42,
                177,18,229,228,111,123,213,2,11,108,219,106,178,185,11,225,23,54,102,161,212,57,118,31,152,
                115,31,159]
        perm += perm # Double to avoid overflow

        def fade(t):
            return t * t * t * (t * (t * 6 - 15) + 10)

        def lerp(t, a, b):
            return a + t * (b - a)

        def grad(hash, x, y):
            h = hash & 15
            u = x if h < 8 else y
            v = y if h < 4 else (x if h == 12 or h == 14 else 0)
            return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)

        def perlin_noise(x, y):
            # Coordinates in unit square
            X = int(math.floor(x)) & 255
            Y = int(math.floor(y)) & 255
            x -= math.floor(x)
            y -= math.floor(y)
            # Fade curves
            u = fade(x)
            v = fade(y)
            # Hash coordinates
            A = perm[X] + Y
            AA = perm[A]
            AB = perm[A+1]
            B = perm[X+1] + Y
            BA = perm[B]
            BB = perm[B+1]
            # Lerp final value
            return lerp(v, lerp(u, grad(perm[AA], x, y), grad(perm[BA], x-1, y)),
                           lerp(u, grad(perm[AB], x, y-1), grad(perm[BB], x-1, y-1)))

        self.blades.clear()

        # Scale for Perlin noise (lower = larger clumps)
        noise_scale = 0.15

        # Commented out previous sine-based noise
        # def clump_noise(x, y):
        #     # Using abs(sin*cos) for islands and sin*sin for organic variation
        #     # This mimics the range of the old noise function without the linear waves
        #     v1 = abs(math.sin(x * 1.5) * math.cos(y * 1.5))
        #     v2 = math.sin(x * 0.8) * math.sin(y * 0.5)
        #     return (v1 + v2) / 2.0

        for chunk_pos, tiles in grass_layer.items():
            for tpos_tuple in tiles.keys():
                itpos = (int(tpos_tuple[0]), int(tpos_tuple[1]))
                
                # Pre-check: If this specific tile is blocked by a wall/water, skip it entirely
                if itpos in blocked_positions:
                    continue
                
                tx, ty = itpos[0] // TILE_SIZE, itpos[1] // TILE_SIZE
                
                # Use Perlin noise instead
                # Normalize from [-1, 1] to [0, 1]
                noise_val = (perlin_noise(tx * noise_scale, ty * noise_scale) + 1.0) / 2.0
                
                # Increased threshold (0.5) for fewer clumps to improve performance
                if noise_val > 0.6:
                    # Clean density (15) as requested
                    density = int((noise_val + 0.2) * 15) 

                    # Use a local RNG for stability without global side effects
                    rng = random.Random(itpos[0] * 1000 + itpos[1])
                    
                    for _ in range(density):
                        # Pick a random position within the tile
                        # This point (bx, by) is the base/pivot of the blade
                        bx = itpos[0] + rng.uniform(0, TILE_SIZE)
                        by = itpos[1] + rng.uniform(0, TILE_SIZE)
                        
                        source_image = rng.choice(self.grass_images)
                        scale = 2.0 * rng.uniform(0.7, 1.0) 
                        color = rng.choice(COLORS)
                        flip = rng.choice([True, False])
                        
                        # Apply transformation
                        final_img = edit_grass_image(source_image, scale, color, flip)
                        
                        # Random idle offset
                        angle_offset = rng.uniform(-10, 10)
                        
                        # CRITICAL CHECK: Ensure the base of the blade is on a valid grass tile
                        # and NOT overlapping a blocked tile (water/wall).
                        check_x = int(bx // TILE_SIZE) * TILE_SIZE
                        check_y = int(by // TILE_SIZE) * TILE_SIZE
                        base_tile_pos = (check_x, check_y)
                        
                        if base_tile_pos in blocked_positions or base_tile_pos not in grass_positions:
                            continue
                        
                        self.blades.append(FastGrassBlade(bx, by, final_img, scale, color, angle_offset))
        
        print(f"[GRASS SYSTEM] Generation Complete. Spawned {len(self.blades)} grass blades in organic clumps.")
