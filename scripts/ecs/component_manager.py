from collections import defaultdict

class ComponentManager:
    def __init__(self):
        self._components = defaultdict(dict) # {component_type: {entity_id: component_instance}}
        self._query_cache = {}
        self._cache_version = 0

    def add(self, entity_id, *components):
        self._cache_version += 1
        for component in components:
            self._components[type(component)][entity_id] = component

    def get(self, entity_id, component_type):
        comps = self._components.get(component_type)
        if comps is None:
            return None
        return comps.get(entity_id)

    def get_many(self, entity_id, *component_types):
        result = []
        for ct in component_types:
            comps = self._components.get(ct)
            if comps is None:
                result.append(None)
            else:
                result.append(comps.get(entity_id))
        return tuple(result)

    def get_entities_with(self, *component_types):
        if not component_types:
            return set()

        key = component_types
        if key in self._query_cache:
            cached_version, result = self._query_cache[key]
            if cached_version == self._cache_version:
                return result

        smallest_ct = min(component_types, key=lambda ct: len(self._components.get(ct, ())))
        smallest_dict = self._components.get(smallest_ct)
        if smallest_dict is None:
            self._query_cache[key] = (self._cache_version, set())
            return set()

        other_dicts = []
        for ct in component_types:
            if ct != smallest_ct:
                d = self._components.get(ct)
                other_dicts.append(d if d is not None else {})

        entities = set()
        for entity_id in smallest_dict:
            if all(entity_id in d for d in other_dicts):
                entities.add(entity_id)

        self._query_cache[key] = (self._cache_version, entities)
        return entities

    def get_entities_with_either(self, *component_types):
        entities = set()
        for ct in component_types:
            comps = self._components.get(ct)
            if comps:
                entities.update(comps.keys())
        return entities

    def remove(self, entity_id, component_type):
        self._cache_version += 1
        comps = self._components.get(component_type)
        if comps and entity_id in comps:
            del comps[entity_id]

    def remove_all(self, entity_id):
        self._cache_version += 1
        for component_type in list(self._components.keys()):
            comps = self._components[component_type]
            if entity_id in comps:
                del comps[entity_id]

    def clear_all(self):
        self._cache_version += 1
        self._components.clear()
        self._query_cache.clear()
