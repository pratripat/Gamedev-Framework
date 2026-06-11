import math
import pygame
import random

class WindSystem:
    def __init__(self):
        self.time = 0.0
        self.magnitude_x = 0.0

    def update(self, dt):
        self.time += dt
        # Wind magnitude fluctuates between -1.0 and 1.0
        self.magnitude_x = math.sin(self.time * 0.5) * 0.7 + math.sin(self.time * 1.2) * 0.3

    def generate_sway_frames(self, base_surf: pygame.Surface, num_frames=24, amplitude=5, **kwargs):
        """
        Generates more frames at slower speeds for a smooth swaying effect.
        """
        w, h = base_surf.get_size()
        frames = []
        
        # Color palette definitions
        LIGHT_GREEN = (99, 199, 77)
        MEDIUM_GREEN = (62, 137, 72)
        
        # 1. Identify Light Green Clumps (Top Surface)
        light_mask = pygame.mask.from_threshold(base_surf, LIGHT_GREEN, (30, 30, 30))
        light_clumps = sorted(light_mask.connected_components(), key=lambda m: m.count(), reverse=True)[:3]
        
        # 2. Identify Medium Green Clumps (Deeper Layers)
        medium_mask = pygame.mask.from_threshold(base_surf, MEDIUM_GREEN, (30, 30, 30))
        medium_clumps = sorted(medium_mask.connected_components(), key=lambda m: m.count(), reverse=True)[:3]
        
        if not light_clumps and not medium_clumps:
            return [base_surf.copy() for _ in range(num_frames)]

        rng = random.Random(id(base_surf))
        all_clump_data = []

        # Process Light Clumps (Surface - Slower)
        for m in light_clumps:
            clump_img = m.to_surface(setcolor=(255,255,255,255), unsetcolor=(0,0,0,0))
            clump_img.blit(base_surf, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
            
            rect = m.get_bounding_rects()[0]
            for r in m.get_bounding_rects()[1:]: rect.union_ip(r)

            all_clump_data.append({
                'img': clump_img,
                'phase': rng.uniform(0, math.pi * 2),
                'speed': rng.uniform(1.2, 1.8), # Reduced speed
                'amp_mult': 1.0,
                'center_y': rect.centery
            })

        # Process Medium Clumps (Deeper - Even Slower)
        for m in medium_clumps:
            clump_img = m.to_surface(setcolor=(255,255,255,255), unsetcolor=(0,0,0,0))
            clump_img.blit(base_surf, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
            
            rect = m.get_bounding_rects()[0]
            for r in m.get_bounding_rects()[1:]: rect.union_ip(r)

            all_clump_data.append({
                'img': clump_img,
                'phase': rng.uniform(0, math.pi * 2),
                'speed': rng.uniform(0.5, 0.9), # Reduced speed
                'amp_mult': 0.4,
                'center_y': rect.centery
            })

        for f in range(num_frames):
            t = (f / num_frames) * 2 * math.pi
            final_surf = base_surf.copy()
            
            for data in all_clump_data:
                # Basic height pinning
                hf = (1.0 - (data['center_y'] / h)) ** 1.5
                
                # Apply combined mults
                clump_amp = amplitude * data['amp_mult'] * hf
                
                dx = math.sin(t * data['speed'] + data['phase']) * clump_amp
                dy = math.cos(t * data['speed'] * 0.7 + data['phase']) * (clump_amp * 0.3)
                
                final_surf.blit(data['img'], (dx, dy))
            
            frames.append(final_surf)
            
        return frames
