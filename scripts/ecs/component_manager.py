from collections import defaultdict
from ..systems.animation_state_machine import AnimationStateMachine

class ComponentManager:
    def __init__(self):
        self._components = defaultdict(dict) # {component_type: {entity_id: instance}}

    def add(self, entity_id, *components):
        for component in components:
            self._components[type(component)][entity_id] = component

    def get(self, entity_id, component_type):
        return self._components[component_type].get(entity_id, None)

    def get_entities_with(self, *component_types):
        sets = [set(self._components[ct]) for ct in component_types]
        return set.intersection(*sets) if sets else set()

    def get_entities_with_either(self, *component_types):
        sets = [set(self._components[ct]) for ct in component_types]
        return set.union(*sets) if sets else set()

    def remove_all(self, entity_id):
        for component_type in list(self._components.keys()):
            if entity_id in self._components[component_type]:
                del self._components[component_type][entity_id]
        # Remove empty component types
        self._components = defaultdict(dict, {k: v for k, v in self._components.items() if v})
        