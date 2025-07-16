import itertools
from ..utils import GameSceneEvents
from ..components.physics import Velocity
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
        if not self.cm.get(entity_id, Velocity) or not self.cm.get(entity_id, AnimationStateMachine):
            return
        
        self.cm.get(entity_id, Velocity).vec = (0, 0)
        self.cm.get(entity_id, AnimationStateMachine).set_animation("death")
        hbc = self.cm.get(entity_id, HurtBoxComponent)
        if hbc: hbc.disabled = True
        hbc = self.cm.get(entity_id, HitBoxComponent)
        if hbc: hbc.disabled = True

        self.dead_entities.add(entity_id)

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

    def refresh_entities(self):
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