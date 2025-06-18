from enum import Enum

class EnemyState(Enum):
    IDLE = 0
    PATROL = 1
    CHASE = 2
    ATTACK = 3
    FLEE = 4

class AIComponent:
    def __init__(self, entity_id, behavior, shoot_fn):
        self.entity_id = entity_id
        self.behavior = behavior
        self.shoot_fn = shoot_fn
        self.state = EnemyState.IDLE
