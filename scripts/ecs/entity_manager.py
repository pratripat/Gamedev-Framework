import itertools
from ..utils import GameSceneEvents
from ..components.physics import Velocity
from ..components.animation import AnimationComponent
from ..systems.animation_state_machine import AnimationStateMachine

class EntityManager:
    def __init__(self, event_manager, component_manager):
        self._next_id = itertools.count()
        self.entities = set() # to not contain multiple occurences of the same entity
        self.to_remove = set()
        self.dead_entities = set() # entities that are dead but not yet removed
        self.player_id = None
        self.component_manager = component_manager

        event_manager.subscribe(GameSceneEvents.DEATH, self.kill_entity)
        event_manager.subscribe(GameSceneEvents.REMOVE_ENTITY, self.delete_entity)
        event_manager.subscribe(GameSceneEvents.ANIMATION_FINISHED, self.check_dead_entity)
    
    def create_entity(self, player=False):
        entity_id = next(self._next_id)
        self.entities.add(entity_id)
        if player: self.player_id = entity_id
        return entity_id
    
    def kill_entity(self, entity_id):
        self.component_manager.get(entity_id, Velocity).vec = (0,0)
        self.component_manager.get(entity_id, AnimationStateMachine).set_animation("death")

        self.dead_entities.add(entity_id)
    
    def check_dead_entity(self, entity_id, animation_id):
        if animation_id.split('_')[-1] == "death" and entity_id in self.dead_entities:
            print(entity_id)
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
        for entity_id in self.to_remove:
            if entity_id in self.entities.copy():
                self.entities.discard(entity_id)
            self.component_manager.remove_all(entity_id)
        self.to_remove.clear()