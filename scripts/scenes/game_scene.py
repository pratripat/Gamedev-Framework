import pygame
from ..systems.scene.scene_manager import Scene
#components
from ..components.physics import Position, Velocity, CollisionComponent
from ..components.combat import HitBoxComponent, HurtBoxComponent
from ..ecs.component_manager import ComponentManager
from ..components.ai import AIComponent

#systems
from ..ecs.entity_manager import EntityManager
from ..ecs.entity_factory import EntityFactory
from ..systems.input.player_input_system import PlayerInputSystem
from ..systems.core.physics_engine import PhysicsEngine
from ..systems.animation.animation_handler import AnimationHandler
from ..systems.rendering.render_system import AnimationSystem, RenderSystem
from ..systems.rendering.camera import Camera
from ..systems.combat.combat_system import CombatSystem
from ..systems.combat.ai_system import AISystem

from ..weapons.bullet_patterns import *

from ..utils import Inputs, CollisionShape, CollisionLayer

import random

class GameScene(Scene):
    """
    Represents the main game scene, managing entities, components, and physics.
    """
    def __init__(self, event_manager):
        """
        Initializes the game scene with an entity manager, component manager, and physics engine.
        """
        super().__init__(id="game")
        self.animation_handler = AnimationHandler()
        self.physics_component_manager = ComponentManager()
        self.event_manager = event_manager
        self.camera = Camera()

        self.entity_manager = EntityManager(component_manager=self.physics_component_manager, event_manager=event_manager)
        self.entity_factory = EntityFactory()

        self.physics_engine = PhysicsEngine(self.physics_component_manager, self.event_manager)
        self.animation_system = AnimationSystem(self.physics_component_manager)
        self.render_system = RenderSystem(event_manager, self.physics_component_manager)
        self.combat_system = CombatSystem(self.physics_component_manager, self.entity_manager, self.camera, event_manager)

    def start(self, input_system):
        print(f"[SCENE] Starting scene: '{self.id}' (DEBUG)")

        # Create a player entity
        self.player = self.entity_factory.create_player(
            component_manager=self.physics_component_manager,
            entity_manager=self.entity_manager,
            event_manager=self.event_manager,
            animation_handler=self.animation_handler,
            input_system=input_system
        )
        self.player_input_system = PlayerInputSystem(entity_id=self.player, event_manager=self.event_manager)
        self.ai_system = AISystem(player_entity_id=self.player, component_manager=self.physics_component_manager, event_manager=self.event_manager)

        for i in range(10):
            coll_box = self.entity_factory.create_entity(
                entity="collision_box",
                component_manager=self.physics_component_manager,
                entity_manager=self.entity_manager,
                event_manager=self.event_manager,
                animation_handler=self.animation_handler,
                input_system=input_system
            )

            self.physics_component_manager.get(coll_box, Position).vec = (i*32, -200)

        for i in range(1):
            enemy = self.entity_factory.create_enemy(
                component_manager=self.physics_component_manager,
                entity_manager=self.entity_manager,
                event_manager=self.event_manager,
                animation_handler=self.animation_handler,
                input_system=input_system,
                chess_piece_type="pawn"
            )

            # Set random position and velocity for the enemy
            self.physics_component_manager.get(enemy, Position).x = 200
            self.physics_component_manager.get(enemy, Position).y = i*100

            self.physics_component_manager.add(
                enemy, 
                AIComponent(
                    entity_id=enemy,
                    behavior="sniper"  # or "sniper", "patrol", etc.
                )
            )

        self.camera.set_target(self.player)

        # Initialize game-specific components here
        # TEMP
        # keybinds

        # Subscribe to player input events
        self.event_manager.subscribe(Inputs.UP, lambda: self.player_input_system.on_move("up"), source=self.player)
        self.event_manager.subscribe(Inputs.DOWN, lambda: self.player_input_system.on_move("down"), source=self.player)
        self.event_manager.subscribe(Inputs.LEFT, lambda: self.player_input_system.on_move("left"), source=self.player)
        self.event_manager.subscribe(Inputs.RIGHT, lambda: self.player_input_system.on_move("right"), source=self.player)

        self.event_manager.subscribe(Inputs.UP_RELEASE, lambda: self.player_input_system.on_move("up", held=False), source=self.player)
        self.event_manager.subscribe(Inputs.DOWN_RELEASE, lambda: self.player_input_system.on_move("down", held=False), source=self.player)
        self.event_manager.subscribe(Inputs.LEFT_RELEASE, lambda: self.player_input_system.on_move("left", held=False), source=self.player)
        self.event_manager.subscribe(Inputs.RIGHT_RELEASE, lambda: self.player_input_system.on_move("right", held=False), source=self.player)
        
        self.event_manager.subscribe(Inputs.LEFT_HOLD, lambda: self.player_input_system.shoot(self.render_system.render_effect_system, self.event_manager), source=self.player)

        # Set up keybinds for input system
        input_system.set_input_binds(
            keys_held = {
                pygame.K_w: Inputs.UP,
                pygame.K_s: Inputs.DOWN,
                pygame.K_a: Inputs.LEFT,
                pygame.K_d: Inputs.RIGHT
            },
            keys_released = {
                pygame.K_w: Inputs.UP_RELEASE,
                pygame.K_s: Inputs.DOWN_RELEASE,
                pygame.K_a: Inputs.LEFT_RELEASE,
                pygame.K_d: Inputs.RIGHT_RELEASE
            },
            mouse_clicked = {
                pygame.BUTTON_LEFT: Inputs.LEFT_CLICK,
                pygame.BUTTON_RIGHT: Inputs.RIGHT_CLICK
            },
            mouse_held = {
                pygame.BUTTON_LEFT: Inputs.LEFT_HOLD,
                pygame.BUTTON_RIGHT: Inputs.RIGHT_HOLD
            }
        )

        # TEMP
  
    def update(self, fps, dt):
        # Update the physics engine
        self.player_input_system.update(self.physics_component_manager) 
        self.ai_system.update(fps, dt)
        self.physics_engine.update(self.camera.scroll, dt)
        self.combat_system.update(
            event_manager=self.event_manager,
            component_manager=self.physics_component_manager,
            entity_list=self.physics_component_manager.get_entities_with_either(HurtBoxComponent, HitBoxComponent),
            scroll=self.camera.scroll,
            fps=fps,
            dt=dt
        )
        self.animation_system.update(dt)
        self.render_system.update(fps, dt)

        self.camera.update(self.physics_component_manager, lerp=True, mouse=pygame.mouse.get_pos(), mouse_ratio=0.1)
    
        self.entity_manager.refresh_entities()

    def render(self, surface):
        self.render_system.render(surface, self.camera)

        # # render all the hurtboxs and hitboxes
        # boxes = self.physics_component_manager.get_entities_with_either(HurtBoxComponent, HitBoxComponent)
        # for entity_id in boxes:
        #     hurtbox = self.physics_component_manager.get(entity_id, HurtBoxComponent)
        #     hitbox = self.physics_component_manager.get(entity_id, HitBoxComponent)
        #     pos = self.physics_component_manager.get(entity_id, Position).vec

        #     if hurtbox:
        #         pygame.draw.rect(surface, (255, 0, 0), (*pos + hurtbox.offset - self.camera.scroll, *hurtbox.size), 1)
        #     if hitbox:
        #         pygame.draw.rect(surface, (0, 255, 0), (*pos + hitbox.offset - self.camera.scroll, *hitbox.size), 1)

        # boxes = self.physics_component_manager.get_entities_with(CollisionComponent)
        # for entity_id in boxes:
        #     collision_component = self.physics_component_manager.get(entity_id, CollisionComponent)
        #     pos = self.physics_component_manager.get(entity_id, Position).vec

        #     if collision_component:
        #         pygame.draw.rect(surface, (255, 255, 255), (*pos + collision_component.offset - self.camera.scroll, *collision_component.size), 1)