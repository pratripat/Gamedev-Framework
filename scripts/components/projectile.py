class ProjectileComponent:
    def __init__(self, source_entity, damage=10, effects=[]):
        self.source_entity = source_entity
        self.damage = damage
        self.effects = effects