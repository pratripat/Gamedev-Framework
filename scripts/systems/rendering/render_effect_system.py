from scripts.components.physics import Velocity
from ...components.render_effect import RenderEffectComponent, ProximityFadeComponent
from ...components.combat import WeaponComponent, HealthComponent
from ...utils import GameSceneEvents
from ...utils.tween import Tween, ease_out_quad

import pygame

class RenderEffectSystem:
    def __init__(self, event_manager, component_manager):
        self.component_manager = component_manager
        self.tween_system = None  # Set externally by GameScene

        event_manager.subscribe(GameSceneEvents.SHOOT, lambda entity_id: self._tweened_squash(entity_id, (0.9, 1.05)))
        event_manager.subscribe(
            GameSceneEvents.DAMAGE,
            self.trigger_flash,
            lambda entity_id, **args: self._tweened_squash(entity_id, target_scale=(1, 0.8)),
            lambda entity_id, proj_id, **args: self.trigger_rotate(
                entity_id, 
                angle=15 * (-1 if args.get('proj_vel', pygame.Vector2(0,0)).x > 0 else 1), 
                lerp=True, 
                duration=0.2
            ) if not args.get('death') else None,
        )
        event_manager.subscribe(GameSceneEvents.DEATH, self.trigger_death_effect)
        event_manager.subscribe(GameSceneEvents.DASH_START, lambda entity_id, duration: self.trigger_dash_blink(entity_id, duration))

    def trigger_death_effect(self, entity_id, **args):
        # 1. Permanent "Lighter Black" Silhouette Tint
        # Force add/reset the component to ensure it's not disabled
        if not self.component_manager.get(entity_id, RenderEffectComponent):
            self.component_manager.add(entity_id, RenderEffectComponent())
        
        rec = self.component_manager.get(entity_id, RenderEffectComponent)
        rec.disabled = False
        # Clear existing transient effects to make way for death visuals
        rec.effect_data.clear()
        rec.effect_timers.clear()

        # rec.effect_data["death_pale"] = {
        #     "color": (58, 68, 102),
        #     "duration": 99.0 
        # }
        # rec.effect_timers["death_pale"] = 0.0

        # 2. Death Rotation (Directional spin - CORRECTED)
        proj_vel = args.get('proj_vel', pygame.Vector2(0, 0))
        spin_angle = -360 if proj_vel.x > 0 else 360
        self.trigger_rotate(entity_id, angle=spin_angle, lerp=True, duration=0.5)

    def disable_render_effect(self, entity_id, **args):
        render_effect_comp = self.component_manager.get(entity_id, RenderEffectComponent)
        if render_effect_comp:
            render_effect_comp.disabled = True
 
    def trigger_flash(self, entity_id, **args):
        self.add_effect(entity_id, "flash", {
            "color": (255, 255, 255),
            "duration": HealthComponent.iframetimer
        })

    def _tweened_squash(self, entity_id, target_scale=(1, 0.8)):
        """Tween-based squash that animates RenderEffectComponent.scale.
        Legacy effect data is NOT used; the tween directly interpolates the scale property.
        """
        rec = self.component_manager.get(entity_id, RenderEffectComponent)
        if rec is None:
            return
        if self.tween_system is None:
            return
        self.tween_system.cancel_tweens_for(rec, 'scale')
        rec.scale = pygame.Vector2(1, 1)
        target = pygame.Vector2(target_scale)
        tween = Tween(rec, 'scale', pygame.Vector2(1, 1), target, 0.04, easing='out_quad')
        tween.on_complete = lambda: self.tween_system.from_to(
            rec, 'scale', target, pygame.Vector2(1, 1), 0.08, easing='out_quad'
        )
        self.tween_system.add(tween)
    
    def trigger_blink(self, entity_id, **args):
        self.add_effect(entity_id, "blink", {
                "color": (255, 255, 255),
                "duration": 1
            }
        )

    def trigger_rotate(self, entity_id, angle=45, lerp=True, duration=0.3):
        self.add_effect(entity_id, "rotate", {
            "target_angle": angle,
            "lerp": lerp,
            "duration": duration
        })

    def trigger_dash_blink(self, entity_id, duration):
        self.add_effect(entity_id, "dash_blink", {
            "duration": duration,
            "flicker_speed": 40.0
        })

    def add_effect(self, entity_id, effect_type, effect_data):
        if not self.component_manager.get(entity_id, RenderEffectComponent):
            self.component_manager.add(entity_id, RenderEffectComponent())
        
        rec = self.component_manager.get(entity_id, RenderEffectComponent)
        if not rec or rec.disabled or effect_type in rec.effect_data:
            return
        
        rec.effect_data[effect_type] = effect_data
        rec.effect_timers[effect_type] = 0
    
    def add_proximity_fade_component(self, entity_id):
        if not self.component_manager.get(entity_id, RenderEffectComponent):
            self.component_manager.add(entity_id, RenderEffectComponent())
        
        render_effect_comp = self.component_manager.get(entity_id, RenderEffectComponent)
        pfc = self.component_manager.get(entity_id, ProximityFadeComponent)

        if render_effect_comp.disabled or not pfc: return

        if "proximity_fade" in render_effect_comp.effect_data:
            return
        
        render_effect_comp.effect_data["proximity_fade"] = {
            "targets": pfc.targets,
            "min_dist_squared": pfc.min_dist_squared,
            "max_dist_squared": pfc.max_dist_squared,
            "alpha_range": pfc.alpha_range
        }
    
    def update(self, dt):
        for entity_id in self.component_manager.get_entities_with(RenderEffectComponent):
            render_effect_comp = self.component_manager.get(entity_id, RenderEffectComponent)
            if render_effect_comp is None or render_effect_comp.disabled:
                continue

            # Death Pale Tint
            if "death_pale" in render_effect_comp.effect_data:
                render_effect_comp.tint = render_effect_comp.effect_data["death_pale"]["color"]
            
            if "flash" in render_effect_comp.effect_data:
                total = render_effect_comp.effect_data["flash"]["duration"]

                render_effect_comp.effect_timers["flash"] += dt
                t = min(render_effect_comp.effect_timers["flash"] / total, 1)


                render_effect_comp.tint = render_effect_comp.effect_data["flash"]["color"]

                if t >= 1:
                    render_effect_comp.tint = None
                    del render_effect_comp.effect_data["flash"]
                    del render_effect_comp.effect_timers["flash"]

            if "blink" in render_effect_comp.effect_data:
                total = render_effect_comp.effect_data["blink"]["duration"]

                render_effect_comp.effect_timers["blink"] += dt
                t = min(render_effect_comp.effect_timers["blink"] / total, 1)

                if any([t > frac for frac in [0.25, 0.5, 0.75, 1]]):
                    if render_effect_comp.tint:
                        render_effect_comp.tint = None
                    else:
                        render_effect_comp.tint = render_effect_comp.effect_data["blink"]["color"]

                if t >= 1:
                    render_effect_comp.tint = None
                    del render_effect_comp.effect_data["blink"]
                    del render_effect_comp.effect_timers["blink"]
                
            if "rotate" in render_effect_comp.effect_data:
                data = render_effect_comp.effect_data["rotate"]
                total = data["duration"]
                render_effect_comp.effect_timers["rotate"] += dt
                t = min(render_effect_comp.effect_timers["rotate"] / total, 1)

                if data["lerp"]:
                    render_effect_comp.rotation = data["target_angle"] * t
                else:
                    render_effect_comp.rotation = data["target_angle"]

                if t >= 1:
                    # Only reset rotation if not a death effect
                    if "death_pale" not in render_effect_comp.effect_data:
                        render_effect_comp.rotation = 0.0
                        del render_effect_comp.effect_data["rotate"]
                        del render_effect_comp.effect_timers["rotate"]

            if "dash_blink" in render_effect_comp.effect_data:
                data = render_effect_comp.effect_data["dash_blink"]
                render_effect_comp.effect_timers["dash_blink"] += dt
                t = render_effect_comp.effect_timers["dash_blink"]
                
                if int(t * data["flicker_speed"]) % 2 == 0:
                    render_effect_comp.alpha = 100
                else:
                    render_effect_comp.alpha = 255

                if t >= data["duration"]:
                    render_effect_comp.alpha = None
                    del render_effect_comp.effect_data["dash_blink"]
                    del render_effect_comp.effect_timers["dash_blink"]

            if "fade" in render_effect_comp.effect_data:
                data = render_effect_comp.effect_data["fade"]
                total = data["duration"]
                render_effect_comp.effect_timers["fade"] += dt
                t = min(render_effect_comp.effect_timers["fade"] / total, 1.0)
                
                start_alpha = data.get("start_alpha", 255)
                target_alpha = data.get("target_alpha", 0)
                render_effect_comp.alpha = int(start_alpha + (target_alpha - start_alpha) * t)

                if t >= 1.0:
                    del render_effect_comp.effect_data["fade"]
                    del render_effect_comp.effect_timers["fade"]

            if len(render_effect_comp.effect_data) == 0:
                self.component_manager.remove(entity_id, RenderEffectComponent)
