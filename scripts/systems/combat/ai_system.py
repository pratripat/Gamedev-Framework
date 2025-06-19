from ...components.ai import AIComponent
from ...components.physics import Position, Velocity

from ...utils import EnemyState, GameSceneEvents

import pygame, random

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

        event_manager.subscribe(GameSceneEvents.DEATH, self._reset_ai_comps, self._handle_dead_enemy)

    def _handle_dead_enemy(self, entity_id):
        ai_comp = self.component_manager.get(entity_id, AIComponent)
        if ai_comp:
            ai_comp.state = EnemyState.DEAD
            ai_comp.timer = 0

    def _reset_ai_comps(self, entity_id):
        if self.player_entity_id != entity_id:
            return
        
        for eid in self.component_manager.get_entities_with(AIComponent):
            ai_comp = self.component_manager.get(eid, AIComponent)

            ai_comp.state = EnemyState.IDLE    
            ai_comp.timer = 0

    def _default_behavior(self, eid, ai_comp, dt):
        return self._chase_behavior(eid, ai_comp, dt)

    def _chase_behavior(self, eid, ai_comp, dt):
        pos = self.component_manager.get(eid, Position)
        vel = self.component_manager.get(eid, Velocity)
        player_pos = self.component_manager.get(self.player_entity_id, Position)

        if ai_comp.state == EnemyState.IDLE:
            if ai_comp.timer > 0.5:
                ai_comp.state = EnemyState.CHASE
                ai_comp.timer = 0
        
        elif ai_comp.state == EnemyState.CHASE:
            if player_pos is None:
                return
            
            if ai_comp.timer > 1:
                target_pos = player_pos.vec + pygame.Vector2(random.uniform(-200, 200), random.uniform(-200, 200)) # TEMP : avoids stacking of enemies
                dir = (player_pos.vec - pos.vec).normalize()
                vel.vec = dir * ai_comp.data["speed"]

                if pos.vec.distance_to(player_pos.vec) <= ai_comp.data["attack_dist"]:
                    vel.vec = (0, 0)
                    ai_comp.state = EnemyState.ATTACK
                    ai_comp.timer = 0

        elif ai_comp.state == EnemyState.ATTACK:
            if ai_comp.timer < 1:
                self.event_manager.emit(GameSceneEvents.SHOOT, entity_id=eid)
            elif pos.vec.distance_to(player_pos.vec) > ai_comp.data["attack_dist"]:
                ai_comp.state = EnemyState.CHASE
                ai_comp.timer = 0

    def _sniper_behavior(self, eid, ai_comp, dt):
        print('sniping', ai_comp.state)

    def _patrol_behavior(self, eid, ai_comp, dt):
        print('patrolling', ai_comp.state)

    def update(self, fps, dt):
        for eid in self.component_manager.get_entities_with(AIComponent):
            ai_comp = self.component_manager.get(eid, AIComponent)
            if ai_comp is None:
                continue

            if ai_comp.state == EnemyState.DEAD:
                continue
            
            ai_comp.timer += dt / fps

            self.AI_FUNCS.get(ai_comp.behavior, self._default_behavior)(eid, ai_comp, dt)

            
