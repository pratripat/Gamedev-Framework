from ...components.ai import AIComponent
from ...components.physics import Position

class AISystem:
    def __init__(self, player_entity_id, component_manager, event_manager):
        self.player_entity_id = player_entity_id
        self.component_manager = component_manager
        self.event_manager = event_manager
        self.AI_FUNCS = {
            "default": self._default_behavior,
            "chase": self._chase_behavior,
            "sniper": self._sniper_behavior,
            "patrol": self._patrol_behavior
        }

    def _default_behavior(self, eid, ai_comp, dt):
        return self._chase_behavior(eid, ai_comp, dt)

    def _chase_behavior(self, eid, ai_comp, dt):
        print('chasing', ai_comp.state)
    
    def _sniper_behavior(self, eid, ai_comp, dt):
        print('sniping', ai_comp.state)

    def _patrol_behavior(self, eid, ai_comp, dt):
        print('patrolling', ai_comp.state)

    def update(self, dt):
        for eid in self.component_manager.get_entities_with(AIComponent):
            ai_comp = self.component_manager.get(eid, AIComponent)
            if ai_comp is None:
                continue
        
            self.AI_FUNCS.get(ai_comp.behavior, self._default_behavior)(eid, ai_comp, dt)

            
