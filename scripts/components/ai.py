from ..utils import EnemyState

class AIComponent:
    def __init__(self, entity_id, behavior, data={
        "speed": 2,
        "attack_dist": 300
    }):
        self.entity_id = entity_id
        self.behavior = behavior
        self.state = EnemyState.IDLE
        self.timer = 0

        self.data = data
