import pygame
import math
import os

# Try to use numpy for faster generation; provide fallback if numpy not available.
try:
    import numpy as np
    _HAS_NUMPY = True
except Exception:
    _HAS_NUMPY = False

# Always use the pure-Pygame generator to preserve alpha and avoid surfarray alpha issues.
# The pure generator is used at load-time and is reliable; numpy path caused alpha/artifacts.

def _generate_water_frames_pure(base_surf: pygame.Surface, num_frames=8, amplitude=2, slice_h=1):
    """
    Pure-Pygame generator that shifts horizontal strips to create a looping wavering effect.
    Preserves per-pixel alpha. slice_h controls strip height (1 = per-row).
    """
    frames = []
    w, h = base_surf.get_size()
    for f in range(num_frames):
        t = f / num_frames
        surf = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()
        y = 0
        while y < h:
            sh = min(slice_h, h - y)
            phase = 2 * math.pi * (t + (y / h) * 0.5)
            off = int(round(math.sin(phase) * amplitude))
            slice_surf = pygame.Surface((w, sh), pygame.SRCALPHA).convert_alpha()
            slice_surf.blit(base_surf, (0, -y))
            surf.blit(slice_surf, (off, y))
            y += sh
        frames.append(surf)
    return frames

# Public interface
def generate_water_frames(base_surf: pygame.Surface, num_frames=8, amplitude=2, slice_h=1):
    return _generate_water_frames_pure(base_surf, num_frames=num_frames, amplitude=amplitude, slice_h=slice_h)


# Tileable sinusoidal (Perlin-like) generator
def generate_tileable_noise_frames(size=128, num_frames=8, octaves=4, base_color=(31,142,255), intensity=0.6, seed=42):
    """
    Generate a tileable looping noise animation using a sum of sinusoids (fast, inherently tileable).
    Returns list[pygame.Surface] of shape (size,size).
    Parameters:
    - size: output width and height in pixels
    - num_frames: number of frames in loop
    - octaves: number of sinusoid layers (higher -> more detail)
    - base_color: RGB tuple for the water base
    - intensity: how strong the highlights are (0..1)
    - seed: RNG seed for deterministic variants
    """
    w = h = size

    # Prefer numpy path for speed
    if _HAS_NUMPY:
        rng = np.random.RandomState(seed)
        # coordinate grid [0,1)
        x = np.linspace(0, 1, w, endpoint=False)
        y = np.linspace(0, 1, h, endpoint=False)
        xv, yv = np.meshgrid(x, y)

        # Precompute octave parameters
        freqs = [2 ** (i + 1) for i in range(octaves)]
        amps = [0.5 ** i for i in range(octaves)]
        angles = rng.rand(octaves) * 2 * np.pi
        phases = rng.rand(octaves) * 2 * np.pi

        frames = []
        for f in range(num_frames):
            t = f / num_frames
            val = np.zeros((h, w), dtype=float)
            for i, (freq, amp) in enumerate(zip(freqs, amps)):
                angle = angles[i]
                dx = np.cos(angle)
                dy = np.sin(angle)
                # move phase slowly over frames for animation
                phase = phases[i] + 2 * np.pi * t * (0.2 + 0.8 * (i / max(1, octaves - 1)))
                # dot product grid and direction, multiplied by freq
                arg = freq * (dx * xv + dy * yv) + phase
                val += amp * np.sin(2 * np.pi * arg)

            # normalize to 0..1
            mn = val.min()
            mx = val.max()
            if mx - mn < 1e-9:
                norm = np.zeros_like(val)
            else:
                norm = (val - mn) / (mx - mn)

            # enhance contrast a bit
            norm = norm ** 1.2

            # colorize: blend base_color with white highlights driven by norm
            base = np.array(base_color, dtype=float).reshape(1, 1, 3)
            white = np.array([255, 255, 255], dtype=float).reshape(1, 1, 3)
            brightness = (norm * intensity)[..., None]
            rgb = base * (1 - brightness) + white * brightness

            # convert to surface: pygame.surfarray requires shape (w,h,3)
            arr = np.clip(rgb, 0, 255).astype(np.uint8)
            arr_swap = np.swapaxes(arr, 0, 1)  # (w,h,3)
            surf = pygame.surfarray.make_surface(arr_swap)
            surf = surf.convert_alpha()
            # Ensure fully opaque alpha so it's easy to composite later
            surf = surf.convert()
            frames.append(surf)

        return frames

    # Fallback Python-only path (slower)
    import math
    rng = __import__('random')
    rng.seed(seed)
    angles = [rng.random() * 2 * math.pi for _ in range(octaves)]
    phases = [rng.random() * 2 * math.pi for _ in range(octaves)]
    freqs = [2 ** (i + 1) for i in range(octaves)]
    amps = [0.5 ** i for i in range(octaves)]

    frames = []
    for f in range(num_frames):
        t = f / num_frames
        surf = pygame.Surface((w, h))
        for yy in range(h):
            for xx in range(w):
                x = xx / w
                y = yy / h
                val = 0.0
                for i, (freq, amp) in enumerate(zip(freqs, amps)):
                    angle = angles[i]
                    dx = math.cos(angle)
                    dy = math.sin(angle)
                    phase = phases[i] + 2 * math.pi * t * (0.2 + 0.8 * (i / max(1, octaves - 1)))
                    arg = freq * (dx * x + dy * y) + phase
                    val += amp * math.sin(2 * math.pi * arg)
                # normalize approximation
                b = (val + 1) * 0.5
                b = pow(max(0.0, min(1.0, b)), 1.2) * intensity
                r = int(base_color[0] * (1 - b) + 255 * b)
                g = int(base_color[1] * (1 - b) + 255 * b)
                bl = int(base_color[2] * (1 - b) + 255 * b)
                surf.set_at((xx, yy), (r, g, bl))
        frames.append(surf.convert())
    return frames


def load_water_frames(directory: str, scale=1.0):
    """
    Load water animation frames (frame_000.png, ...) from a directory.
    """
    if not os.path.exists(directory):
        return None
    
    files = sorted([f for f in os.listdir(directory) if f.startswith('frame_') and f.endswith('.png')])
    if not files:
        return None
    
    frames = []
    for f in files:
        path = os.path.join(directory, f)
        surf = pygame.image.load(path).convert()
        if scale != 1.0:
            w, h = surf.get_size()
            surf = pygame.transform.scale(surf, (int(w * scale), int(h * scale)))
        frames.append(surf)
    return frames


# Tileable Worley (cellular) noise generator
def generate_tileable_worley_frames(size=32, num_frames=8, cells=4, jitter=0.75, base_color=(30,140,220), highlight_color=(255,255,255), intensity=0.7, seed=0, mode='negative'):
    """
    Generate tileable looping Worley (cellular) noise frames.
    - size: pixel width/height
    - cells: number of feature cells per axis
    - jitter: amount of random offset within cell (0..1)
    - mode: 'positive' (bright cells), 'negative' (dark cells), 'difference' (F2-F1)
    """
    w = h = size
    # create grid coordinates normalized 0..1
    xs = np.linspace(0, 1, w, endpoint=False) if _HAS_NUMPY else [i / w for i in range(w)]
    ys = np.linspace(0, 1, h, endpoint=False) if _HAS_NUMPY else [i / h for i in range(h)]

    if _HAS_NUMPY:
        xv, yv = np.meshgrid(xs, ys)
        rng = np.random.RandomState(seed)
        # feature points per cell
        fx = np.zeros((cells*cells,))
        fy = np.zeros((cells*cells,))
        idx = 0
        base_pos = []
        for iy in range(cells):
            for ix in range(cells):
                # base cell center
                bx = (ix + 0.5) / cells
                by = (iy + 0.5) / cells
                base_pos.append((bx, by))
        base_pos = np.array(base_pos)

        # Random angle & radius for smooth looping motion per feature
        angles = rng.rand(len(base_pos)) * 2 * np.pi
        radii = (rng.rand(len(base_pos)) * 0.5 + 0.5) * (jitter / cells)

        frames = []
        for f in range(num_frames):
            t = f / num_frames
            # compute dynamic positions
            px = base_pos[:,0] + radii * np.cos(angles + 2*np.pi*t)
            py = base_pos[:,1] + radii * np.sin(angles + 2*np.pi*t)
            # wrap into [0,1)
            px = px % 1.0
            py = py % 1.0

            # compute toroidal distance from each pixel to each feature
            # shapes: px (F,), xv (H,W) -> dx shape (F,H,W)
            dx = np.abs(xv[None, :, :] - px[:, None, None])
            dx = np.minimum(dx, 1.0 - dx)
            dy = np.abs(yv[None, :, :] - py[:, None, None])
            dy = np.minimum(dy, 1.0 - dy)
            dist = np.sqrt(dx * dx + dy * dy)
            # nearest feature distance
            # also compute second-nearest when needed
            max_possible = np.sqrt(2) / cells
            if mode == 'difference':
                # get two smallest distances per pixel
                part = np.partition(dist, 1, axis=0)
                f1 = part[0]
                f2 = part[1]
                diff = np.clip((f2 - f1) / max_possible, 0.0, 1.0)
                val = diff ** 1.3
            else:
                nearest = dist.min(axis=0)
                # normalize: distances range roughly 0..(sqrt(2)/(cells)) ; scale accordingly
                norm = np.clip(nearest / max_possible, 0.0, 1.0)
                if mode == 'positive':
                    # centers bright
                    val = (1.0 - norm) ** 1.3
                else:
                    # 'negative' or any other -> centers dark (inverted)
                    val = (norm) ** 1.3

            # colorize
            base = np.array(base_color, dtype=float).reshape(1,1,3)
            high = np.array(highlight_color, dtype=float).reshape(1,1,3)
            brightness = (val * intensity)[..., None]
            rgb = base * (1 - brightness) + high * brightness
            arr = np.clip(rgb, 0, 255).astype(np.uint8)
            arr_swap = np.swapaxes(arr, 0, 1)
            surf = pygame.surfarray.make_surface(arr_swap)
            frames.append(surf.convert())
        return frames
    else:
        # Python fallback: brute force
        import math, random
        rng = random.Random(seed)
        base_pos = []
        for iy in range(cells):
            for ix in range(cells):
                bx = (ix + 0.5) / cells
                by = (iy + 0.5) / cells
                base_pos.append((bx, by))
        angles = [rng.random() * 2 * math.pi for _ in base_pos]
        radii = [ (rng.random() * 0.5 + 0.5) * (jitter / cells) for _ in base_pos]

        frames = []
        for f in range(num_frames):
            t = f / num_frames
            surf = pygame.Surface((w,h))
            for y in range(h):
                for x in range(w):
                    nx = x / w
                    ny = y / h
                    nearest = 1e9
                    for (bx,by), ang, rad in zip(base_pos, angles, radii):
                        px = (bx + rad * math.cos(ang + 2*math.pi*t)) % 1.0
                        py = (by + rad * math.sin(ang + 2*math.pi*t)) % 1.0
                        dx = abs(nx - px)
                        if dx > 0.5: dx = 1.0 - dx
                        dy = abs(ny - py)
                        if dy > 0.5: dy = 1.0 - dy
                        d = math.hypot(dx, dy)
                        if d < nearest: nearest = d
                    max_possible = math.sqrt(2) / cells
                    norm = max(0.0, min(1.0, nearest / max_possible))
                    if mode == 'difference':
                        # compute second nearest distance (slow fallback)
                        # brute force find second smallest
                        sec = 1e9
                        for (bx2,by2), ang2, rad2 in zip(base_pos, angles, radii):
                            px2 = (bx2 + rad2 * math.cos(ang2 + 2*math.pi*t)) % 1.0
                            py2 = (by2 + rad2 * math.sin(ang2 + 2*math.pi*t)) % 1.0
                            dx2 = abs(nx - px2)
                            if dx2 > 0.5: dx2 = 1.0 - dx2
                            dy2 = abs(ny - py2)
                            if dy2 > 0.5: dy2 = 1.0 - dy2
                            d2 = math.hypot(dx2, dy2)
                            if d2 < sec and d2 > nearest: sec = d2
                        diff = max(0.0, min(1.0, (sec - nearest) / max_possible))
                        v = diff ** 1.3
                    else:
                        if mode == 'positive':
                            v = (1.0 - norm) ** 1.3
                        else:
                            v = (norm) ** 1.3
                    b = v * intensity
                    r = int(base_color[0] * (1 - b) + highlight_color[0] * b)
                    g = int(base_color[1] * (1 - b) + highlight_color[1] * b)
                    bl = int(base_color[2] * (1 - b) + highlight_color[2] * b)
                    surf.set_at((x,y),(r,g,bl))
            frames.append(surf.convert())
        return frames
