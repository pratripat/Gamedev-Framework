import pygame
from ..systems.scene.scene_manager import Scene
#components
from ..components.physics import Position, Velocity, CollisionComponent
from ..components.animation import AnimationComponent, RenderComponent
from ..components.combat import WeaponComponent, HitBoxComponent, HurtBoxComponent, HealthComponent
from ..components.tags import PlayerTagComponent, EnemyTagComponent
from ..ecs.component_manager import ComponentManager

#systems
from ..ecs.entity_manager import EntityManager
from ..ecs.entity_factory import EntityFactory
from ..systems.input.player_input_system import PlayerInputSystem
from ..systems.core.physics_engine import PhysicsEngine
from ..systems.animation.animation_handler import AnimationHandler
from ..systems.animation.animation_state_machine import AnimationStateMachine
from ..systems.rendering.render_system import AnimationSystem, RenderSystem
from ..systems.rendering.camera import Camera
from ..systems.combat.combat_system import CombatSystem

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

        self.physics_engine = PhysicsEngine(self.physics_component_manager)
        self.animation_system = AnimationSystem(self.physics_component_manager)
        self.render_system = RenderSystem(self.physics_component_manager)
        self.combat_system = CombatSystem(self.physics_component_manager, self.entity_manager, self.camera, event_manager)

    def start(self, input_system):
        print(f"[SCENE] Starting scene: '{self.id}' (DEBUG)")

        # Create a player entity
        # self.player = self.entity_manager.create_entity(player=True)
        
        self.player = self.entity_factory.create_player(
            component_manager=self.physics_component_manager,
            entity_manager=self.entity_manager,
            event_manager=self.event_manager,
            animation_handler=self.animation_handler,
            input_system=input_system
        )
        self.player_input_system = PlayerInputSystem(entity_id=self.player)

        shoot_radial_rotate = SpiralShooter()

        # self.physics_component_manager.add(            
        #     self.player, 
        #     PlayerTagComponent(),
        #     Position(self.player, 10, 10), 
        #     Velocity(self.player, 0, 0, speed=4), 
        #     AnimationComponent(
        #         entity_id=self.player,
        #         entity="white_pawn",
        #         animation_id="idle",
        #         animation_handler=self.animation_handler,
        #         event_manager=self.event_manager,
        #         center=True,
        #         entity_type="chess_piece"
        #     ),
        #     AnimationStateMachine(
        #         entity_id = self.player,
        #         component_manager=self.physics_component_manager,
        #         event_manager=self.event_manager,
        #         animation_priority_list = [
        #             "idle",
        #             "shoot",
        #             "moving",
        #             "damage",
        #             "death"
        #         ],
        #         transitions = {
        #             "moving": {
        #                 "to_animation": "idle", 
        #                 "cond": (lambda eid=self.player: self.physics_component_manager.get(eid, Velocity).vec.length_squared() == 0),
        #                 "self_dest": False
        #             },
        #             "shoot": {
        #                 "to_animation": "idle", 
        #                 "cond": (lambda: input_system.mouse_states['left_held'] == False),
        #                 "self_dest": False
        #             }
        #         }
        #     ),
        #     WeaponComponent(
        #         cooldown=1/100,
        #         shoot_fn=shoot_spread,
        #         projectile_data={
        #             "damage": 20,
        #             "speed": 10,
        #             "range": 100,
        #             "effects": [],
        #             "size": 1,
        #             "image_file": "data/graphics/images/projectile.png",
        #             "angle": 3,
        #             "number": 10
        #         }
        #     ),
        #     HurtBoxComponent(
        #         entity_id=self.player, 
        #         offset=(0, 0), 
        #         size=(16, 64), 
        #         shape=CollisionShape.RECT, 
        #         layer=CollisionLayer.PLAYER
        #     ),
        #     HealthComponent(
        #         entity_id=self.player,
        #         max_health=100,
        #         event_manager=self.event_manager,
        #         component_manager=self.physics_component_manager
        #     ),
        #     CollisionComponent(
        #         entity_id=self.player,
        #         offset=(0, 0),
        #         size=(32, 32),
        #         center=True
        #     )
        # )

        for i in range(100):
            # add a collision block
            block = self.entity_manager.create_entity()
            self.physics_component_manager.add(
                block,
                Position(block, -400+i*32, 50),
                # RenderComponent(
                #     entity_id=block,
                #     surface=load_image('data/graphics/animations/black_rook.png'),
                #     offset=(0, 0),
                #     center=True
                # ),
                CollisionComponent(
                    entity_id=block,
                    offset=(0, 0),
                    size=(32, 32),
                    solid=True
                )
            )

        # create some enemy entities
        for i in range(1):
            enemy = self.entity_manager.create_entity()

            self.physics_component_manager.add(enemy, 
                EnemyTagComponent(),
                Position(enemy, 50, random.uniform(-50, 50)), 
                Velocity(enemy, random.uniform(-0.5, 0.5), random.uniform(0, 1), speed=5), 
                AnimationComponent(
                    entity_id=enemy,
                    entity="black_pawn",
                    animation_id="moving",
                    animation_handler=self.animation_handler,
                    event_manager=self.event_manager,
                    center=True,
                    entity_type="chess_piece"
                ),
                AnimationStateMachine(
                    entity_id = enemy,
                    component_manager=self.physics_component_manager,
                    event_manager=self.event_manager,
                    animation_priority_list = [
                        "idle",
                        "shoot",
                        "moving",
                        "damage",
                        "death"
                    ],
                    transitions = {
                        "moving": {
                            "to_animation": "idle", 
                            "cond": (lambda eid=enemy: self.physics_component_manager.get(eid, Velocity).vec.length_squared() == 0),
                            "self_dest": False
                        }
                    }
                ),
                WeaponComponent(
                    cooldown=1/6,
                    shoot_fn=shoot_spread,
                    projectile_data={
                        "damage": 10,
                        "speed": 5,
                        "range": 100,
                        "effects": [],
                        "size": 1,
                        "image_file": "data/graphics/images/projectile.png",
                        "towards_player": True,
                        "angle": 3
                    }
                ),
                HurtBoxComponent(
                    entity_id=enemy, 
                    offset=(0, 0), 
                    size=(32, 32), 
                    shape=CollisionShape.RECT, 
                    layer=CollisionLayer.ENEMY
                ),
                HealthComponent(
                    entity_id=enemy,
                    max_health=100,
                    event_manager=self.event_manager,
                    component_manager=self.physics_component_manager
                ),
                CollisionComponent(
                    entity_id=enemy,
                    offset=(0, 0),
                    size=(32, 32),
                    center=True,
                    solid=False
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
        
        self.event_manager.subscribe(Inputs.LEFT_HOLD, lambda: self.player_input_system.shoot(self.physics_component_manager, self.event_manager), source=self.player)

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

        self.camera.update(self.physics_component_manager, lerp=True, mouse=pygame.mouse.get_pos(), mouse_ratio=0.05)
    
        self.entity_manager.refresh_entities()

    def render(self, surface):
        self.render_system.render(surface, self.camera)

        # render all the hurtboxs and hitboxes
        # boxes = self.physics_component_manager.get_entities_with_either(HurtBoxComponent, HitBoxComponent)
        # for entity_id in boxes:
        #     hurtbox = self.physics_component_manager.get(entity_id, HurtBoxComponent)
        #     hitbox = self.physics_component_manager.get(entity_id, HitBoxComponent)
        #     pos = self.physics_component_manager.get(entity_id, Position).vec

        #     if hurtbox:
        #         pygame.draw.rect(surface, (255, 0, 0), (*pos + hurtbox.offset - self.camera.scroll, *hurtbox.size), 1)
        #     if hitbox:
        #         pygame.draw.rect(surface, (0, 255, 0), (*pos + hitbox.offset - self.camera.scroll, *hitbox.size), 1)

        boxes = self.physics_component_manager.get_entities_with(CollisionComponent)
        for entity_id in boxes:
            collision_component = self.physics_component_manager.get(entity_id, CollisionComponent)
            pos = self.physics_component_manager.get(entity_id, Position).vec

            if collision_component:
                pygame.draw.rect(surface, (255, 255, 255), (*pos + collision_component.offset - self.camera.scroll, *collision_component.size), 1)