import math
import random
import pygame
from ...components.destructible import DestructibleComponent
from ...components.physics import Position, CollisionComponent
from ...components.render_effect import YSortRender
from ...components.combat import HitBoxComponent
from ...components.projectile import ProjectileComponent
from ...utils import CollisionShape

class DestructibleSystem:
    def __init__(self, component_manager, entity_manager):
        self.component_manager = component_manager
        self.entity_manager = entity_manager
        self.projectile_system = None
        self.particle_system = None

    def update(self, dt, player_id):
        col_dict = self.component_manager._components.get(CollisionComponent, {})
        pos_dict = self.component_manager._components.get(Position, {})
        hitbox_dict = self.component_manager._components.get(HitBoxComponent, {})
        proj_dict = self.component_manager._components.get(ProjectileComponent, {})

        p_col = col_dict.get(player_id)
        p_pos = pos_dict.get(player_id)
        p_rect = None
        if p_col and p_pos:
            p_rect = pygame.Rect(*(p_pos.vec + p_col.offset), *p_col.size)

        projectiles = []
        if self.projectile_system:
            for pool_idx in self.projectile_system.active_indices:
                p = self.projectile_system.pool[pool_idx]
                if p.active:
                    pr = p.size / 2
                    projectiles.append((p, pool_idx, pygame.Rect(p.x - pr, p.y - pr, p.size, p.size)))

        for eid in list(self.component_manager.get_entities_with(DestructibleComponent)):
            if eid not in self.component_manager._components.get(DestructibleComponent, {}):
                continue
            dc = self.component_manager.get(eid, DestructibleComponent)
            pos = pos_dict.get(eid)
            col = col_dict.get(eid)
            if not dc or not pos:
                continue

            if not dc.shattered:
                destroyed = False

                if col and p_rect:
                    d_rect = pygame.Rect(*(pos.vec + col.offset), *col.size)
                    if d_rect.colliderect(p_rect):
                        dc.shatter(pos.x, pos.y, 15.0)
                        destroyed = True

                if not destroyed and col:
                    d_rect = pygame.Rect(*(pos.vec + col.offset), *col.size)
                    for p, pool_idx, pr in projectiles:
                        if pr.colliderect(d_rect):
                            dc.shatter(pos.x, pos.y, 60.0)
                            if self.particle_system:
                                for _ in range(3):
                                    self.particle_system.emit_fast_particle(
                                        x=pos.x + random.uniform(-8, 8),
                                        y=pos.y + random.uniform(-8, 8),
                                        vx=random.uniform(-40, 40), vy=random.uniform(-60, -20),
                                        lifetime=random.uniform(0.3, 0.6),
                                        r=random.randint(100, 180), g=random.randint(80, 140), b=random.randint(60, 100), a=255,
                                        size=random.uniform(1.5, 3.5),
                                        fade=True, shrink=True, friction=0.9,
                                        gravity=120
                                    )
                            destroyed = True
                            break

                if not destroyed and col:
                    d_rect = pygame.Rect(*(pos.vec + col.offset), *col.size)
                    for hb_eid, hb in hitbox_dict.items():
                        if hb.disabled: continue
                        if hb_eid not in proj_dict: continue
                        if hb.shape != CollisionShape.CIRCLE: continue
                        hb_pos = pos_dict.get(hb_eid)
                        if not hb_pos: continue
                        cx = hb_pos.x + hb.offset.x + hb.size[0] / 2
                        cy = hb_pos.y + hb.offset.y + hb.size[1] / 2
                        r = hb.size[0] / 2
                        closest_x = max(d_rect.left, min(cx, d_rect.right))
                        closest_y = max(d_rect.top, min(cy, d_rect.bottom))
                        dx = cx - closest_x
                        dy = cy - closest_y
                        if dx*dx + dy*dy <= r*r:
                            dc.shatter(pos.x, pos.y, 80.0)
                            destroyed = True
                            break
            else:
                alive = dc.update_shards(dt)
                if not alive:
                    self.entity_manager.delete_entity(eid)

    def collect_shard_items(self, camera, screen_rect):
        scroll = camera.scroll_int
        if not hasattr(self, '_shard_items'):
            self._shard_items = []
        items = self._shard_items
        items.clear()
        for eid in self.component_manager.get_entities_with(DestructibleComponent):
            dc = self.component_manager.get(eid, DestructibleComponent)
            pos = self.component_manager.get(eid, Position)
            if not dc or not pos or not dc.shattered:
                continue
            ysort = self.component_manager.get(eid, YSortRender)
            sort_y = int(pos.y) + (ysort.offset[1] if ysort else 0)
            for shard in dc.shards:
                if shard.alpha <= 0:
                    continue
                sx = int(pos.x + shard.x - shard.w / 2 - scroll.x)
                sy = int(pos.y + shard.y - shard.h / 2 - scroll.y)
                if not screen_rect.inflate(32, 32).collidepoint(sx, sy):
                    continue
                if shard.alpha < 255 or shard.rotation != 0:
                    surf = shard.surface.copy()
                    surf.set_alpha(shard.alpha)
                    if shard.rotation != 0:
                        surf = pygame.transform.rotate(surf, shard.rotation)
                else:
                    surf = shard.surface
                items.append((sort_y, "sprite", surf, (sx, sy)))
        return items
