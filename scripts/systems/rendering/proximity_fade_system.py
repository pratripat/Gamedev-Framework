from ...components.render_effect import ProximityFadeComponent
from ...components.physics import Position
from ...components.render_effect import RenderEffectComponent

class ProximityFadeSystem:
    def __init__(self, component_manager):
        self.cm = component_manager

    def update(self):
        for entity in self.cm.get_entities_with(ProximityFadeComponent, Position, RenderEffectComponent):
            fade = self.cm.get(entity, ProximityFadeComponent)
            pos = self.cm.get(entity, Position)
            rec = self.cm.get(entity, RenderEffectComponent)

            # Find nearest target
            closest = float("inf")
            for target_tag in fade.targets:
                ids = self.cm.get_entities_with(target_tag, Position)
                for target_id in ids:
                    target_pos = self.cm.get(target_id, Position)
                    dist = (target_pos.vec - pos.vec).length_squared()
                    closest = min(closest, dist)

            # Compute alpha based on distance
            if closest <= fade.min_dist_squared:
                alpha = fade.alpha_range[1]
            elif closest >= fade.max_dist_squared:
                alpha = fade.alpha_range[0]
            else:
                t = (closest - fade.min_dist_squared) / (fade.max_dist_squared - fade.min_dist_squared)
                alpha = fade.alpha_range[1] * (1 - t) + fade.alpha_range[0] * t

            fade.current_alpha = int(alpha)
            rec.alpha = fade.current_alpha
