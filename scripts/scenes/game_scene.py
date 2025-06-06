import pygame
from ..scene_manager import Scene
from ..ecs.component_manager import ComponentManager, Position, Velocity
from ..ecs.entity_manager import EntityManager
from ..physics_engine import PhysicsEngine

class GameScene(Scene):
    """
    Represents the main game scene, managing entities, components, and physics.
    """
    def __init__(self):
        """
        Initializes the game scene with an entity manager, component manager, and physics engine.
        """
        super().__init__(id="game")
        self.entity_manager = EntityManager()
        self.physics_component_manager = ComponentManager()
        self.physics_engine = PhysicsEngine(self.physics_component_manager)
    
    def move_player(self, dx=None, dy=None):
        vel = self.physics_component_manager.get(self.player, Velocity)
        if dx is not None: vel.x = dx
        if dy is not None: vel.y = dy

        print(vel, end='\r')

    def start(self, event_manager, input_system):
        print(f"[SCENE] Starting scene: '{self.id}' (DEBUG)")

        # Initialize game-specific components here
        # TEMP
        # keybinds

        self.player = self.entity_manager.create_entity()

        self.physics_component_manager.add(self.player, Position(10, 10))
        self.physics_component_manager.add(self.player, Velocity(0, 0))

        event_manager.subscribe("player_up", lambda: self.move_player(dy = -1))
        event_manager.subscribe("player_down", lambda: self.move_player(dy = 1))
        event_manager.subscribe("player_left", lambda: self.move_player(dx = -1))
        event_manager.subscribe("player_right", lambda: self.move_player(dx = 1))

        event_manager.subscribe("player_stop_up", lambda: self.move_player(dy = 0))
        event_manager.subscribe("player_stop_down", lambda: self.move_player(dy = 0))
        event_manager.subscribe("player_stop_left", lambda: self.move_player(dx = 0))
        event_manager.subscribe("player_stop_right", lambda: self.move_player(dx = 0))

        input_system.set_keybinds(
            keys_held = {
                pygame.K_w: "player_up",
                pygame.K_s: "player_down",
                pygame.K_a: "player_left",
                pygame.K_d: "player_right"
            },
            keys_released = {
                pygame.K_w: "player_stop_up",
                pygame.K_s: "player_stop_down",
                pygame.K_a: "player_stop_left",
                pygame.K_d: "player_stop_right"
            }
        )

        # TEMP
  
    def update(self, dt):
        # Update the physics engine
        self.physics_engine.update(dt)
    