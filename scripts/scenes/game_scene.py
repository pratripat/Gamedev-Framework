import pygame, math

from scripts.components.combat import HealthComponent
from ..systems.scene.scene_manager import Scene
#components
from ..components.physics import Position, Velocity, CollisionComponent
# from ..components.combat import HitBoxComponent, HurtBoxComponent
from ..components.render_effect import RenderEffectComponent, YSortRender
from ..ecs.component_manager import ComponentManager
# from ..components.ai import AIComponent

#systems
from ..systems.core.timer_system import TimerSystem
from ..ecs.entity_manager import EntityManager
from ..ecs.entity_factory import EntityFactory
from ..systems.input.player_input_system import PlayerInputSystem
from ..systems.core.physics_engine import PhysicsEngine
# from ..systems.animation.animation_handler import AnimationHandler
from ..systems.rendering.render_system import AnimationSystem, RenderSystem
from ..systems.rendering.camera import Camera
from ..systems.combat.combat_system import CombatSystem
from ..systems.combat.ai_system import AISystem
from ..systems.rendering.particle_effect_system import ParticleEmitter

from ..systems.scene.level_manager import Level

from ..weapons.bullet_patterns import *

from ..utils import LEVEL, Inputs, GameSceneEvents#, swap_color

import random

class GameScene(Scene):
    """
    Represents the main game scene, managing entities, components, and physics.
    """
    def __init__(self, ctx):
        """
        Initializes the game scene with an entity manager, component manager, and physics engine.
        """
        super().__init__(id="game", ctx=ctx)
        self.component_manager = ComponentManager()
        self.camera = Camera()
        
        self.timer_system = TimerSystem(self.component_manager)

        self.entity_manager = EntityManager(component_manager=self.component_manager, event_manager=self.ctx.event_manager)
        self.entity_factory = EntityFactory()

        self.physics_engine = PhysicsEngine(self.component_manager, self.ctx.event_manager)
        self.animation_system = AnimationSystem(self.component_manager)
        self.render_system = RenderSystem(self.ctx.event_manager, self.component_manager, self.entity_manager, self.ctx.resource_manager)
        self.combat_system = CombatSystem(self.component_manager, self.entity_manager, self.camera, self.ctx.event_manager, self.ctx.resource_manager)
        
        # Link combat system to render system so projectiles can be drawn
        self.render_system.combat_system = self.combat_system

        self.level = Level(self.ctx)
        self.current_level = f'data/levels/{LEVEL}.json'

        # Font for debug overlay (FPS)
        try:
            self.font = pygame.font.SysFont(None, 20)
        except Exception:
            # Fallback in case font subsystem isn't ready yet
            self.font = None

        # Health Bar Assets & State
        self.health_bar_img = self.ctx.resource_manager.get_image("data/graphics/images/health_bar.png")
        if self.health_bar_img:
            self.health_bar_img.set_colorkey((0, 0, 0))

        self.health_drain = 100.0 # Will be initialized in start()
        self.health_red = (228, 59, 68)
        self.health_orange = (247, 118, 34)
        
        self.hb_scale_juice = 1.0
        self.hb_rot_juice = 0.0

    def start(self):
        print(f"[SCENE] Starting scene: '{self.id}' (DEBUG)")

        self.player = self.level.load(self.current_level, self.component_manager, self.entity_factory, self.entity_manager, self.render_system.render_effect_system)

        self.player_input_system = PlayerInputSystem(entity_id=self.player, event_manager=self.ctx.event_manager)
        self.ai_system = AISystem(player_entity_id=self.player, component_manager=self.component_manager, event_manager=self.ctx.event_manager)

        self.camera.set_target(self.player)

        # Initialize health UI state
        p_health = self.component_manager.get(self.player, HealthComponent)
        if p_health:
            self.health_drain = p_health.health

        # Subscribe to player input events
        self.ctx.event_manager.subscribe(Inputs.UP, lambda: self.player_input_system.on_move("up"), source=self.player)
        self.ctx.event_manager.subscribe(Inputs.DOWN, lambda: self.player_input_system.on_move("down"), source=self.player)
        self.ctx.event_manager.subscribe(Inputs.LEFT, lambda: self.player_input_system.on_move("left"), source=self.player)
        self.ctx.event_manager.subscribe(Inputs.RIGHT, lambda: self.player_input_system.on_move("right"), source=self.player)

        self.ctx.event_manager.subscribe(Inputs.UP_RELEASE, lambda: self.player_input_system.on_move("up", held=False), source=self.player)
        self.ctx.event_manager.subscribe(Inputs.DOWN_RELEASE, lambda: self.player_input_system.on_move("down", held=False), source=self.player)
        self.ctx.event_manager.subscribe(Inputs.LEFT_RELEASE, lambda: self.player_input_system.on_move("left", held=False), source=self.player)
        self.ctx.event_manager.subscribe(Inputs.RIGHT_RELEASE, lambda: self.player_input_system.on_move("right", held=False), source=self.player)
        
        self.ctx.event_manager.subscribe(Inputs.LEFT_HOLD, lambda: self.player_input_system.shoot(self.ctx.event_manager), source=self.player)

        self.ctx.event_manager.subscribe(Inputs.SPACE, lambda: self.player_input_system.spawn_bomb(self.component_manager, self.entity_manager, self.ctx.animation_handler, self.ctx.event_manager), source=self.player)
        self.ctx.event_manager.subscribe(Inputs.SPACE_RELEASE, lambda: self.player_input_system.on_bomb_release(), source=self.player)
        self.ctx.event_manager.subscribe(Inputs.DASH, lambda: self.player_input_system.dash(self.component_manager), source=self.player)
        self.ctx.event_manager.subscribe(Inputs.DASH_RELEASE, lambda: self.player_input_system.on_dash_release(), source=self.player)
        
        # Screen shake event
        self.ctx.event_manager.subscribe(GameSceneEvents.SCREEN_SHAKE, lambda **kwargs: self.camera.trigger_shake(kwargs.get('intensity', 5.0), kwargs.get('duration', 0.5)))
        
        # Particles events
        self.ctx.event_manager.subscribe(GameSceneEvents.PROJECTILE_COLLISION, self._on_projectile_collision)
        self.ctx.event_manager.subscribe(GameSceneEvents.WALK, self._on_walk)
        self.ctx.event_manager.subscribe(GameSceneEvents.WATER_SPLASH, self._on_water_splash)
        self.ctx.event_manager.subscribe(GameSceneEvents.SPAWN_GHOST, self._on_spawn_ghost)

        # Damage particles
        self.ctx.event_manager.subscribe(GameSceneEvents.DAMAGE, lambda entity_id, proj_id, **args: self._on_projectile_collision(
            pos=self.component_manager.get(entity_id, Position).vec.copy(),
            vel=args.get('proj_vel', pygame.Vector2(0,0)),
            target_type="enemy",
            size=10.0 # FastProjectiles don't have a reliable size parameter passed in DAMAGE yet, 10.0 is a good default
        ))
        
        # Water death check
        self.ctx.event_manager.subscribe('request_water_check', self._handle_water_check)

        # Health Bar Juice
        def trigger_hb_juice(entity_id, **kwargs):
            if entity_id == self.player:
                self.hb_scale_juice = 1.1
                self.hb_rot_juice = random.uniform(-3, 3)

        self.ctx.event_manager.subscribe(GameSceneEvents.DAMAGE, trigger_hb_juice)

        self.ctx.event_manager.subscribe('l', lambda eid=self.entity_manager.create_entity(): self.component_manager.add(
            eid,
            Position(
                eid,
                *self.component_manager.get(self.player, Position).vec
            ),
            ParticleEmitter(
                rate=10,
                duration=10,
                loop = False
            )
        ))

        # Set up keybinds for input system
        self.ctx.input_system.set_input_binds(
            keys_pressed = {
                pygame.K_SPACE: Inputs.SPACE,
                pygame.K_LSHIFT: Inputs.DASH
            },
            keys_held = {
                pygame.K_w: Inputs.UP,
                pygame.K_s: Inputs.DOWN,
                pygame.K_a: Inputs.LEFT,
                pygame.K_d: Inputs.RIGHT,
                pygame.K_l: 'l'
            },
            keys_released = {
                pygame.K_w: Inputs.UP_RELEASE,
                pygame.K_s: Inputs.DOWN_RELEASE,
                pygame.K_a: Inputs.LEFT_RELEASE,
                pygame.K_d: Inputs.RIGHT_RELEASE,
                pygame.K_SPACE: Inputs.SPACE_RELEASE,
                pygame.K_LSHIFT: Inputs.DASH_RELEASE
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
  
    def update(self, fps, dt):
        # Update the physics engine
        self.timer_system.update(dt)

        # Update player water status for dash extension
        if hasattr(self, 'player_input_system'):
            p_pos = self.component_manager.get(self.player, Position)
            p_col = self.component_manager.get(self.player, CollisionComponent)
            if p_pos and p_col:
                left = p_pos.x + p_col.offset.x
                top = p_pos.y + p_col.offset.y
                right = left + p_col.size.x
                bottom = top + p_col.size.y
                center_x = left + p_col.size.x / 2.0
                center_y = top + p_col.size.y / 2.0
                
                # Check corners (inset slightly) and center of the actual collision box
                points = [
                    (center_x, center_y),
                    (left + 2, top + 2),
                    (right - 2, top + 2),
                    (left + 2, bottom - 2),
                    (right - 2, bottom - 2)
                ]
                
                water_count = 0
                for px, py in points:
                    if self._is_pos_in_water(pygame.Vector2(px, py)):
                        water_count += 1
                
                self.player_input_system.is_touching_water = (water_count > 0)
                self.player_input_system.on_water_completely = (water_count == len(points))
                # For completeness (though no longer the primary dash decider)
                self.player_input_system.on_land_completely = (water_count == 0)

        # Build a single shared Dynamic Quadtree for all non-tile entities per frame
        from ..utils import Quadtree, VIRTUAL_WINDOW_SIZE
        dynamic_quadtree = Quadtree(0, (*self.camera.scroll, *VIRTUAL_WINDOW_SIZE))
        
        # Only insert entities that aren't tiles (tiles are in level.static_quadtree)
        # Foliage and destructibles need to be in this tree to be hittable/collidable
        for entity in self.component_manager.get_entities_with(CollisionComponent, Position):
            comp = self.component_manager.get(entity, CollisionComponent)
            pos = self.component_manager.get(entity, Position)
            
            # Entities with CollisionComponents are dynamic by nature in our ECS 
            # (unless they were tile-entities which we removed from the loop)
            rect = pygame.Rect(*(pos.vec + comp.offset), *comp.size)
            dynamic_quadtree.insert(entity, rect)

        self.player_input_system.update(self.component_manager, dt) 
        self.ai_system.update(dt)
        self.physics_engine.update(
            self.camera.scroll, fps, dt, 
            is_dashing=self.player_input_system.is_dashing, 
            player_id=self.player, 
            static_quadtree=self.level.static_quadtree,
            dynamic_quadtree=dynamic_quadtree
        )
        self.combat_system.update(
            event_manager=self.ctx.event_manager,
            component_manager=self.component_manager,
            scroll=self.camera.scroll,
            dt=dt,
            fps=fps,
            static_quadtree=self.level.static_quadtree,
            dynamic_quadtree=dynamic_quadtree,
            particle_system=self.render_system.particle_effect_system,
            is_dashing=self.player_input_system.is_dashing,
            player_id=self.player,
            camera_center=self.camera.center
        )
        self.animation_system.update(fps, dt, camera_rect=self.camera.rect)
        self.render_system.update(dt, tilemap=self.level.tilemap, camera=self.camera)
        self.entity_manager.refresh_entities(dt=dt)

        # Update tilemap animations (water frames)
        if self.level and self.level.tilemap:
            try:
                self.level.tilemap.update(dt)
            except Exception:
                pass

        raw_mouse = pygame.mouse.get_pos()
        scaled_mouse = (raw_mouse[0] // 2, raw_mouse[1] // 2)
        self.camera.update(dt, self.component_manager, lerp=True, mouse=scaled_mouse, mouse_ratio=0.1)

        # Update health bar drain effect
        p_health = self.component_manager.get(self.player, HealthComponent)
        if p_health:
            if self.health_drain > p_health.health:
                self.health_drain = max(p_health.health, self.health_drain - 40.0 * dt)
            else:
                self.health_drain = p_health.health

        # Recover HB Juice
        self.hb_scale_juice = 1.0 + (self.hb_scale_juice - 1.0) * (0.9 ** (dt * 60))
        self.hb_rot_juice *= (0.9 ** (dt * 60))

    def _on_projectile_collision(self, **kwargs):
        pos = kwargs.get('pos')
        vel = kwargs.get('vel')
        target_type = kwargs.get('target_type')
        size = kwargs.get('size', 10.0)
        
        if not pos or not vel: return
        
        # Calculate impact details
        impact_dir = -vel.normalize() if vel.length_squared() > 0 else pygame.Vector2(0, 0)
        impact_speed = vel.length() * 0.4 # Strong impact
        
        color = (255, 255, 255) # Enemy hit
        particle_count = 8
        
        if target_type == "environment":
            # Shades of brown from path/foliage
            color = random.choice([(116, 73, 56), (155, 103, 80), (184, 111, 80)])
            particle_count = 12 # Much lower for performance, especially with shotguns
            
        if hasattr(self, 'render_system') and self.render_system.particle_effect_system:
            for _ in range(particle_count):
                particle_size = random.uniform(4.0, 8.0) if target_type == "enemy" else random.uniform(1.5, 4.5) * (size/15.0)
                
                # Directional spread
                spread_rad = math.radians(60.0)
                base_angle = math.atan2(impact_dir.y, impact_dir.x) if impact_dir.length_squared() > 0 else random.uniform(0, math.pi * 2)
                angle = base_angle + random.uniform(-spread_rad/2, spread_rad/2)
                speed = random.uniform(impact_speed * 0.8, impact_speed * 1.4)
                
                self.render_system.particle_effect_system.emit_fast_particle(
                    x=pos.x + random.uniform(-5, 5), y=pos.y + random.uniform(-5, 5),
                    vx=math.cos(angle) * speed, vy=math.sin(angle) * speed,
                    lifetime=0.6,
                    r=color[0], g=color[1], b=color[2], a=255,
                    size=particle_size,
                    fade=False, shrink=True, friction=0.8
                )
        
    def _on_walk(self, **kwargs):
        pos = kwargs.get('pos')
        vel = kwargs.get('vel')
        eid = kwargs.get('entity_id')
        if not pos or not vel: return

        # Spawn dust behind feet directly without ECS
        if hasattr(self, 'render_system') and self.render_system.particle_effect_system:
            for _ in range(2): # Just a couple of dust particles
                self.render_system.particle_effect_system.emit_fast_particle(
                    x=pos.x, y=pos.y + 5,
                    vx=random.uniform(-5, 5), vy=random.uniform(-5, 5),
                    lifetime=0.5,
                    r=184, g=111, b=80, a=255,
                    size=random.uniform(1.0, 2.5),
                    fade=False, shrink=True, friction=0.85
                )

    def _on_water_splash(self, **kwargs):
        pos = kwargs.get('pos')
        vel = kwargs.get('vel')
        size = kwargs.get('size', 10.0)
        
        if not pos or not vel: return
        
        impact_dir = -vel.normalize() if vel.length_squared() > 0 else pygame.Vector2(0, 0)
        impact_speed = vel.length() * 0.15
        
        particle_count = int(10 * (size/15.0)) # Not too many
        
        if hasattr(self, 'render_system') and self.render_system.particle_effect_system:
            for _ in range(particle_count):
                particle_size = random.uniform(2.0, 4.0) * (size/15.0)
                spread_rad = math.radians(90.0)
                base_angle = math.atan2(impact_dir.y, impact_dir.x) if impact_dir.length_squared() > 0 else random.uniform(0, math.pi * 2)
                angle = base_angle + random.uniform(-spread_rad/2, spread_rad/2)
                speed = random.uniform(impact_speed * 0.8, impact_speed * 1.4)
                
                self.render_system.particle_effect_system.emit_fast_particle(
                    x=pos.x + random.uniform(-2, 2), y=pos.y + random.uniform(-2, 2),
                    vx=math.cos(angle) * speed, vy=math.sin(angle) * speed,
                    lifetime=0.3,
                    r=255, g=255, b=255, a=255,
                    size=particle_size,
                    fade=False, shrink=True, friction=0.9
                )

    def _is_pos_in_water(self, pos):
        if not self.level.tilemap: return False
        from ..utils import TILE_SIZE
        water_layer = self.level.tilemap.layers.get("water")
        if not water_layer: return False
        
        chunk_pos = (int(pos.x // (self.level.tilemap.CHUNK_SIZE * TILE_SIZE)) * (self.level.tilemap.CHUNK_SIZE * TILE_SIZE),
                     int(pos.y // (self.level.tilemap.CHUNK_SIZE * TILE_SIZE)) * (self.level.tilemap.CHUNK_SIZE * TILE_SIZE))
        if chunk_pos in water_layer:
            for tpos, tdata in water_layer[chunk_pos].items():
                if tdata["rect"].collidepoint(pos.x, pos.y):
                    return True
        return False

    def _handle_water_check(self, **kwargs):
        eid = kwargs.get('entity_id')
        pos = kwargs.get('pos')
        respawn_pos = kwargs.get('respawn_pos')
        if not pos: return

        # Check multiple points around the player to see if any part is in water
        p_col = self.component_manager.get(eid, CollisionComponent)
        is_touching_water = False
        
        if p_col:
            left = pos.x + p_col.offset.x
            top = pos.y + p_col.offset.y
            right = left + p_col.size.x
            bottom = top + p_col.size.y
            center_x = left + p_col.size.x / 2.0
            center_y = top + p_col.size.y / 2.0
            points = [
                (center_x, center_y),
                (left + 2, top + 2),
                (right - 2, top + 2),
                (left + 2, bottom - 2),
                (right - 2, bottom - 2)
            ]
            for px, py in points:
                if self._is_pos_in_water(pygame.Vector2(px, py)):
                    is_touching_water = True
                    break
        else:
            if self._is_pos_in_water(pos):
                is_touching_water = True

        if is_touching_water:
            # If a specific respawn position was provided (e.g. start of dash), use it as a raycast target
            if respawn_pos and p_col:
                p_pos = self.component_manager.get(eid, Position)
                if p_pos:
                    # Raycast backwards from current pos to respawn_pos
                    start_vec = pygame.Vector2(respawn_pos)
                    curr_vec = pygame.Vector2(pos.x, pos.y)
                    direction = start_vec - curr_vec
                    
                    if direction.length_squared() > 0:
                        direction_norm = direction.normalize()
                        dist = direction.length()
                        step = 2.0 # Move back in 2-pixel increments
                        
                        safe_found = False
                        test_vec = curr_vec.copy()
                        for _ in range(int(dist / step) + 1):
                            left = test_vec.x + p_col.offset.x
                            top = test_vec.y + p_col.offset.y
                            right = left + p_col.size.x
                            bottom = top + p_col.size.y
                            cx = left + p_col.size.x / 2.0
                            cy = top + p_col.size.y / 2.0
                            
                            pts = [
                                (cx, cy),
                                (left + 2, top + 2),
                                (right - 2, top + 2),
                                (left + 2, bottom - 2),
                                (right - 2, bottom - 2)
                            ]
                            
                            in_water = any(self._is_pos_in_water(pygame.Vector2(px, py)) for px, py in pts)
                            if not in_water:
                                safe_found = True
                                break
                                
                            test_vec += direction_norm * step
                            
                        if safe_found:
                            # Add a small buffer to ensure the physics system doesn't register a collision on the boundary
                            p_pos.vec.update(test_vec + direction_norm * 2.0)
                        else:
                            p_pos.vec.update(respawn_pos) # Fallback to start
                    else:
                        p_pos.vec.update(respawn_pos)
                        
                    self.render_system.render_effect_system.trigger_flash(eid)
                    p_vel = self.component_manager.get(eid, Velocity)
                    if p_vel: p_vel.vec.update(0, 0)
                return

            # Find nearest walkable tile (grass or path)
            safe_pos = None
            found = False
            # Spiral search outwards
            for radius in range(1, 10):
                for dx in range(-radius, radius + 1):
                    for dy in [-radius, radius]:
                        if self._is_tile_walkable(pos.x + dx * 32, pos.y + dy * 32): # TILE_SIZE=32
                            safe_pos = pygame.Vector2(pos.x + dx * 32, pos.y + dy * 32)
                            found = True; break
                    if found: break
                    for dy in range(-radius + 1, radius):
                        for dx in [-radius, radius]:
                            if self._is_tile_walkable(pos.x + dx * 32, pos.y + dy * 32):
                                safe_pos = pygame.Vector2(pos.x + dx * 32, pos.y + dy * 32)
                                found = True; break
                        if found: break
                    if found: break
                if found: break
            
            if safe_pos:
                # Teleport player
                p_pos = self.component_manager.get(eid, Position)
                if p_pos:
                    dist = pos.distance_to(safe_pos)
                    # SOFT LANDING: if we are within 16px of shore, just snap without penalty
                    if dist < 16:
                        p_pos.vec.update(safe_pos)
                    else:
                        # Full drowning penalty
                        p_pos.vec.update(safe_pos)
                        self.render_system.render_effect_system.trigger_flash(eid)
                        p_vel = self.component_manager.get(eid, Velocity)
                        if p_vel: p_vel.vec.update(0, 0)

    def _is_tile_walkable(self, x, y):
        # A tile is not walkable if it is water
        if self._is_pos_in_water(pygame.Vector2(x, y)):
            return False

        tilemap = self.level.tilemap
        from ..utils import TILE_SIZE
        chunk_x = int(x // (tilemap.CHUNK_SIZE * TILE_SIZE)) * (tilemap.CHUNK_SIZE * TILE_SIZE)
        chunk_y = int(y // (tilemap.CHUNK_SIZE * TILE_SIZE)) * (tilemap.CHUNK_SIZE * TILE_SIZE)
        chunk_pos = (chunk_x, chunk_y)

        # Walkable if it exists in grass or path layer
        for layer_id in ["grass", "path"]:
            layer = tilemap.layers.get(layer_id)
            if layer and chunk_pos in layer:
                for tpos, tdata in layer[chunk_pos].items():
                    if tdata["rect"].collidepoint(x, y):
                        return True
        return False
    def _on_spawn_ghost(self, **kwargs):
        image = kwargs.get('image')
        pos = kwargs.get('pos')
        offset = kwargs.get('offset')
        if not image or not pos: return
        
        ghost_id = self.entity_manager.create_entity()
        self.component_manager.add(ghost_id, Position(ghost_id, pos.x, pos.y))
        self.component_manager.add(ghost_id, RenderComponent(ghost_id, surface=image.copy(), offset=offset, center=True))
        
        # Fade effect
        rec = RenderEffectComponent()
        rec.alpha = 150 # Start semi-transparent
        self.component_manager.add(ghost_id, rec)
        self.render_system.render_effect_system.add_effect(ghost_id, "fade", {"duration": 0.4, "start_alpha": 150, "target_alpha": 0})
        
        # Y-Sort
        self.component_manager.add(ghost_id, YSortRender(ghost_id, offset=(0, 0)))
        
        # Auto-delete
        self.component_manager.add(ghost_id, TimerComponent(0.4, lambda: self.entity_manager.delete_entity(ghost_id)))

    def render(self, surface):
        self.render_system.render(surface, self.level.tilemap, self.camera)

    def render_ui(self, screen):
        # Draw FPS counter and bomb cooldown timer on the screen if font is available
        if self.font:
            if not hasattr(self, '_ui_text_cache'):
                self._ui_text_cache = {}

            def get_cached_text(text, color):
                key = (text, color)
                if key not in self._ui_text_cache:
                    self._ui_text_cache[key] = self.font.render(text, True, color)
                return self._ui_text_cache[key]

            # Limit cache size
            if len(self._ui_text_cache) > 200:
                self._ui_text_cache.clear()

            ui_blits = []
            
            fps_val = int(getattr(self.ctx, 'fps', 0))
            fps_text = f"FPS: {fps_val}"
            text_surf = get_cached_text(fps_text, (255, 255, 255))
            shadow = get_cached_text(fps_text, (0, 0, 0))
            ui_blits.append((shadow, (11, 11)))
            ui_blits.append((text_surf, (10, 10)))

            # Bomb cooldown display
            bomb_timer = None
            if hasattr(self, 'player_input_system'):
                bomb_timer = getattr(self.player_input_system, 'bomb_timer', 0.0)

            if bomb_timer and bomb_timer > 0:
                bomb_text = f"Bomb CD: {bomb_timer:.1f}s"
                color = (255, 200, 0)
            else:
                bomb_text = "Bomb: Ready"
                color = (255, 200, 0)

            bomb_surf = get_cached_text(bomb_text, color)
            bomb_shadow = get_cached_text(bomb_text, (0, 0, 0))
            ui_blits.append((bomb_shadow, (11, 31)))
            ui_blits.append((bomb_surf, (10, 30)))

            # Dash info
            dash_charges = getattr(self.player_input_system, 'dash_charges', 0)
            dash_refill = getattr(self.player_input_system, 'dash_refill_timer', 0.0)
            is_dashing = getattr(self.player_input_system, 'is_dashing', False)
            
            dash_text = f"Dashes: {dash_charges} | Refill: {dash_refill:.1f}s"
            if is_dashing:
                dash_text += " [DASHING]"
            
            dash_surf = get_cached_text(dash_text, (0, 255, 255))
            dash_shadow = get_cached_text(dash_text, (0, 0, 0))
            ui_blits.append((dash_shadow, (11, 51)))
            ui_blits.append((dash_surf, (10, 50)))

            # Wind info
            wind_mag = getattr(self.render_system.wind_system, 'magnitude_x', 0.0)
            wind_text = f"Wind X: {wind_mag:+.2f}"
            wind_surf = get_cached_text(wind_text, (200, 255, 200))
            wind_shadow = get_cached_text(wind_text, (0, 0, 0))
            ui_blits.append((wind_shadow, (11, 71)))
            ui_blits.append((wind_surf, (10, 70)))
            
            if ui_blits:
                screen.blits(ui_blits)

        # Draw Health Bar
        p_health = self.component_manager.get(self.player, HealthComponent)
        if p_health and self.health_bar_img:
            # Base Scale
            hb_base_scale = 0.5
            
            # Dimensions based on scaled image
            bw, bh = int(self.health_bar_img.get_width() * hb_base_scale), int(self.health_bar_img.get_height() * hb_base_scale)
            
            # Create a temporary surface
            temp_hb_surf = pygame.Surface((bw, bh))
            # Fill with the outer-transparency color
            MASK_COLOR = (0, 0, 1)
            temp_hb_surf.fill(MASK_COLOR)
            
            # Fill logic
            inner_padding_x = 4 * hb_base_scale
            inner_padding_y = 4 * hb_base_scale
            inner_w = bw - (inner_padding_x * 2)
            inner_h = bh - (inner_padding_y * 2)
            
            health_ratio = p_health.health / p_health.max_health
            drain_ratio = self.health_drain / p_health.max_health
            
            # 1. Draw Bars underneath
            # Draw Drain (Orange)
            if drain_ratio > health_ratio:
                drain_rect = pygame.Rect(inner_padding_x, inner_padding_y, int(inner_w * drain_ratio), inner_h)
                pygame.draw.rect(temp_hb_surf, self.health_orange, drain_rect)
            
            # Draw Current Health (Red)
            health_rect = pygame.Rect(inner_padding_x, inner_padding_y, int(inner_w * health_ratio), inner_h)
            pygame.draw.rect(temp_hb_surf, self.health_red, health_rect)
            
            # 2. Draw Frame on top (using its (0,0,0) colorkey to let bars show through)
            scaled_frame = pygame.transform.scale(self.health_bar_img, (bw, bh))
            scaled_frame.set_colorkey((0, 0, 0))
            temp_hb_surf.blit(scaled_frame, (0, 0))
            
            # Apply Juice (Final Scale and Rotation)
            final_hb_scale = 1.5 * self.hb_scale_juice
            if final_hb_scale != 1.0:
                new_w = int(bw * (final_hb_scale/hb_base_scale))
                new_h = int(bh * (final_hb_scale/hb_base_scale))
                temp_hb_surf = pygame.transform.scale(temp_hb_surf, (new_w, new_h))
            
            if self.hb_rot_juice != 0:
                temp_hb_surf = pygame.transform.rotate(temp_hb_surf, self.hb_rot_juice)
            
            # Set the final transparency (makes the (0,0,1) background invisible)
            temp_hb_surf.set_colorkey(MASK_COLOR)
            
            # Center at bottom
            pos_x = (screen.get_width() - temp_hb_surf.get_width()) // 2
            pos_y = screen.get_height() - temp_hb_surf.get_height() - 10
            
            screen.blit(temp_hb_surf, (pos_x, pos_y))
