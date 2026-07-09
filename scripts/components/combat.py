import pygame

from scripts.ecs.component_manager import ComponentManager
from scripts.systems.core.event_manager import EventManager
from ..utils import GameSceneEvents
from ..systems.animation.animation_state_machine import AnimationStateMachine

class WeaponComponent:
    def __init__(self, cooldown, shoot_fn, projectile_data):
        self.cooldown = cooldown
        self.shoot_fn = shoot_fn
        self.projectile_data = projectile_data

        self.time = 0
        self.shot = False
        self.disabled = False

    @property
    def can_shoot(self):
        return not self.shot

class HitBoxComponent:
    def __init__(self, entity_id, offset, size, shape, layer: int, mask: int, center=True):
        self.entity_id = entity_id
        self.offset = pygame.Vector2(offset)
        self.size = size
        self.shape = shape
        self.layer = layer
        self.mask = mask
        self.disabled = False

        if center:
            self.offset -= pygame.Vector2(size) / 2

class HurtBoxComponent:
    def __init__(self, entity_id, offset, size, shape, layer: int, center=True):
        self.entity_id = entity_id
        self.offset = pygame.Vector2(offset)
        self.size = size
        self.shape = shape
        self.layer = layer
        self.disabled = False
        
        if center:
            self.offset -= pygame.Vector2(size) / 2

class HealthComponent:
    iframetimer = 1/6
    def __init__(self, entity_id, max_health, event_manager: EventManager, component_manager: ComponentManager):
        self.entity_id = entity_id
        self.health = self.max_health = max_health
        self.invincibility_timer = 0
        self.event_manager = event_manager
        self.component_manager = component_manager

        self.effects = []

        event_manager.subscribe(GameSceneEvents.DAMAGE, self.take_damage, source=self.entity_id)

    def take_damage(self, entity_id, proj_id, damage, effects, **kwargs):
        if entity_id != self.entity_id:
            return
        
        if self.invincibility_timer > 0:
            # Still invincible, ignore damage
            return
        
        self.health -= damage
        self.effects = effects

        # if self.entity_id == 0: # TEMP: Assuming entity_id 0 is the player
        #     print(f"[HEALTH COMPONENT] Player took {damage} damage, health now: {self.health}")

        # TEMP
        # set animation to hit
        # self.component_manager.get(self.entity_id, AnimationStateMachine).set_animation("damage")

        self.invincibility_timer = self.iframetimer
        if self.health <= 0:
            self.health = 0
            # Trigger death logic here, e.g., event_manager.publish("entity_died", self.entity_id)
            self.event_manager.emit(GameSceneEvents.DEATH, entity_id=self.entity_id, proj_vel=kwargs.get('proj_vel'), proj_pos=kwargs.get('proj_pos'), death=True)
        
class AttackPattern:
    def __init__(self, shoot_fn, projectile_data, cooldown, duration, warmup=0.0, tier="light", tier_cooldown=0.0):
        self.shoot_fn = shoot_fn
        self.projectile_data = projectile_data
        self.cooldown = cooldown      # time between shots within this pattern
        self.duration = duration      # how long this pattern lasts before cycling to next
        self.warmup = warmup or 0.0   # telegraph delay before first shot fires
        self.tier = tier              # "light", "heavy", "signature"
        self.tier_cooldown = tier_cooldown  # global cooldown before this tier can be used again
        self.shoot_timer = 0
        self.phase_timer = 0
        self.warmed = False           # becomes True after warmup elapses
        self._last_used = -999.0      # time when this pattern was last used

class AttackPatternComponent:
    def __init__(self, patterns: list[AttackPattern], loop=True):
        self.patterns = patterns
        self.current_index = 0
        self.loop = loop
        self.active = False           # Controlled by the AI system
        self.disabled = False
        self._last_attack_tier = "light"
        self._consecutive_light = 0

    @property
    def current(self):
        return self.patterns[self.current_index]
    
    def advance(self):
        if self.current_index < len(self.patterns) - 1:
            self.current_index += 1
        elif self.loop:
            self.current_index = 0
        # reset timers on advance
        self.current.shoot_timer = 0
        self.current.phase_timer = 0
        self.current.warmed = False

    def select_pattern(self, dist_to_player, time_since_last):
        """Choose the best pattern based on distance and cooldown tiers."""
        eligible = []
        for i, p in enumerate(self.patterns):
            if time_since_last - p._last_used < p.tier_cooldown:
                continue  # still on tier cooldown
            range_min = p.projectile_data.get("range_min", 0)
            if range_min is None:
                range_min = 0
            range_max = p.projectile_data.get("range", 9999)
            if range_max is None:
                range_max = 9999
            if dist_to_player < range_min or dist_to_player > range_max:
                continue  # out of range for this attack
            eligible.append((i, p))

        if not eligible:
            eligible = [(i, p) for i, p in enumerate(self.patterns)]

        # Prefer alternating tiers: avoid using the same tier twice in a row
        tier_order = {"light": 0, "heavy": 1, "signature": 2}
        def sort_key(item):
            _, p = item
            # Prefer different tier from last attack
            same_tier = 1 if p.tier == self._last_attack_tier else 0
            # Prefer heavy/signature less often
            tier_priority = tier_order.get(p.tier, 0)
            return (same_tier, -tier_priority)

        eligible.sort(key=sort_key)
        import random
        idx, chosen = eligible[0] if len(eligible) == 1 else random.choice(eligible[:2])
        self.current_index = idx
        self._last_attack_tier = chosen.tier
        if chosen.tier == "light":
            self._consecutive_light += 1
        else:
            self._consecutive_light = 0
        chosen._last_used = time_since_last
        # Reset the chosen pattern
        chosen.shoot_timer = 0
        chosen.phase_timer = 0
        chosen.warmed = False

