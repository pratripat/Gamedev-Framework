import itertools
import math
import random
import pygame
from ..utils import GameSceneEvents
from ..components.physics import Velocity, Position
from ..components.combat import HurtBoxComponent, HitBoxComponent
from ..components.render_effect import RenderEffectComponent
from ..systems.animation.animation_state_machine import AnimationStateMachine

import itertools

class EntityManager:
    def __init__(self, event_manager, component_manager):
        self._next_id = itertools.count()
        self.entities = set()
        self.to_remove = set()
        self.dead_entities = set()
        self.player_id = None

        self.cm = component_manager
        self.em = event_manager

        self.em.subscribe(GameSceneEvents.DEATH, self.kill_entity)
        self.em.subscribe(GameSceneEvents.REMOVE_ENTITY, self.delete_entity)
        self.em.subscribe(GameSceneEvents.ANIMATION_FINISHED, self.check_dead_entity)

    def create_entity(self, player=False):
        eid = next(self._next_id)
        self.entities.add(eid)
        if player:
            self.player_id = eid
        return eid

    def kill_entity(self, entity_id):
        asm = self.cm.get(entity_id, AnimationStateMachine)
        
        # Disable collision for the dying entity immediately
        hbc = self.cm.get(entity_id, HurtBoxComponent)
        if hbc: hbc.disabled = True
        hbc = self.cm.get(entity_id, HitBoxComponent)
        if hbc: hbc.disabled = True

        # Only handle death animation for the player
        if entity_id == self.player_id and asm:
            self.cm.get(entity_id, Velocity).vec = (0, 0)
            
            # Safely try to set death animation
            anim_comp = asm.animation_component
            death_anim_id = anim_comp.entity_name + "_death"
            if death_anim_id in anim_comp.animation_handler.animations:
                asm.set_animation("death")
                self.dead_entities.add(entity_id)
            else:
                self.to_remove.add(entity_id)
        else:
            # "Tossed" death effect for enemies
            # Calculate knockback direction: Away from the player
            from ..components.physics import KnockbackComponent
            
            player_pos = self.cm.get(self.player_id, Position)
            target_pos = self.cm.get(entity_id, Position)
            
            if player_pos and target_pos:
                from ..utils import get_unit_direction_towards
                toss_dir = get_unit_direction_towards(player_pos.vec, target_pos.vec)
            else:
                angle = random.uniform(0, math.pi * 2)
                toss_dir = pygame.Vector2(math.cos(angle), math.sin(angle))

            # Apply a strong "toss" knockback
            self.cm.add(entity_id, KnockbackComponent(toss_dir, 15, duration=0.4))
            
            # Add rotation effect matching the toss direction
            rec = self.cm.get(entity_id, RenderEffectComponent)
            if not rec:
                rec = RenderEffectComponent()
                self.cm.add(entity_id, rec)
            
            rec.disabled = False # Re-enable for toss rotation
            spin_angle = 720 if toss_dir.x < 0 else -720
            rec.effect_data["rotate"] = {"target_angle": spin_angle, "lerp": True, "duration": 0.4}
            rec.effect_timers["rotate"] = 0.0

            # Stop regular movement
            vel = self.cm.get(entity_id, Velocity)
            if vel: vel.vec = (0, 0)

            # Queue for delayed removal
            if not hasattr(self, 'dying_timers'): self.dying_timers = {}
            self.dying_timers[entity_id] = 0.4 # Match toss duration

    def check_dead_entity(self, entity_id, animation_id):
        if animation_id.endswith("_death") and entity_id in self.dead_entities:
            self.dead_entities.discard(entity_id)
            self.to_remove.add(entity_id)
            return True
        return False

    def delete_entity(self, entity_id):
        if entity_id in self.entities:
            self.to_remove.add(entity_id)
            return True
        return False

    def refresh_entities(self, dt=0):
        # 1. Update dying timers for "tossed" enemies
        if hasattr(self, 'dying_timers'):
            finished = []
            for eid, t in self.dying_timers.items():
                self.dying_timers[eid] -= dt
                if self.dying_timers[eid] <= 0:
                    finished.append(eid)
            
            for eid in finished:
                del self.dying_timers[eid]
                # Trigger particle burst at the final position
                pos = self.cm.get(eid, Position)
                if pos:
                    from ..components.particle import ParticleEmitter, ParticleConfig, EmitterShape, EmitterShapeType
                    burst = self.create_entity()
                    self.cm.add(burst, Position(burst, pos.x, pos.y))
                    self.cm.add(burst, ParticleEmitter(
                        rate=250, # High rate for instant feel
                        duration=0.1,
                        loop=False,
                        particle_config=ParticleConfig(
                            vel=0.4, # Lower initial velocity
                            lifetime=0.8, 
                            color=(255,255,255), 
                            size=8, # Start larger
                            fade=True, # No alpha fade, stay solid
                            flicker_colors=[(0,0,0), (255,255,255)],
                            flicker_speed=5.0, # Slower flicker
                            shrink=True, # Shrink instead of oscillate
                            friction=0.9 # Decay velocity over time
                        ),
                        shape=EmitterShape(EmitterShapeType.CIRCLE, radius=20)
                    ))

                self.to_remove.add(eid)

        for eid in self.to_remove:
            if eid in self.entities:
                self.entities.discard(eid)
                self.em.unsubscribe_all_for(eid)
                self.cm.remove_all(eid)
        self.to_remove.clear()

    def clear_entities(self):
        self.entities.clear()
        self.to_remove.clear()
        self.dead_entities.clear()
        self.player_id = None
        self.cm.clear_all()
        self.em.unsubscribe_all_for(None)