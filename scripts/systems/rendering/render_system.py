import pygame, math
from ...utils import CENTER, INITIAL_WINDOW_SIZE, VIRTUAL_WINDOW_SIZE

from ...components.physics import Position, Velocity
from ...components.animation import RenderComponent, AnimationComponent
from ...components.render_effect import RenderEffectComponent, YSortRender, ShadowComponent, WindAffectedComponent, PulseComponent

from .wind_system import WindSystem
from ..animation.animation_state_machine import AnimationStateMachine
from .render_effect_system import RenderEffectSystem
from .particle_effect_system import ParticleEffectSystem
from .proximity_fade_system import ProximityFadeSystem

class RenderSystem:
    def __init__(self, event_manager, component_manager, entity_manager, resource_manager, surface_size=VIRTUAL_WINDOW_SIZE):
        self.component_manager = component_manager
        self.render_effect_system = RenderEffectSystem(event_manager, component_manager)
        self.particle_effect_system = ParticleEffectSystem(component_manager, entity_manager)
        self.proximity_fade_system = ProximityFadeSystem(component_manager)

        self.wind_system = WindSystem()
        self.particle_effect_system.wind_system = self.wind_system
        self._pulse_cache = {}
        self._sprite_transform_cache = {}

    def update(self, dt, tilemap=None, camera=None, quadtree=None):
        self.render_effect_system.update(dt)
        self.particle_effect_system.update(dt, quadtree=None, camera_rect=camera.rect if camera else None) 
        self.proximity_fade_system.update()
        self.wind_system.update(dt)
        
        for eid in self.component_manager.get_entities_with(PulseComponent):
            pulse = self.component_manager.get(eid, PulseComponent)
            pulse.time += dt
    
    def render(self, surface, tilemap, camera):
        # Draw directly to virtual surface to avoid buffer issues
        scroll = camera.scroll_int
        screen_rect = surface.get_rect()

        surface.fill((0, 0, 0))

        # 1. Base Ground
        tilemap.render(surface, camera)

        # 2. Y-Sorting Queue
        ysort_queue = []
        
        # Batch objects
        ysort_queue.extend(self.particle_effect_system.collect_render_items(camera))
        if hasattr(self, 'combat_system') and self.combat_system:
            ysort_queue.extend(self.combat_system.projectile_system.collect_render_items(camera))
        ysort_queue.extend(tilemap.get_ysort_items(camera.rect))

        # Entities
        for eid in self.component_manager.get_entities_with(Position):
            pos = self.component_manager.get(eid, Position)
            sx, sy = int(pos.x - scroll.x), int(pos.y - scroll.y)

            # Cull
            if not screen_rect.inflate(256, 256).collidepoint(sx, sy):
                continue

            render = self.component_manager.get(eid, RenderComponent)
            anim = self.component_manager.get(eid, AnimationComponent)
            rec = self.component_manager.get(eid, RenderEffectComponent)
            ysort = self.component_manager.get(eid, YSortRender)
            shadow = self.component_manager.get(eid, ShadowComponent)
            pulse = self.component_manager.get(eid, PulseComponent)

            # Effects
            if rec and not rec.disabled:
                scale, tint, alpha, rotation, z_off = rec.scale, rec.tint, rec.alpha, rec.rotation, rec.z_offset
            else:
                scale, tint, alpha, rotation, z_off = None, None, None, 0.0, 0.0

            sort_y = int(pos.y) + (ysort.offset[1] if ysort else 0)

            # Pulse
            if pulse:
                p_val = (math.sin(pulse.time * pulse.speed) + 1) / 2
                dr = int(pulse.radius * (0.8 + 0.4 * p_val))
                if dr > 0:
                    surface.blit(self._get_pulse_surf(pulse, dr), (sx - dr, sy - dr))

            # Shadow
            if shadow:
                s_pos = (sx + int(shadow.offset[0]), sy + int(shadow.offset[1]))
                ysort_queue.append((sort_y, "shadow", shadow.surface, s_pos, shadow.alpha))

            if render:
                cached = self._get_transformed_sprite(render.surface, scale, tint, alpha, rotation)
                d_pos = (sx + int(render.offset.x), sy + int(render.offset.y - z_off))
                ysort_queue.append((sort_y, "sprite", cached, d_pos))

            if anim:
                a_pos = (sx + int(anim.offset.x), sy + int(anim.offset.y - z_off))
                ysort_queue.append((sort_y, "animation", anim, a_pos, scale, tint, alpha, rotation))

        # 3. Sort and Flush
        ysort_queue.sort(key=lambda x: x[0])
        batch = []
        def flush():
            if batch: surface.blits(batch); batch.clear()
        
        for item in ysort_queue:
            itype = item[1]
            if itype == "tile":
                batch.append((item[2], (int(item[3][0]-scroll.x), int(item[3][1]-scroll.y))))
            elif itype in ["shadow", "sprite"]:
                batch.append((item[2], item[3]))
            elif itype == "animation":
                flush()
                item[2].animation.render(surface, item[3], scale=item[4], tint=item[5], alpha=item[6], angle=item[7], offset=pygame.Vector2(0,0))
        flush()

    def _get_pulse_surf(self, pulse, dr):
        ck = (pulse.color[0], pulse.color[1], pulse.color[2], pulse.alpha, dr)
        surf = self._pulse_cache.get(ck)
        if not surf:
            surf = pygame.Surface((dr*2, dr*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*pulse.color, pulse.alpha), (dr, dr), dr)
            self._pulse_cache[ck] = surf
        return surf

    def _get_transformed_sprite(self, surf, scale, tint, alpha, rotation):
        ckey = (id(surf), tuple(scale) if scale else (1,1), tint, alpha, rotation)
        cached = self._sprite_transform_cache.get(ckey)
        if not cached:
            res = surf
            if rotation: res = pygame.transform.rotate(res, rotation)
            if scale and (scale.x != 1 or scale.y != 1):
                res = pygame.transform.scale(res, (int(res.get_width()*scale.x), int(res.get_height()*scale.y)))
            if tint:
                mask = pygame.mask.from_surface(res)
                res = mask.to_surface(setcolor=tint, unsetcolor=(0,0,0,0))
            if alpha:
                res = res.copy(); res.set_alpha(alpha)
            cached = res
            self._sprite_transform_cache[ckey] = cached
        return cached

class AnimationSystem:
    def __init__(self, component_manager):
        self.component_manager = component_manager
    
    def update(self, fps, dt, camera_rect=None):
        for eid in self.component_manager.get_entities_with(AnimationStateMachine):
            asm = self.component_manager.get(eid, AnimationStateMachine)
            if asm.animation_component.entity_type == "chess_piece":
                vel_comp = self.component_manager._components.get(Velocity, {}).get(eid)
                if vel_comp:
                    suggested = "moving" if vel_comp.vec.length_squared() > 0 else "idle"
                    asm.set_animation(suggested)
        
        for eid in self.component_manager.get_entities_with(AnimationComponent, Position):
            if camera_rect:
                pos = self.component_manager.get(eid, Position)
                if not camera_rect.inflate(200, 200).collidepoint(pos.x, pos.y):
                    continue
            self.component_manager.get(eid, AnimationComponent).update(fps, dt)
