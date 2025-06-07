import pygame
from ..scene_manager import Scene
from ..ecs.component import Position, Velocity, AnimationComponent
from ..ecs.component_manager import ComponentManager
from ..ecs.entity_manager import EntityManager
from ..ecs.player import Player
from ..physics_engine import PhysicsEngine
from ..animation_handler import AnimationHandler
from ..render_system import AnimationSystem, RenderSystem

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
        self.animation_handler = AnimationHandler()
        self.physics_component_manager = ComponentManager()

        self.physics_engine = PhysicsEngine(self.physics_component_manager)
        self.animation_system = AnimationSystem(self.physics_component_manager)
        self.render_system = RenderSystem(self.physics_component_manager)

    def start(self, event_manager, input_system):
        print(f"[SCENE] Starting scene: '{self.id}' (DEBUG)")

        # Define keybinds for player movement
        # These are the events that will be emitted when the keys are pressed or released
        UP = "up"
        DOWN = "down"
        LEFT = "left"
        RIGHT = "right"
        UP_RELEASE = "up_release"
        DOWN_RELEASE = "down_release"
        LEFT_RELEASE = "left_release"
        RIGHT_RELEASE = "right_release"

        # Create a player entity
        self.player = Player(entity_id=self.entity_manager.create_entity())

        # self.physics_component_manager.add(self.player.entity_id, Position(10, 10))
        # self.physics_component_manager.add(self.player.entity_id, Velocity(0, 0, speed=1))
        self.physics_component_manager.add(self.player.entity_id, Position(10, 10), Velocity(0, 0, speed=5), AnimationComponent(
            animation_id="white_pawn_moving",
            animation_handler=self.animation_handler
        ))

        # Initialize game-specific components here
        # TEMP
        # keybinds

        # Subscribe to player movement events
        event_manager.subscribe(UP, lambda: self.player.on_move("up"))
        event_manager.subscribe(DOWN, lambda: self.player.on_move("down"))
        event_manager.subscribe(LEFT, lambda: self.player.on_move("left"))
        event_manager.subscribe(RIGHT, lambda: self.player.on_move("right"))

        event_manager.subscribe(UP_RELEASE, lambda: self.player.on_move("up", held=False))
        event_manager.subscribe(DOWN_RELEASE, lambda: self.player.on_move("down", held=False))
        event_manager.subscribe(LEFT_RELEASE, lambda: self.player.on_move("left", held=False))
        event_manager.subscribe(RIGHT_RELEASE, lambda: self.player.on_move("right", held=False))

        # Set up keybinds for input system
        input_system.set_keybinds(
            keys_held = {
                pygame.K_w: UP,
                pygame.K_s: DOWN,
                pygame.K_a: LEFT,
                pygame.K_d: RIGHT
            },
            keys_released = {
                pygame.K_w: UP_RELEASE,
                pygame.K_s: DOWN_RELEASE,
                pygame.K_a: LEFT_RELEASE,
                pygame.K_d: RIGHT_RELEASE
            }
        )

        # TEMP
  
    def update(self, dt):
        # Update the physics engine
        self.player.update(self.physics_component_manager) 
        self.animation_system.update(dt)
        self.physics_engine.update(dt)
    
    def render(self, surface):
        self.render_system.render(surface)
