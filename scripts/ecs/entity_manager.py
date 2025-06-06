import itertools

class EntityManager:
    def __init__(self):
        self._next_id = itertools.count()
        self.entities = set() # to not contain multiple occurences of the same entity
    
    def create_entity(self):
        entity_id = next(self._next_id)
        self.entities.add(entity_id)
        return entity_id

    def delete_entity(self, entity_id):
        if entity_id in self.entities:
            self.entities.discard(entity_id)
            return True
        return False
