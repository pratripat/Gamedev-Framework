class ProjectileComponent:
    def __init__(self, source_entity, damage=10, effects=[], lifetime=5.0):
        self.source_entity = source_entity
        self.damage = damage
        self.effects = effects
        self.lifetime = lifetime