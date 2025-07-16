import pygame
from ...utils import CENTER, INITIAL_WINDOW_SIZE

from ...components.physics import Position, Velocity
from ...components.animation import RenderComponent, AnimationComponent
from ...components.render_effect import RenderEffectComponent, YSortRender

from ..animation.animation_state_machine import AnimationStateMachine
from .render_effect_system import RenderEffectSystem
from .particle_effect_system import ParticleEffectSystem

class AnimationSystem:
    def __init__(self, component_manager):
        self.component_manager = component_manager
    
    def update(self, fps, dt):
        for eid in self.component_manager.get_entities_with(AnimationStateMachine):
            animation_state_machine = self.component_manager.get(eid, AnimationStateMachine)

            if animation_state_machine.animation_component.entity_type == "chess_piece":
                vel = self.component_manager.get(eid, Velocity).vec
                is_moving = vel.x != 0 or vel.y != 0
                
                suggested_anim = "moving" if is_moving else "idle"

                animation_state_machine.set_animation(suggested_anim)
        
        for eid in self.component_manager.get_entities_with(AnimationComponent):
            animation_comp = self.component_manager.get(eid, AnimationComponent)

            animation_comp.update(fps, dt)

class RenderSystem:
    def __init__(self, event_manager, component_manager, entity_manager, surface_size=INITIAL_WINDOW_SIZE):
        self.component_manager = component_manager

        self.render_effect_system = RenderEffectSystem(event_manager, component_manager)
        self.particle_effect_system = ParticleEffectSystem(component_manager, entity_manager)

        self.temp_surf = pygame.Surface(surface_size).convert_alpha()

    def update(self, dt):
        self.render_effect_system.update(dt)
        self.particle_effect_system.update(dt)
    
    def render(self, surface, tilemap, camera):
        self.temp_surf.fill((0, 0, 0))

        scroll = camera.scroll
        temp_surf_offset = pygame.Vector2(0, 0)
        screen_rect = self.temp_surf.get_rect()

        # Queues
        normal_queue = []
        ysort_queue = []

        # Render tilemap
        tilemap.render(self.temp_surf, camera)

        for eid in self.component_manager.get_entities_with(Position):
            pos = self.component_manager.get(eid, Position)
            world_pos = pygame.Vector2(pos.x, pos.y)
            screen_pos = world_pos - scroll

            # Components
            render = self.component_manager.get(eid, RenderComponent)
            anim = self.component_manager.get(eid, AnimationComponent)
            rec = self.component_manager.get(eid, RenderEffectComponent)
            ysort = self.component_manager.get(eid, YSortRender)

            # Skip entities with no visible component
            if render is None and anim is None:
                continue

            # Effects
            scale = rec.scale if rec and not rec.disabled else None
            tint = rec.tint if rec and not rec.disabled else None

            # Sprite render
            if render:
                surf = render.surface
                offset = render.offset.copy()

                if scale and (scale[0] != 1 or scale[1] != 1):
                    offset[0] *= scale[0]
                    offset[1] *= scale[1]
                    surf = pygame.transform.scale(surf, (
                        int(surf.get_width() * scale[0]),
                        int(surf.get_height() * scale[1])
                    ))

                if tint:
                    surf = surf.copy()
                    tint_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                    tint_surf.fill(tint)
                    surf.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                draw_pos = screen_pos + offset
                if screen_rect.colliderect(pygame.Rect(draw_pos, surf.get_size())):
                    if ysort:
                        sort_y = world_pos.y + ysort.offset[1]
                        ysort_queue.append((sort_y, surf, draw_pos))
                    else:
                        normal_queue.append((surf, draw_pos))

            # Animation render
            if anim:
                anim_pos = screen_pos + anim.offset
                if screen_rect.collidepoint(anim_pos):
                    if ysort:
                        sort_y = world_pos.y + ysort.offset[1]
                        ysort_queue.append((sort_y, anim, anim_pos, True, scale, tint))
                    else:
                        normal_queue.append((anim, anim_pos, True, scale, tint))

        # Sort and draw ysort
        ysort_queue.sort(key=lambda item: item[0])
        for item in ysort_queue:
            if len(item) == 3:  # sprite
                _, surf, pos = item
                self.temp_surf.blit(surf, pos)
            else:  # animation
                _, anim, pos, _, scale, tint = item
                anim.animation.render(self.temp_surf, pos, scale=scale, tint=tint)

        # Draw normal
        for item in normal_queue:
            if len(item) == 2:  # sprite
                surf, pos = item
                self.temp_surf.blit(surf, pos)
            else:  # animation
                anim, pos, _, scale, tint = item
                anim.animation.render(self.temp_surf, pos, scale=scale, tint=tint)

        # Particle effects
        self.particle_effect_system.render(self.temp_surf, scroll=scroll)

        # Apply camera zoom
        if camera.zoom != 1:
            self.temp_surf = pygame.transform.scale(
                self.temp_surf,
                (int(surface.get_width() * camera.zoom), int(surface.get_height() * camera.zoom))
            )
            temp_surf_offset = pygame.Vector2(surface.get_width() / 2, surface.get_height() / 2) - pygame.Vector2(
                self.temp_surf.get_size()
            ) / 2

        surface.blit(self.temp_surf, temp_surf_offset)