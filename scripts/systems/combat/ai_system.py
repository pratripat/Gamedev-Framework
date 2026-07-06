from scripts.components.combat import AttackPatternComponent
from ...components.ai import AIComponent
from ...components.physics import Position, Velocity, CollisionComponent
from ...components.timer import TimerComponent

from ...utils import EnemyState, GameSceneEvents

import pygame, random, math

# TEMP : GET RID OF THE MAGIC NUMBRES IN THE AI FUNCS

class AISystem:
    def __init__(self, player_entity_id, component_manager, event_manager):
        self.player_entity_id = player_entity_id
        self.component_manager = component_manager
        self.event_manager = event_manager
        self.AI_FUNCS = {
            "default": self._default_behavior,
            "chase": self._chase_behavior,
            "sniper": self._sniper_behavior,
            "aggressive": self._aggressive_behavior,
            "kiting": self._kiting_behavior,
            "support": self._support_behavior,
            "patrol": self._patrol_behavior
        }

        event_manager.subscribe(GameSceneEvents.DEATH, self._reset_ai_comps, self._handle_dead_enemy)

    def _handle_dead_enemy(self, entity_id, **kwargs):
        ai_comp = self.component_manager.get(entity_id, AIComponent)
        if ai_comp:
            ai_comp.state = EnemyState.DEAD
            ai_comp.timer = 0
        
        apc = self.component_manager.get(entity_id, AttackPatternComponent)
        if apc: apc.active = False

    def _reset_ai_comps(self, entity_id, **kwargs):
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

        # idle 
        if ai_comp.state == EnemyState.IDLE:
            if ai_comp.timer > 0.5:
                ai_comp.state = EnemyState.CHASE
                ai_comp.timer = 0
                
        # chase player
        elif ai_comp.state == EnemyState.CHASE:
            if player_pos is None:
                return
            
            if ai_comp.timer > 1:
                target_pos = player_pos.vec + pygame.Vector2(random.uniform(-200, 200), random.uniform(-200, 200)) # TEMP : avoids stacking of enemies
                dir = (target_pos - pos.vec).normalize()
                vel.vec = dir * ai_comp.data["speed"]

                if pos.vec.distance_to(player_pos.vec) <= ai_comp.data["attack_dist"]:
                    vel.vec = (0, 0)
                    ai_comp.state = EnemyState.ATTACK
                    ai_comp.timer = 0
        # attack once closer to player
        elif ai_comp.state == EnemyState.ATTACK:
            apc = self.component_manager.get(eid, AttackPatternComponent)
            if apc: apc.active = True

            if ai_comp.timer > 2:
                if apc: apc.active = False
                ai_comp.state = EnemyState.CHASE
                ai_comp.timer = 0

    def _aggressive_behavior(self, eid, ai_comp, dt):
        """Dashes toward player, circles around them, and retreats unpredictably."""
        pos = self.component_manager.get(eid, Position)
        vel = self.component_manager.get(eid, Velocity)
        player_pos = self.component_manager.get(self.player_entity_id, Position)

        if ai_comp.state == EnemyState.IDLE:
            if ai_comp.timer > 0.3:
                ai_comp.state = EnemyState.CHASE
                ai_comp.timer = 0

        elif ai_comp.state == EnemyState.CHASE:
            if player_pos is None:
                return

            dist = pos.vec.distance_to(player_pos.vec)

            # Dash toward player when far
            if dist > ai_comp.data["attack_dist"] * 1.5:
                dir = (player_pos.vec - pos.vec).normalize()
                vel.vec = dir * ai_comp.data["speed"] * 1.5
                ai_comp.timer = 0
            # Circle when close
            elif dist < ai_comp.data["attack_dist"] * 0.5:
                perp = pygame.Vector2(-(player_pos.vec - pos.vec).y, (player_pos.vec - pos.vec).x)
                perp = perp.normalize() if perp.length_squared() > 0 else pygame.Vector2(1, 0)
                # Alternate circling direction
                if random.random() < 0.02:
                    ai_comp.data["_dir"] = -ai_comp.data.get("_dir", 1)
                perp *= ai_comp.data.get("_dir", 1)
                vel.vec = perp * ai_comp.data["speed"] * 1.2
                # Occasionally attack while circling
                if ai_comp.timer > 1.0:
                    apc = self.component_manager.get(eid, AttackPatternComponent)
                    if apc:
                        apc.active = True
                    ai_comp.timer = 0
            else:
                # Charge toward player
                dir = (player_pos.vec - pos.vec).normalize()
                vel.vec = dir * ai_comp.data["speed"]
                if ai_comp.timer > 0.8:
                    ai_comp.state = EnemyState.ATTACK
                    ai_comp.timer = 0

        elif ai_comp.state == EnemyState.ATTACK:
            apc = self.component_manager.get(eid, AttackPatternComponent)
            if apc: apc.active = True

            # Fire while moving sideways
            if player_pos:
                perp = pygame.Vector2(-(player_pos.vec - pos.vec).y, (player_pos.vec - pos.vec).x)
                perp = perp.normalize() if perp.length_squared() > 0 else pygame.Vector2(1, 0)
                vel.vec = perp * ai_comp.data["speed"] * 0.8

            if ai_comp.timer > 1.5:
                if apc: apc.active = False
                ai_comp.state = EnemyState.CHASE
                ai_comp.timer = 0

    def _kiting_behavior(self, eid, ai_comp, dt):
        """Maintains distance from player, fires while retreating."""
        pos = self.component_manager.get(eid, Position)
        vel = self.component_manager.get(eid, Velocity)
        player_pos = self.component_manager.get(self.player_entity_id, Position)

        if ai_comp.state == EnemyState.IDLE:
            if ai_comp.timer > 0.3:
                ai_comp.state = EnemyState.FLEE
                ai_comp.timer = 0

        elif ai_comp.state == EnemyState.FLEE:
            if player_pos is None:
                return

            dist = pos.vec.distance_to(player_pos.vec)

            # Player too close -> retreat
            if dist < ai_comp.data.get("preferred_dist", 300):
                dir = (pos.vec - player_pos.vec).normalize()
                vel.vec = dir * ai_comp.data["speed"]
                # Shoot while retreating
                apc = self.component_manager.get(eid, AttackPatternComponent)
                if apc: apc.active = True
            # Good distance -> strafe and shoot
            elif dist < ai_comp.data.get("preferred_dist", 300) * 1.5:
                perp = pygame.Vector2(-(player_pos.vec - pos.vec).y, (player_pos.vec - pos.vec).x)
                perp = perp.normalize() if perp.length_squared() > 0 else pygame.Vector2(1, 0)
                if random.random() < 0.01:
                    ai_comp.data["_dir"] = -ai_comp.data.get("_dir", 1)
                perp *= ai_comp.data.get("_dir", 1)
                vel.vec = perp * ai_comp.data["speed"] * 0.6
                apc = self.component_manager.get(eid, AttackPatternComponent)
                if apc: apc.active = True
            else:
                # Too far -> approach slowly
                dir = (player_pos.vec - pos.vec).normalize()
                vel.vec = dir * ai_comp.data["speed"] * 0.4
                apc = self.component_manager.get(eid, AttackPatternComponent)
                if apc: apc.active = False

            # Switch to attack state briefly
            if ai_comp.timer > 3.0:
                ai_comp.state = EnemyState.ATTACK
                ai_comp.timer = 0

        elif ai_comp.state == EnemyState.ATTACK:
            apc = self.component_manager.get(eid, AttackPatternComponent)
            if apc: apc.active = True
            # Hold position briefly while firing
            vel.vec = (0, 0)
            if ai_comp.timer > 1.0:
                if apc: apc.active = False
                ai_comp.state = EnemyState.FLEE
                ai_comp.timer = 0

    def _support_behavior(self, eid, ai_comp, dt):
        """Stays near other enemies, creates hazards, buffs allies."""
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

            # Stay near other enemies (find nearest ally)
            nearest_ally = None
            nearest_dist = 999999
            for other_eid in self.component_manager.get_entities_with(AIComponent):
                if other_eid == eid:
                    continue
                other_pos = self.component_manager.get(other_eid, Position)
                if other_pos:
                    d = pos.vec.distance_to(other_pos.vec)
                    if d < nearest_dist:
                        nearest_dist = d
                        nearest_ally = other_pos

            dist = pos.vec.distance_to(player_pos.vec)

            # If too far from allies, move toward them
            if nearest_ally and nearest_dist > 200:
                dir = (nearest_ally.vec - pos.vec).normalize()
                vel.vec = dir * ai_comp.data["speed"]
            # If player is close, retreat while placing hazards
            elif dist < ai_comp.data["attack_dist"]:
                dir = (pos.vec - player_pos.vec).normalize()
                vel.vec = dir * ai_comp.data["speed"]
                apc = self.component_manager.get(eid, AttackPatternComponent)
                if apc: apc.active = True
            else:
                vel.vec = (0, 0)
                apc = self.component_manager.get(eid, AttackPatternComponent)
                if apc: apc.active = True

            if ai_comp.timer > 2.0:
                ai_comp.state = EnemyState.ATTACK
                ai_comp.timer = 0

        elif ai_comp.state == EnemyState.ATTACK:
            apc = self.component_manager.get(eid, AttackPatternComponent)
            if apc: apc.active = True
            vel.vec = (0, 0)
            if ai_comp.timer > 2.0:
                if apc: apc.active = False
                ai_comp.state = EnemyState.CHASE
                ai_comp.timer = 0

    def _sniper_behavior(self, eid, ai_comp, dt):
        pos = self.component_manager.get(eid, Position)
        vel = self.component_manager.get(eid, Velocity)
        player_pos = self.component_manager.get(self.player_entity_id, Position)

        # idle
        if ai_comp.state == EnemyState.IDLE:
            if ai_comp.timer > 0.5:
                ai_comp.state = EnemyState.FLEE
                ai_comp.timer = 0
        # flee away from the player
        elif ai_comp.state == EnemyState.FLEE:
            if player_pos is None:
                return
        
            if ai_comp.timer > 1:
                target_pos = player_pos.vec + pygame.Vector2(random.uniform(-200, 200), random.uniform(-200, 200))
                dir = (pos.vec - target_pos).normalize()
                vel.vec = dir * ai_comp.data["speed"]

                if pos.vec.distance_to(player_pos.vec) > 500:
                    vel.vec = (0, 0)
                    ai_comp.state = EnemyState.ATTACK
                    ai_comp.timer = 0
        # snipe the player from far
        elif ai_comp.state == EnemyState.ATTACK:
            apc = self.component_manager.get(eid, AttackPatternComponent)
            if ai_comp.timer > 0.5:
                if apc: apc.active = True
            if ai_comp.timer > 2:
                if apc: apc.active = False
                ai_comp.state = EnemyState.FLEE
                ai_comp.timer = 0

    def _patrol_behavior(self, eid, ai_comp, dt):
        print('patrolling', ai_comp.state)

    def update(self, dt):
        for eid in self.component_manager.get_entities_with(AIComponent):
            ai_comp = self.component_manager.get(eid, AIComponent)
            if ai_comp is None:
                continue

            if ai_comp.state == EnemyState.DEAD:
                continue
            
            ai_comp.timer += dt

            self.AI_FUNCS.get(ai_comp.behavior, self._default_behavior)(eid, ai_comp, dt)

            
