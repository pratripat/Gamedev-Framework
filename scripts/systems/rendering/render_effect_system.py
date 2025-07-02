from ...components.render_effect import RenderEffectComponent
from ...components.combat import WeaponComponent, HealthComponent
from ...utils import GameSceneEvents

import pygame

class RenderEffectSystem:
    def __init__(self, event_manager, component_manager):
        self.component_manager = component_manager

        event_manager.subscribe(GameSceneEvents.SHOOT, lambda entity_id: self.trigger_squash(entity_id, (0.9, 1.05)))
        event_manager.subscribe(GameSceneEvents.DAMAGE, self.trigger_flash, lambda entity_id, **args: self.trigger_squash(entity_id, target_scale=(1, 0.8)))
        event_manager.subscribe(GameSceneEvents.DEATH, self.disable_render_effect)

    def disable_render_effect(self, entity_id):
        render_effect_comp = self.component_manager.get(entity_id, RenderEffectComponent)
        render_effect_comp.disabled = True
 
    def trigger_squash(self, entity_id, target_scale=(0.5,0.5)):
        weapon_comp = self.component_manager.get(entity_id, WeaponComponent)

        if weapon_comp is None: return 

        self.add_squash_effect(
            entity_id = entity_id, 
            effect_data = {
                "start_scale": pygame.Vector2(1, 1),
                "target_scale": pygame.Vector2(target_scale),
                "duration": 0.05,
                "return_back": True
            }
        )
    
    def trigger_flash(self, entity_id, **args):
        self.add_flash_effect(
            entity_id = entity_id,
            effect_data = {
                "color": (255, 255, 255),
                "duration": HealthComponent.iframetimer
            }
        )
    
    def trigger_blink(self, entity_id, **args):
        self.add_blink_effect(
            entity_id=entity_id,
            effect_data = {
                "color": (255, 255, 255),
                "duration": 1
            }
        )

    def add_squash_effect(self, entity_id, effect_data):
        if not self.component_manager.get(entity_id, RenderEffectComponent):
            self.component_manager.add(entity_id, RenderEffectComponent())
        
        render_effect_comp = self.component_manager.get(entity_id, RenderEffectComponent)

        if render_effect_comp.disabled: return

        if "squash" in render_effect_comp.effect_data:
            return
        
        render_effect_comp.effect_data["squash"] = effect_data
        render_effect_comp.effect_timers["squash"] = 0
    
    def add_flash_effect(self, entity_id, effect_data):
        if not self.component_manager.get(entity_id, RenderEffectComponent):
            self.component_manager.add(entity_id, RenderEffectComponent())
        
        render_effect_comp = self.component_manager.get(entity_id, RenderEffectComponent)

        if render_effect_comp.disabled: return

        if "flash" in render_effect_comp.effect_data:
            return
        
        render_effect_comp.effect_data["flash"] = effect_data
        render_effect_comp.effect_timers["flash"] = 0
    
    def add_blink_effect(self, entity_id, effect_data):
        if not self.component_manager.get(entity_id, RenderEffectComponent):
            self.component_manager.add(entity_id, RenderEffectComponent())
        
        render_effect_comp = self.component_manager.get(entity_id, RenderEffectComponent)

        if render_effect_comp.disabled: return

        if "blink" in render_effect_comp.effect_data:
            return
        
        render_effect_comp.effect_data["blink"] = effect_data
        render_effect_comp.effect_timers["blink"] = 0
    
    def update(self, dt):
        for entity_id in self.component_manager.get_entities_with(RenderEffectComponent):
            render_effect_comp = self.component_manager.get(entity_id, RenderEffectComponent)
            if render_effect_comp is None or render_effect_comp.disabled:
                continue

            if "squash" in render_effect_comp.effect_data:
                total = render_effect_comp.effect_data["squash"]["duration"]

                render_effect_comp.effect_timers["squash"] += dt
                t = min(render_effect_comp.effect_timers["squash"] / total, 1)

                current_scale = render_effect_comp.effect_data["squash"]["start_scale"].lerp(render_effect_comp.effect_data["squash"]["target_scale"], t)
                render_effect_comp.scale = current_scale

                if t >= 1:
                    if render_effect_comp.effect_data["squash"]["return_back"]:
                        render_effect_comp.effect_data["squash"]["start_scale"], render_effect_comp.effect_data["squash"]["target_scale"] = (
                            render_effect_comp.effect_data["squash"]["target_scale"],
                            pygame.Vector2(1, 1)
                        )
                        render_effect_comp.effect_timers["squash"] = 0
                        render_effect_comp.effect_data["squash"]["return_back"] = False
                    else:
                        del render_effect_comp.effect_timers["squash"]
                        del render_effect_comp.effect_data["squash"]
            
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

            if len(render_effect_comp.effect_data) == 0:
                self.component_manager.remove(entity_id, RenderEffectComponent)