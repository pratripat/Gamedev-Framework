import pygame
from ..scene_manager import Scene
from ..ecs.component import Position, Velocity, AnimationComponent, RenderComponent
from ..ecs.component_manager import ComponentManager
from ..ecs.entity_manager import EntityManager
from ..ecs.player import Player
from ..physics_engine import PhysicsEngine
from ..animation_handler import AnimationHandler
from ..animation_state_machine import AnimationStateMachine
from ..render_system import AnimationSystem, RenderSystem
from ..camera import Camera

import random

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
        self.camera = Camera()

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
        LEFT_CLICK = "left_click"
        RIGHT_CLICK = "right_click"
        LEFT_HOLD = "left_hold"
        RIGHT_HOLD = "right_hold"

        # Create a player entity
        self.player = Player(entity_id=self.entity_manager.create_entity())

        # self.physics_component_manager.add(self.player.entity_id, Position(10, 10))
        # self.physics_component_manager.add(self.player.entity_id, Velocity(0, 0, speed=1))
        self.physics_component_manager.add(
            self.player.entity_id, 
            Position(self.player.entity_id, 10, 10), 
            Velocity(self.player.entity_id, 0, 0, speed=5), 
            AnimationComponent(
                entity_id=self.player.entity_id,
                entity="black_pawn",
                animation_id="idle",
                animation_handler=self.animation_handler,
                event_manager=event_manager,
                center=True,
                entity_type="chess_piece"
            ),
            AnimationStateMachine(
                entity_id = self.player.entity_id,
                component_manager=self.physics_component_manager,
                event_manager=event_manager,
                animation_priority_list = [
                    "idle",
                    "shoot",
                    "moving",
                    "death"
                ],
                transitions = {
                    "moving": {
                        "to_animation": "idle", 
                        "cond": lambda: self.physics_component_manager.get(self.player.entity_id, Velocity).vec.length_squared() == 0,
                        "self_dest": False
                    },
                    "shoot": {
                        "to_animation": "idle", 
                        "cond": lambda: input_system.mouse_states['left_held'] == False,
                        "self_dest": False
                    }
                }
            )
        )

        for i in range(2):
            enemy = self.entity_manager.create_entity()

            self.physics_component_manager.add(enemy, 
                Position(enemy, 100, 100), 
                Velocity(enemy, random.uniform(0,1), random.uniform(0,1), speed=5), 
                AnimationComponent(
                    entity_id=enemy,
                    entity="black_pawn",
                    animation_id="idle",
                    animation_handler=self.animation_handler,
                    event_manager=event_manager,
                    center=True,
                    entity_type="chess_piece"
                ),
                AnimationStateMachine(
                    entity_id = enemy,
                    component_manager=self.physics_component_manager,
                    event_manager=event_manager,
                    animation_priority_list = [
                        "idle",
                        "shoot",
                        "moving",
                        "death"
                    ],
                    transitions = {
                        "moving": {
                            "to_animation": "idle", 
                            "cond": lambda: self.physics_component_manager.get(enemy, Velocity).vec.length_squared() == 0,
                            "self_dest": False
                        },
                        "shoot": {
                            "to_animation": "idle", 
                            "cond": lambda: input_system.mouse_states['left_held'] == False,
                            "self_dest": False
                        }
                    }
                )
            )

        self.camera.set_target(self.player.entity_id)

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
        
        event_manager.subscribe(LEFT_HOLD, lambda: self.physics_component_manager.get(self.player.entity_id, AnimationStateMachine).set_animation("shoot"))

        # Set up keybinds for input system
        input_system.set_input_binds(
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
            },
            mouse_clicked = {
                pygame.BUTTON_LEFT: LEFT_CLICK,
                pygame.BUTTON_RIGHT: RIGHT_CLICK
            },
            mouse_held = {
                pygame.BUTTON_LEFT: LEFT_HOLD,
                pygame.BUTTON_RIGHT: RIGHT_HOLD
            }
        )

        # TEMP
  
    def update(self, dt):
        # Update the physics engine
        self.player.update(self.physics_component_manager) 
        self.animation_system.update(dt)
        self.physics_engine.update(dt)

        self.camera.update(self.physics_component_manager, lerp=True, mouse=pygame.mouse.get_pos(), mouse_ratio=0.05)
    
    def render(self, surface):
        self.render_system.render(surface, self.camera)
