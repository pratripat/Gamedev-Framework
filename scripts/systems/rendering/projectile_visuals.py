import pygame

_circle_cache = {}
_glow_cache = {}

def _circle(r, color):
    key = (r, tuple(color))
    s = _circle_cache.get(key)
    if s is None:
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (r, r), r)
        _circle_cache[key] = s
    return s

def _glow(r, color):
    key = (r, tuple(color))
    s = _glow_cache.get(key)
    if s is None:
        s = _circle(r, color).copy()
        blur_surf = pygame.transform.smoothscale(s, (r*2+8, r*2+8))
        s = pygame.transform.smoothscale(blur_surf, (r*2, r*2))
        s.fill((*color, 120), None, pygame.BLEND_RGBA_MULT)
        _glow_cache[key] = s
    return s

def build_standard(base_size, color):
    s = pygame.Surface((base_size, base_size), pygame.SRCALPHA)
    r = base_size // 2
    pygame.draw.circle(s, (255, 255, 255), (r, r), r)
    pygame.draw.circle(s, color, (r, r), r - 1)
    return s

def build_heavy(base_size, color):
    s = pygame.Surface((base_size + 4, base_size + 4), pygame.SRCALPHA)
    r = (base_size + 4) // 2
    glow = _glow(r, color)
    s.blit(glow, (2, 2))
    pygame.draw.circle(s, (255, 255, 255), (r, r), r - 2)
    pygame.draw.circle(s, color, (r, r), r - 3)
    return s

def build_homing(base_size, color):
    s = pygame.Surface((base_size + 4, base_size + 8), pygame.SRCALPHA)
    cx, cy = (base_size + 4) // 2, (base_size + 8) // 2
    r = base_size // 3
    # Eye shape: two overlapping circles with a pupil
    pygame.draw.circle(s, color, (cx - r, cy), r)
    pygame.draw.circle(s, color, (cx + r, cy), r)
    # pupil
    pygame.draw.circle(s, (255, 255, 255), (cx, cy), r // 2)
    pygame.draw.circle(s, (0, 0, 0), (cx, cy), r // 3)
    # small tail flick
    pts = [(cx - r*2, cy), (cx - r*3, cy - 2), (cx - r*3, cy + 2)]
    pygame.draw.polygon(s, color, pts)
    return s

def build_curve(base_size, color):
    s = pygame.Surface((base_size + 6, base_size + 4), pygame.SRCALPHA)
    cx, cy = (base_size + 6) // 2, (base_size + 4) // 2
    r = base_size // 2
    # Crescent / boomerang silhouette
    pygame.draw.circle(s, color, (cx, cy), r)
    # cut out inner circle offset to make crescent
    cut_color = (0, 0, 0, 0)
    pygame.draw.circle(s, cut_color, (cx - r//2, cy - r//4), r)
    # outline
    pygame.draw.circle(s, (255, 255, 255), (cx, cy), r, 1)
    return s

def build_accel(base_size, color):
    s = pygame.Surface((base_size + 8, base_size + 4), pygame.SRCALPHA)
    cx, cy = (base_size + 8) // 2, (base_size + 4) // 2
    r = base_size // 2
    # stretched oval (like a teardrop or bullet shape)
    pygame.draw.ellipse(s, color, (2, cy - r, base_size + 4, r * 2))
    pygame.draw.ellipse(s, (255, 255, 255), (2, cy - r, base_size + 4, r * 2), 1)
    # tip
    pts = [(base_size + 4, cy), (base_size + 8, cy - 2), (base_size + 8, cy + 2)]
    pygame.draw.polygon(s, color, pts)
    return s

def build_delayed(base_size, color):
    s = pygame.Surface((base_size + 4, base_size + 4), pygame.SRCALPHA)
    r = (base_size + 4) // 2
    # Hollow circle with pulsing core
    pygame.draw.circle(s, color, (r, r), r, 2)
    pygame.draw.circle(s, (255, 255, 255), (r, r), r // 3)
    # cross hairs inside
    pygame.draw.line(s, color, (r - r//2, r), (r + r//2, r), 1)
    pygame.draw.line(s, color, (r, r - r//2), (r, r + r//2), 1)
    return s

def build_split(base_size, color):
    s = pygame.Surface((base_size + 4, base_size + 4), pygame.SRCALPHA)
    r = (base_size + 4) // 2
    # cracked core
    pygame.draw.circle(s, color, (r, r), r)
    # cracks
    for angle in [0, 60, 120, 180, 240, 300]:
        rad = angle * 3.14159 / 180
        ex = r + int(r * 0.6 * pygame.math.Vector2(1, 0).rotate(angle).x)
        ey = r + int(r * 0.6 * pygame.math.Vector2(1, 0).rotate(angle).y)
        pygame.draw.line(s, (255, 255, 255), (r, r), (ex, ey), 1)
    # bright center
    pygame.draw.circle(s, (255, 255, 200), (r, r), r // 3)
    return s

def build_mine(base_size, color):
    s = pygame.Surface((base_size + 6, base_size + 6), pygame.SRCALPHA)
    r = (base_size + 6) // 2
    # Spiked circle (hazard look)
    pygame.draw.circle(s, color, (r, r), r)
    # spikes around the edge
    for angle in range(0, 360, 30):
        rad = angle * 3.14159 / 180
        cos_a = pygame.math.Vector2(1, 0).rotate(angle).x
        sin_a = pygame.math.Vector2(1, 0).rotate(angle).y
        x1 = r + int((r - 2) * cos_a)
        y1 = r + int((r - 2) * sin_a)
        x2 = r + int((r + 4) * cos_a)
        y2 = r + int((r + 4) * sin_a)
        pygame.draw.line(s, (255, 255, 255), (x1, y1), (x2, y2), 2)
    # center dot
    pygame.draw.circle(s, (255, 255, 200), (r, r), 3)
    return s

def build_orbit(base_size, color):
    s = pygame.Surface((base_size + 8, base_size + 8), pygame.SRCALPHA)
    cx, cy = (base_size + 8) // 2, (base_size + 8) // 2
    r = base_size // 3
    # Ring with orbiting balls
    pygame.draw.circle(s, color, (cx, cy), r + 2, 2)
    pygame.draw.circle(s, (255, 255, 255), (cx + r + 2, cy), 2)
    pygame.draw.circle(s, (255, 255, 255), (cx - r - 2, cy), 2)
    pygame.draw.circle(s, color, (cx, cy), 3)
    return s

BUILDERS = {
    "standard": build_standard,
    "heavy": build_heavy,
    "homing": build_homing,
    "curve": build_curve,
    "accel": build_accel,
    "delayed": build_delayed,
    "split": build_split,
    "mine": build_mine,
    "orbit": build_orbit,
}

def get_projectile_sprite(visual_type, size, color):
    builder = BUILDERS.get(visual_type, build_standard)
    base = max(int(size * 0.6), 6)
    return builder(base, color)
