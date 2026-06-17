from collections import defaultdict
from ..systems.animation.animation_state_machine import AnimationStateMachine

class ComponentManager:
    def __init__(self):
        self._components = defaultdict(dict) # {component_type: {entity_id: instance}}

    def add(self, entity_id, *components, check_existing=False):
        for component in components:
            if check_existing:
                if self._components.get(type(component),{}).get(entity_id):
                    continue
            self._components[type(component)][entity_id] = component

    def get(self, entity_id, component_type):
        return self._components[component_type].get(entity_id, None)

    def get_entities_with(self, *component_types):
        if not component_types:
            return set()
            
        # Optimization: Find the component type with the fewest entities
        smallest_ct = min(component_types, key=lambda ct: len(self._components.get(ct, {})))
        
        # Iterating over the smallest set of keys drastically reduces loop iterations
        entities = set()
        other_dicts = [self._components.get(ct, {}) for ct in component_types if ct != smallest_ct]
        
        for entity_id in self._components.get(smallest_ct, {}):
            # dict lookup is O(1), and we only check entities that definitely have the rarest component
            if all(entity_id in d for d in other_dicts):
                entities.add(entity_id)
                
        return entities

    def get_entities_with_either(self, *component_types):
        entities = set()
        for ct in component_types:
            entities.update(self._components.get(ct, {}).keys())
        return entities

    def remove(self, entity_id, component_type):
        del self._components[component_type][entity_id]

    def remove_all(self, entity_id):
        for component_type in list(self._components.keys()):
            if entity_id in self._components[component_type]:
                del self._components[component_type][entity_id]
        # Remove empty component types
        self._components = defaultdict(dict, {k: v for k, v in self._components.items() if v})
    
    def clear_all(self):
        self._components.clear()
        