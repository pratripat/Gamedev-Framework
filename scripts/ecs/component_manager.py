from collections import defaultdict

class ComponentManager:
    def __init__(self):
        self._components = defaultdict(dict) # {component_type: {entity_id: component_instance}}
        self._query_cache = {}

    def add(self, entity_id, *components):
        self._query_cache.clear()
        for component in components:
            self._components[type(component)][entity_id] = component
    
    def get(self, entity_id, component_type):
        return self._components.get(component_type, {}).get(entity_id)

    def get_entities_with(self, *component_types):
        if not component_types:
            return set()
            
        # Check cache
        if component_types in self._query_cache:
            return self._query_cache[component_types]
            
        # Optimization: Find the component type with the fewest entities
        smallest_ct = min(component_types, key=lambda ct: len(self._components.get(ct, {})))
        
        entities = set()
        other_dicts = [self._components.get(ct, {}) for ct in component_types if ct != smallest_ct]
        
        for entity_id in self._components.get(smallest_ct, {}):
            if all(entity_id in d for d in other_dicts):
                entities.add(entity_id)
                
        self._query_cache[component_types] = entities
        return entities

    def get_entities_with_either(self, *component_types):
        entities = set()
        for ct in component_types:
            entities.update(self._components.get(ct, {}).keys())
        return entities

    def remove(self, entity_id, component_type):
        self._query_cache.clear()
        if component_type in self._components and entity_id in self._components[component_type]:
            del self._components[component_type][entity_id]

    def remove_all(self, entity_id):
        self._query_cache.clear()
        for component_type in list(self._components.keys()):
            if entity_id in self._components[component_type]:
                del self._components[component_type][entity_id]
    
    def clear_all(self):
        self._query_cache.clear()
        self._components.clear()
