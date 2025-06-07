from .ecs.component import Position, RenderComponent, AnimationComponent

class AnimationSystem:
    def __init__(self, component_manager):
        self.component_manager = component_manager
    
    def update(self, dt):
        for eid in self.component_manager.get_entities_with(AnimationComponent):
            animation_component = self.component_manager.get(eid, AnimationComponent)
            animation_component.update(dt)

class RenderSystem:
    def __init__(self, component_manager):
        self.component_manager = component_manager

    def render(self, surface):
        for eid in self.component_manager.get_entities_with(Position):
            pos = self.component_manager.get(eid, Position)

            if self.component_manager.get(eid, RenderComponent):
                render_component = self.component_manager.get(eid, RenderComponent)
                offset = render_component.offset
                surface.blit(render_component.surface, (pos.x + offset.x, pos.y + offset.y))
            elif self.component_manager.get(eid, AnimationComponent):
                animation_component = self.component_manager.get(eid, AnimationComponent)
                animation = animation_component.animation
                animation.render(surface, (pos.x + animation_component.offset.x, pos.y + animation_component.offset.y))
