import math
import numpy as np
import pygame

class WindSystem:
    def __init__(self):
        self.time = 0.0
        self.frame_count = 12

    def update(self, dt):
        self.time += dt

    def get_phase(self, pos_x, pos_y):
        phase = (pos_x * 0.01 + pos_y * 0.007)
        return self.time * 2.0 + phase

    def get_sway_offset(self, pos_x, pos_y) -> float:
        """Returns horizontal pixel offset for foliage sway (deprecated).
        Prefer using precomputed sway frames for visuals.
        """
        return math.sin(self.get_phase(pos_x, pos_y)) * 3.0

def generate_sway_frames(base_surf: pygame.Surface, num_frames=12, amplitude=3, slice_h=4):
    """
    Generate a small number of pre-distorted frames for a foliage surface.
    Each frame is created by slicing the surface into horizontal strips and shifting each strip by a small offset
    derived from a smooth sinusoidal phase. This creates a shader-like sway without moving the whole sprite.
    """
    w, h = base_surf.get_size()
    frames = []
    base_arr = None
    # Work on surfaces directly via blits to preserve colorkey/alpha
    for f in range(num_frames):
        t = f / num_frames
        surf = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()
        # For each horizontal slice
        y = 0
        while y < h:
            sh = min(slice_h, h - y)
            # compute offset for this slice: use sin with slightly varying phase so different rows move differently
            phase = 2 * math.pi * (t + y / h * 0.5)
            offset = int(round(math.sin(phase) * amplitude * (1 - (y / h))))  # less movement near bottom
            rect = pygame.Rect(0, y, w, sh)
            slice_surf = pygame.Surface((w, sh), pygame.SRCALPHA).convert_alpha()
            slice_surf.blit(base_surf, (0, -y))
            # blit shifted
            surf.blit(slice_surf, (offset, y))
            y += sh
        frames.append(surf)
    return frames
