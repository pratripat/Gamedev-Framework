import pygame
from ...components.physics import Velocity, Position
from ...weapons.bullet_patterns import spawn_bomb

from ...utils import GameSceneEvents

class PlayerInputSystem:
    def __init__(self, entity_id, event_manager):
        """
        Initializes a player with a given entity ID.

        :param entity_id: The unique identifier for the player entity.
        """
        self.entity_id = entity_id
        self.held = {
            "up": False,
            "down": False,
            "left": False,
            "right": False
        }
        self.disable_movement = False

        # Bomb cooldown state
        self.bomb_cooldown = 3.0  # seconds
        self.bomb_timer = 0.0

        # Dash state
        self.dash_max_charges = 3
        self.dash_charges = self.dash_max_charges
        self.dash_refill_cooldown = 0.7  # seconds per charge
        self.dash_refill_timer = 0.0
        
        self.dash_duration = 0.15
        self.dash_speed_mult = 4.0
        self.dash_timer = 0.0
        self.dash_dir = pygame.Vector2(0, 0)
        self.is_dashing = False
        self.dash_key_pressed = False
        self.dash_cooldown = 0.1   # seconds between dashes
        self.dash_cooldown_timer = 0.0

        self.event_manager = event_manager
        event_manager.subscribe(GameSceneEvents.DEATH, self.on_death)

    def on_bomb_release(self):
        pass
    
    def on_dash_release(self):
        self.dash_key_pressed = False

    def dash(self, cm):
        # Only dash if charges available, not currently dashing, key was released, and inter-dash cooldown passed
        if self.dash_charges <= 0 or self.is_dashing or self.dash_key_pressed or self.dash_cooldown_timer > 0:
            return
        
        self.dash_key_pressed = True
        
        # Determine dash direction based on current input
        dir = pygame.Vector2(0, 0)
        if self.held["up"]: dir.y -= 1
        if self.held["down"]: dir.y += 1
        if self.held["left"]: dir.x -= 1
        if self.held["right"]: dir.x += 1

        if dir.length_squared() == 0:
            return

        self.dash_dir = dir.normalize()
        self.is_dashing = True
        self.dash_timer = self.dash_duration
        self.dash_charges -= 1
        
        # Emit dash start event for render effects
        self.event_manager.emit(GameSceneEvents.DASH_START, entity_id=self.entity_id, duration=self.dash_duration)

        # Reset refill timer whenever we dash; refill only starts after dash_refill_cooldown of NO dashing
        self.dash_refill_timer = self.dash_refill_cooldown

        # Grant invulnerability
        from ...components.combat import HealthComponent
        health = cm.get(self.entity_id, HealthComponent)
        if health:
            health.invincibility_timer = max(health.invincibility_timer, self.dash_duration)

    def spawn_bomb(self, cm, em, anim_handler, event_manager):
        # Only spawn if cooldown elapsed
        if self.bomb_timer > 0:
            return None

        bomb_id = spawn_bomb(
            self.entity_id, 
            cm, 
            em, 
            anim_handler, 
            event_manager, 
            data = {
                "pos": cm.get(self.entity_id, Position).vec.copy(),
                "timer": 0.75,
                "radius": 150
            }
        )

        # start cooldown
        if bomb_id is not None:
            self.bomb_timer = self.bomb_cooldown

        return bomb_id

    def shoot(self, event_manager):
        if not self.is_dashing:
            event_manager.emit(GameSceneEvents.SHOOT, entity_id=self.entity_id)

    def on_move(self, direction, held=True):
        self.held[direction] = held
    
    def on_death(self, entity_id):
        if self.entity_id == entity_id:
            self.disable_movement = True
            self.is_dashing = False

    def update(self, component_manager, dt):
        # Update bomb cooldown timer
        if self.bomb_timer > 0:
            self.bomb_timer -= dt
            if self.bomb_timer < 0:
                self.bomb_timer = 0

        # Update dash refill logic
        if self.dash_charges < self.dash_max_charges:
            self.dash_refill_timer -= dt
            if self.dash_refill_timer <= 0:
                self.dash_charges += 1
                # If still below max, wait another full cooldown for the next charge
                if self.dash_charges < self.dash_max_charges:
                    self.dash_refill_timer = self.dash_refill_cooldown
                else:
                    self.dash_refill_timer = 0
        
        # Ensure charges never exceed max
        self.dash_charges = min(self.dash_charges, self.dash_max_charges)

        # Update inter-dash cooldown
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt

        if self.disable_movement:
            return

        vel = component_manager.get(self.entity_id, Velocity)
        
        # Safety: reset dashing state if timer is up
        if self.is_dashing and self.dash_timer <= 0:
            self.is_dashing = False
            self.dash_cooldown_timer = self.dash_cooldown # Start inter-dash cooldown

        if self.is_dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.dash_timer = 0
            
            # During dash, move at high speed in dash direction
            vel.vec = self.dash_dir * vel.speed * self.dash_speed_mult
            return

        # Normal movement
        dir = pygame.Vector2(0, 0)
        if self.held["up"]: dir.y -= 1
        if self.held["down"]: dir.y += 1
        if self.held["left"]: dir.x -= 1
        if self.held["right"]: dir.x += 1

        if dir.length_squared() > 0: dir = dir.normalize()

        vel.vec = dir * vel.speed # setting the velocity based on direction and speed
        