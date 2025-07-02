class ProjectileComponent:
    def __init__(self, source_entity, damage=10, effects=[], lifetime=2.0, bounce=2, penetration=0):
        # self.entity_id = entity_id
        self.source_entity = source_entity
        self.damage = damage
        self.effects = effects
        self.lifetime = lifetime
        self.data = {
            "bounce": bounce,
            "penetration": penetration
        }