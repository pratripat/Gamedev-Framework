import pygame
from ..utils import CENTER
from ..components.physics import Position, Velocity
from ..components.animation import RenderComponent, AnimationComponent
from .animation_state_machine import AnimationStateMachine

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
    def __init__(self, component_manager):
        self.component_manager = component_manager

    def render(self, surface, camera):
        scroll = camera.scroll
        offset = pygame.Vector2(0,0)
        temp_surf = pygame.Surface(surface.get_size())
        for eid in self.component_manager.get_entities_with(Position):
            pos = self.component_manager.get(eid, Position)
            pos -= scroll

            if self.component_manager.get(eid, RenderComponent):
                render_component = self.component_manager.get(eid, RenderComponent)
                offset = render_component.offset
                temp_surf.blit(render_component.surface, (pos.x + offset.x, pos.y + offset.y))
            elif self.component_manager.get(eid, AnimationComponent):
                animation_component = self.component_manager.get(eid, AnimationComponent)
                animation = animation_component.animation
                animation.render(temp_surf, (pos.x + animation_component.offset.x, pos.y + animation_component.offset.y))

        if camera.zoom != 1:
            temp_surf = pygame.transform.scale(temp_surf, ((surface.get_width() * camera.zoom), (surface.get_height() * camera.zoom)))
            offset = CENTER - (pygame.Vector2(temp_surf.get_size()) / 2)

        surface.blit(temp_surf, offset)