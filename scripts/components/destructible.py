import pygame, random, math

class Shard:
    __slots__ = ['surface', 'ox', 'oy', 'x', 'y', 'vx', 'vy', 'rotation', 'rot_speed', 'alpha', 'lifetime', 'max_lifetime', 'w', 'h']

    def __init__(self, surface, ox, oy, w, h):
        self.surface = surface
        self.ox = ox
        self.oy = oy
        self.x = ox
        self.y = oy
        self.vx = 0.0
        self.vy = 0.0
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-200, 200)
        self.alpha = 255
        self.lifetime = random.uniform(0.5, 1.2)
        self.max_lifetime = self.lifetime
        self.w = w
        self.h = h

class DestructibleComponent:
    def __init__(self, texture):
        self.shattered = False
        self.shards = []
        self.texture = texture
        self.shatter_timer = 0.0
        self.total_duration = 1.5

    def shatter(self, origin_x, origin_y, impulse_power):
        w, h = self.texture.get_size()
        pieces = [pygame.Rect(0, 0, w, h)]
        target_pieces = random.randint(6, 12)
        for _ in range(target_pieces - 1):
            if not pieces:
                break
            idx = random.randint(0, len(pieces) - 1)
            rect = pieces.pop(idx)
            if rect.w > rect.h and rect.w > 10:
                split_x = random.randint(5, rect.w - 5)
                r1 = pygame.Rect(rect.x, rect.y, split_x, rect.h)
                r2 = pygame.Rect(rect.x + split_x, rect.y, rect.w - split_x, rect.h)
                pieces.extend([r1, r2])
            elif rect.h > 10:
                split_y = random.randint(5, rect.h - 5)
                r1 = pygame.Rect(rect.x, rect.y, rect.w, split_y)
                r2 = pygame.Rect(rect.x, rect.y + split_y, rect.w, rect.h - split_y)
                pieces.extend([r1, r2])
            else:
                pieces.append(rect)

        self.shards = []
        for rect in pieces:
            sub = self.texture.subsurface(rect).copy()
            cx = rect.x + rect.w / 2 - w / 2
            cy = rect.y + rect.h / 2 - h / 2
            shard = Shard(sub, cx, cy, rect.w, rect.h)
            angle = math.atan2(cy, cx)
            spread = random.uniform(0.5, 1.5)
            shard.vx = math.cos(angle + random.uniform(-0.5, 0.5)) * impulse_power * spread
            shard.vy = math.sin(angle + random.uniform(-0.5, 0.5)) * impulse_power * spread - impulse_power * 0.5
            shard.rot_speed += random.uniform(-50, 50) * (impulse_power / 30)
            self.shards.append(shard)

        self.shattered = True
        self.shatter_timer = self.total_duration

    def update_shards(self, dt):
        if not self.shattered:
            return True
        self.shatter_timer -= dt
        any_alive = False
        for shard in self.shards:
            if shard.lifetime <= 0:
                continue
            any_alive = True
            shard.vy += 120.0 * dt
            shard.vx *= 0.98
            shard.x += shard.vx * dt
            shard.y += shard.vy * dt
            shard.rotation += shard.rot_speed * dt
            elapsed = 1.0 - (shard.lifetime / shard.max_lifetime)
            if elapsed > 0.3:
                shard.alpha = max(0, int(255 * (1.0 - (elapsed - 0.3) / 0.7)))
            shard.lifetime -= dt
        return any_alive
