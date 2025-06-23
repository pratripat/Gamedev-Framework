import pygame
from ...utils import CENTER
from ...components.physics import Position, Velocity
from ...components.animation import RenderComponent, AnimationComponent
from ..animation.animation_state_machine import AnimationStateMachine
from .render_effect_system import RenderEffectSystem
from ...components.render_effect import RenderEffectComponent

class AnimationSystem:
    def __init__(self, component_manager):
        self.component_manager = component_manager
    
    def update(self, dt):
        for eid in self.component_manager.get_entities_with(AnimationStateMachine):
            animation_state_machine = self.component_manager.get(eid, AnimationStateMachine)

            if animation_state_machine.animation_component.entity_type == "chess_piece":
                vel = self.component_manager.get(eid, Velocity).vec
                is_moving = vel.x != 0 or vel.y != 0
                
                suggested_anim = "moving" if is_moving else "idle"

                animation_state_machine.set_animation(suggested_anim)

            animation_state_machine.animation_component.update(dt)

class RenderSystem:
    def __init__(self, event_manager, component_manager):
        self.component_manager = component_manager

        self.render_effect_system = RenderEffectSystem(event_manager, component_manager)
    
    def update(self, fps, dt):
        self.render_effect_system.update(fps, dt)

    def render(self, surface, camera):
        scroll = camera.scroll
        temp_surf_offset = pygame.Vector2(0,0)
        temp_surf = pygame.Surface(surface.get_size())
        for eid in self.component_manager.get_entities_with(Position):
            pos = self.component_manager.get(eid, Position)
            pos -= scroll

            scale = None
            tint = None

            # render effect component
            rec = self.component_manager.get(eid, RenderEffectComponent)
            if rec:
                scale = rec.scale
                tint = rec.tint

            if self.component_manager.get(eid, RenderComponent):
                render_component = self.component_manager.get(eid, RenderComponent)
                offset = render_component.offset
                rcs = render_component.surface
                if not (scale == None or (scale[0] == 1 and scale[1] == 1)):
                    offset[0] *= scale[0]
                    offset[1] *= scale[1]
                    rcs = pygame.transform.scale(rcs, (rcs.get_width()*scale[0], rcs.get_height()*scale[1]))
                
                if tint is not None:
                    tint_surf = pygame.Surface(rcs.get_size(), pygame.SRCALPHA)
                    tint_surf.fill(rec.tint)
                    rcs.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                temp_surf.blit(rcs, (pos.x + offset.x, pos.y + offset.y))
            elif self.component_manager.get(eid, AnimationComponent):
                animation_component = self.component_manager.get(eid, AnimationComponent)
                animation = animation_component.animation
                animation.render(temp_surf, (pos.x + animation_component.offset.x, pos.y + animation_component.offset.y), scale=scale, tint=tint)

        if camera.zoom != 1:
            temp_surf = pygame.transform.scale(temp_surf, ((surface.get_width() * camera.zoom), (surface.get_height() * camera.zoom)))
            temp_surf_offset = CENTER - (pygame.Vector2(temp_surf.get_size()) / 2)

        surface.blit(temp_surf, temp_surf_offset)