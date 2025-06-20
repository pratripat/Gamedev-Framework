from ...components.render_effects import SquashEffect
from ...components.animation import RenderComponent, AnimationComponent

class RenderEffectSystem:
    def __init__(self, component_manager):
        self.component_manager = component_manager
    
    def update(self, fps, dt):
        for entity_id in self.component_manager.get_entities_with(SquashEffect):
            squash_effect = self.component_manager.get(entity_id, SquashEffect)

            comp = self.component_manager.get(entity_id, RenderComponent)
            if comp is None:
                comp = self.component_manager.get(entity_id, AnimationComponent)
            
            if comp is None:
                continue

            squash_effect.timer += dt / fps
            t = min(squash_effect.timer / squash_effect.duration, 1)

            current_scale = squash_effect.start_scale.lerp(squash_effect.target_scale, t)
            comp.resize_scale(current_scale)

            if t >= 1:
                if squash_effect.return_to_normal:
                    squash_effect.start_scale, squash_effect.target_scale = (
                        squash_effect.target_scale,
                        pygame.Vector2(1, 1)
                    )