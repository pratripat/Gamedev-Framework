from ..utils import EnemyState

class AIComponent:
    def __init__(self, entity_id, behavior, shoot_fn):
        self.entity_id = entity_id
        self.behavior = behavior
        self.shoot_fn = shoot_fn
        self.state = EnemyState.IDLE
        self.timer = 0
        
        self.data = {
            "speed": 2,
            "attack_dist": 300
        }
