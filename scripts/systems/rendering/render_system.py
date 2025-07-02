import pygame
from ...utils import CENTER

from ...components.physics import Position, Velocity
from ...components.animation import RenderComponent, AnimationComponent
from ...components.render_effect import RenderEffectComponent

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
    def __init__(self, event_manager, component_manager, entity_manager):
        self.component_manager = component_manager

        self.render_effect_system = RenderEffectSystem(event_manager, component_manager)
        self.particle_effect_system = ParticleEffectSystem(component_manager, entity_manager)

    def update(self, dt):
        self.render_effect_system.update(dt)
        self.particle_effect_system.update(dt)

    def render(self, surface, camera):
        scroll = camera.scroll
        temp_surf_offset = pygame.Vector2(0, 0)
        temp_surf = pygame.Surface(surface.get_size())
        temp_surf.convert_alpha()

        for eid in self.component_manager.get_entities_with(Position):
            pos = self.component_manager.get(eid, Position)
            pos -= scroll

            scale = None
            tint = None

            # Render effect component
            rec = self.component_manager.get(eid, RenderEffectComponent)
            if rec and not rec.disabled:
                scale = rec.scale
                tint = rec.tint

            # Render component
            render_component = self.component_manager.get(eid, RenderComponent)
            if render_component:
                offset = render_component.offset
                rcs = render_component.surface
                if not (scale is None or (scale[0] == 1 and scale[1] == 1)):
                    offset[0] *= scale[0]
                    offset[1] *= scale[1]
                    rcs = pygame.transform.scale(
                        rcs, (int(rcs.get_width() * scale[0]), int(rcs.get_height() * scale[1]))
                    )

                if tint is not None:
                    tint_surf = pygame.Surface(rcs.get_size(), pygame.SRCALPHA)
                    tint_surf.fill(tint)
                    rcs.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                temp_surf.blit(rcs, (pos.x + offset.x, pos.y + offset.y))

            # Animation component
            animation_component = self.component_manager.get(eid, AnimationComponent)
            if animation_component:
                animation = animation_component.animation
                animation_pos = pygame.Vector2(pos.x + animation_component.offset.x, pos.y + animation_component.offset.y)

                # Apply scaling to animation
                if scale is not None and (scale[0] != 1 or scale[1] != 1):
                    animation.render(temp_surf, animation_pos, scale=scale, tint=tint)
                else:
                    animation.render(temp_surf, animation_pos, tint=tint)

        # Particle effects
        self.particle_effect_system.render(temp_surf, scroll=scroll)

        # Apply camera zoom
        if camera.zoom != 1:
            temp_surf = pygame.transform.scale(
                temp_surf, (int(surface.get_width() * camera.zoom), int(surface.get_height() * camera.zoom))
            )
            temp_surf_offset = pygame.Vector2(surface.get_width() / 2, surface.get_height() / 2) - pygame.Vector2(
                temp_surf.get_size()
            ) / 2

        surface.blit(temp_surf, temp_surf_offset)