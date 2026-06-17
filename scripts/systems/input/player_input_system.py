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
        self.on_land_completely = True
        self.on_water_completely = False
        self.is_touching_water = False
        self.dash_extension_timer = 0.0 # Safety limit for water extension
        self.dash_start_pos = pygame.Vector2(0, 0)

        self.ghost_interval = 0.03 # Spawn approx 5 ghosts during 0.15s dash
        self.ghost_timer = 0.0

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

        # Record start position for water respawn
        pos = cm.get(self.entity_id, Position)
        if pos:
            self.dash_start_pos = pos.vec.copy()
        
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
                "radius": 75
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
    
    def on_death(self, entity_id, **kwargs):
        if self.entity_id == entity_id:
            self.disable_movement = True
            self.is_dashing = False

    def check_water_death(self, cm, respawn_pos=None):
        # Request a formal water check and potential respawn from the scene
        pos = cm.get(self.entity_id, Position)
        if pos:
            self.event_manager.emit('request_water_check', entity_id=self.entity_id, pos=pos.vec.copy(), respawn_pos=respawn_pos)

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
        
        # Safety: handle dash end and extensions
        if self.is_dashing:
            # GHOST LOGIC: Spawn ghosts at intervals
            from ...components.animation import AnimationComponent
            anim = component_manager.get(self.entity_id, AnimationComponent)
            pos = component_manager.get(self.entity_id, Position)
            if anim and pos:
                self.ghost_timer += dt
                if self.ghost_timer >= self.ghost_interval:
                    self.ghost_timer = 0
                    self.event_manager.emit(GameSceneEvents.SPAWN_GHOST, 
                        image=anim.current_image, 
                        pos=pos.vec.copy(), 
                        offset=anim.offset.copy()
                    )

            if self.dash_timer > 0:
                self.dash_timer -= dt
                self.dash_extension_timer = 0.0 # reset extension during normal dash
            else:
                # Normal dash duration is over. Check terrain
                if self.on_water_completely:
                    # Deep in water: Die and respawn at dash start
                    self.is_dashing = False
                    self.check_water_death(component_manager, respawn_pos=self.dash_start_pos)
                    self.dash_extension_timer = 0.0
                elif not self.is_touching_water:
                    # Safe on solid ground: stop
                    self.is_dashing = False
                    self.dash_cooldown_timer = self.dash_cooldown
                    self.dash_extension_timer = 0.0
                else:
                    # PARTIALLY TOUCHING WATER: Extend dash until completely on land
                    self.dash_extension_timer += dt
                    # Safety timeout
                    if self.dash_extension_timer > 1.5: # Lowered safety timeout
                        self.is_dashing = False
                        self.check_water_death(component_manager, respawn_pos=self.dash_start_pos)
                        self.dash_extension_timer = 0.0

        if self.is_dashing:
            # During dash (or extension), move at high speed
            vel.vec = self.dash_dir * vel.speed * self.dash_speed_mult
            return

        # NEW: Constant water check when NOT dashing to prevent staying in water
        if self.on_water_completely:
            self.check_water_death(component_manager)

        # Normal movement
        dir = pygame.Vector2(0, 0)
        if self.held["up"]: dir.y -= 1
        if self.held["down"]: dir.y += 1
        if self.held["left"]: dir.x -= 1
        if self.held["right"]: dir.x += 1

        if dir.length_squared() > 0: dir = dir.normalize()

        vel.vec = dir * vel.speed # setting the velocity based on direction and speed
