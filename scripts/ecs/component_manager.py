from collections import defaultdict

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