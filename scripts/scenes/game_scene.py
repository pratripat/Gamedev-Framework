import pygame, math

from scripts.components.combat import HealthComponent
from ..systems.scene.scene_manager import Scene
from ..components.physics import Position, Velocity, CollisionComponent
from ..ecs.component_manager import ComponentManager

from ..systems.core.timer_system import TimerSystem
from ..ecs.entity_manager import EntityManager
from ..ecs.entity_factory import EntityFactory
from ..systems.input.player_input_system import PlayerInputSystem
from ..systems.core.physics_engine import PhysicsEngine
from ..systems.rendering.render_system import AnimationSystem, RenderSystem
from ..systems.rendering.camera import Camera
from ..systems.combat.combat_system import CombatSystem
from ..systems.combat.destructible_system import DestructibleSystem
from ..systems.combat.ai_system import AISystem
from ..systems.rendering.particle_effect_system import ParticleEmitter

from ..systems.scene.level_manager import Level

from ..weapons.bullet_patterns import *

from ..utils import LEVEL, Inputs, GameSceneEvents, screen_to_virtual
from ..utils.tween import TweenSystem
from ..utils.events import ScreenShakeEvent
from ..systems.gamefeel import GameFeelManager
from ..systems.vfx import VFXManager

import random

from ..utils import Quadtree, VIRTUAL_WINDOW_SIZE
from ..utils.events import AnimationEvent
from ..systems.animation.animation_event_handler import AnimationEventHandler

from .game_hud import GameHUD
from .particle_event_coordinator import ParticleEventCoordinator
from .respawn_manager import RespawnManager
from ..systems.debug import Profiler, DebugOverlay


class GameScene(Scene):
    """Orchestrates all game systems. Delegates UI, particles, and respawn
    to focused sub-managers so the scene stays manageable as the project grows."""

    def __init__(self, ctx):
        super().__init__(id="game", ctx=ctx)
        self.component_manager = ComponentManager()
        self.camera = Camera()
        self._dynamic_quadtree = None

        self.tween_system = TweenSystem()
        self.timer_system = TimerSystem(self.component_manager)

        self.entity_manager = EntityManager(
            component_manager=self.component_manager,
            event_manager=self.ctx.event_manager
        )
        self.entity_factory = EntityFactory()

        self.physics_engine = PhysicsEngine(self.component_manager, self.ctx.event_manager)
        self.animation_system = AnimationSystem(self.component_manager)
        self.render_system = RenderSystem(
            self.ctx.event_manager, self.component_manager,
            self.entity_manager, self.ctx.resource_manager
        )
        self.combat_system = CombatSystem(
            self.component_manager, self.entity_manager,
            self.camera, self.ctx.event_manager, self.ctx.resource_manager
        )

        self.render_system.combat_system = self.combat_system
        self.destructible_system = DestructibleSystem(self.component_manager, self.entity_manager)
        self.destructible_system.projectile_system = self.combat_system.projectile_system
        self.destructible_system.particle_system = self.render_system.particle_effect_system
        self.render_system.destructible_system = self.destructible_system
        self.render_system.render_effect_system.tween_system = self.tween_system

        self.level = Level(self.ctx)
        self.current_level = f'data/levels/{LEVEL}.json'

        # Sub-managers (created in start())
        self.hud = None
        self.particle_coordinator = None
        self.respawn_manager = None

        self.gamefeel = None
        self.vfx_manager = None

        self.profiler = Profiler()
        self.debug_overlay = None

        self._game_time = 0.0
        self._ripple_timer = 0.0

        # Active tree shakes: {entity_id: {'orig_x': float, 'orig_y': float,
        #   'strength': float, 'timer': float, 'duration': float}}
        self._tree_shakes: dict[int, dict] = {}

    # ------------------------------------------------------------------
    # Scene lifecycle
    # ------------------------------------------------------------------

    def start(self):
        print(f"[SCENE] Starting scene: '{self.id}' (DEBUG)")

        self.player = self.level.load(
            self.current_level, self.component_manager,
            self.entity_factory, self.entity_manager, self.render_system
        )
        self.player_input_system = PlayerInputSystem(
            entity_id=self.player, event_manager=self.ctx.event_manager
        )
        self.ai_system = AISystem(
            player_entity_id=self.player,
            component_manager=self.component_manager,
            event_manager=self.ctx.event_manager
        )
        self.camera.set_target(self.player)

        # --- Sub-managers ---
        font = self._create_font()
        health_bar_img = self.ctx.resource_manager.get_image("data/graphics/images/health_bar.png")
        self.hud = GameHUD(self.component_manager, font, health_bar_img, self.ctx.event_manager)
        self.hud.set_player(self.player, self.player_input_system, self.render_system)

        self.particle_coordinator = ParticleEventCoordinator(
            self.render_system, self.component_manager, self.entity_manager
        )
        self.particle_coordinator.subscribe_all(self.ctx.event_manager)

        # Game-feel / juice systems
        self.gamefeel = GameFeelManager(
            camera=self.camera,
            tween_system=self.tween_system,
            component_manager=self.component_manager,
            event_manager=self.ctx.event_manager,
        )
        self.vfx_manager = VFXManager(
            gamefeel=self.gamefeel,
            particle_coordinator=self.particle_coordinator,
        )

        # Debug overlay
        self.debug_overlay = DebugOverlay(font)

        self.respawn_manager = RespawnManager(
            self.level, self.component_manager, self.render_system
        )
        self.respawn_manager.set_player(self.player, self.player_input_system)

        # Animation event handler — maps frame events (footstep, shoot, …) to game actions
        self.animation_event_handler = AnimationEventHandler(
            self.component_manager, self.ctx.event_manager,
            self.render_system, self.ctx.resource_manager
        )
        self.ctx.event_manager.subscribe(
            GameSceneEvents.ANIMATION_EVENT,
            self.animation_event_handler.handle_kwargs
        )
        self.ctx.event_manager.subscribe_typed(
            AnimationEvent, self.animation_event_handler.handle
        )

        # --- Event subscriptions ---
        self._subscribe_events()

        # Input binds
        self.ctx.input_system.set_input_binds(
            keys_pressed={
                pygame.K_SPACE: Inputs.SPACE,
                pygame.K_LSHIFT: Inputs.DASH
            },
            keys_held={
                pygame.K_w: Inputs.UP, pygame.K_s: Inputs.DOWN,
                pygame.K_a: Inputs.LEFT, pygame.K_d: Inputs.RIGHT,
                pygame.K_l: 'l'
            },
            keys_released={
                pygame.K_w: Inputs.UP_RELEASE, pygame.K_s: Inputs.DOWN_RELEASE,
                pygame.K_a: Inputs.LEFT_RELEASE, pygame.K_d: Inputs.RIGHT_RELEASE,
                pygame.K_SPACE: Inputs.SPACE_RELEASE,
                pygame.K_LSHIFT: Inputs.DASH_RELEASE
            },
            mouse_clicked={
                pygame.BUTTON_LEFT: Inputs.LEFT_CLICK,
                pygame.BUTTON_RIGHT: Inputs.RIGHT_CLICK
            },
            mouse_held={
                pygame.BUTTON_LEFT: Inputs.LEFT_HOLD,
                pygame.BUTTON_RIGHT: Inputs.RIGHT_HOLD
            }
        )

    @staticmethod
    def _create_font():
        try:
            return pygame.font.SysFont(None, 20)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Event wiring
    # ------------------------------------------------------------------

    def _subscribe_events(self):
        em = self.ctx.event_manager

        # Player input — use self.player_input_system so closures stay valid after respawn
        em.subscribe(Inputs.UP, lambda: self.player_input_system.on_move("up"), source=self.player)
        em.subscribe(Inputs.DOWN, lambda: self.player_input_system.on_move("down"), source=self.player)
        em.subscribe(Inputs.LEFT, lambda: self.player_input_system.on_move("left"), source=self.player)
        em.subscribe(Inputs.RIGHT, lambda: self.player_input_system.on_move("right"), source=self.player)
        em.subscribe(Inputs.UP_RELEASE, lambda: self.player_input_system.on_move("up", held=False), source=self.player)
        em.subscribe(Inputs.DOWN_RELEASE, lambda: self.player_input_system.on_move("down", held=False), source=self.player)
        em.subscribe(Inputs.LEFT_RELEASE, lambda: self.player_input_system.on_move("left", held=False), source=self.player)
        em.subscribe(Inputs.RIGHT_RELEASE, lambda: self.player_input_system.on_move("right", held=False), source=self.player)
        em.subscribe(Inputs.LEFT_HOLD, lambda: self.player_input_system.shoot(em), source=self.player)
        em.subscribe(Inputs.SPACE, lambda: self.player_input_system.spawn_bomb(
            self.component_manager, self.entity_manager,
            self.ctx.animation_handler, em
        ), source=self.player)
        em.subscribe(Inputs.SPACE_RELEASE, lambda: self.player_input_system.on_bomb_release(), source=self.player)
        em.subscribe(Inputs.DASH, lambda: self.player_input_system.dash(self.component_manager), source=self.player)
        em.subscribe(Inputs.DASH_RELEASE, lambda: self.player_input_system.on_dash_release(), source=self.player)

        # Screen shake (legacy — keep for backwards compat)
        em.subscribe_typed(ScreenShakeEvent, self._on_screen_shake)
        em.subscribe(GameSceneEvents.SCREEN_SHAKE, lambda **kw: self.camera.trigger_shake(
            kw.get('intensity', 5.0), kw.get('duration', 0.5)
        ))

        # Death detection
        def _on_player_death(entity_id, **kwargs):
            if entity_id == self.player:
                self.respawn_manager.is_dead = True
                self.hud.set_dead(True)

        em.subscribe(GameSceneEvents.DEATH, _on_player_death)

        # Water rescue
        em.subscribe('request_water_check', lambda **kw: self.respawn_manager.handle_water_check(**kw))

        # Debug: spawn particle emitter at player position
        em.subscribe('l', lambda eid=self.entity_manager.create_entity():
                     self.component_manager.add(
                         eid,
                         Position(eid, *self.component_manager.get(self.player, Position).vec),
                         ParticleEmitter(rate=10, duration=10, loop=False)
                     ))

        # --- VFX event wiring ---
        em.subscribe(GameSceneEvents.DASH_START, self._on_dash_vfx)
        em.subscribe('bomb_burst', self._on_bomb_vfx)
        em.subscribe(GameSceneEvents.DAMAGE, self._on_damage_vfx)
        em.subscribe(GameSceneEvents.DEATH, self._on_death_vfx)
        em.subscribe(GameSceneEvents.PROJECTILE_COLLISION, self._on_projectile_vfx)
        em.subscribe(GameSceneEvents.WATER_SPLASH, lambda **kw: self.ctx.audio_manager.play('water_splash', priority=90))

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_screen_shake(self, event):
        self.camera.trigger_shake(event.intensity, event.duration)

    # ------------------------------------------------------------------
    # VFX callbacks
    # ------------------------------------------------------------------

    def _on_dash_vfx(self, entity_id, duration, **kw):
        if self.vfx_manager:
            self.vfx_manager.play('dash', entity_id=entity_id)
        self.ctx.audio_manager.play('dash')

    def _on_bomb_vfx(self, entity_id, **kw):
        if not self.vfx_manager:
            return
        pos_comp = self.component_manager.get(entity_id, Position)
        self.vfx_manager.play('bomb', entity_id=entity_id,
                              pos=pos_comp.vec.copy() if pos_comp else None)
        self.ctx.audio_manager.play('explosion', priority=200)

        # Tree shake + leaf particles within bomb blast radius
        radius = kw.get('radius', 150)
        if not pos_comp:
            return
        bomb_pos = pos_comp.vec
        from ..components.render_effect import RenderEffectComponent, WindAffectedComponent
        p_sys = self.render_system.particle_effect_system
        shake_duration = 0.8
        for eid in self.component_manager.get_entities_with(Position, WindAffectedComponent):
            tree_pos = self.component_manager.get(eid, Position)
            if not tree_pos:
                continue
            dist = tree_pos.vec.distance_to(bomb_pos)
            if dist > radius:
                continue

            # Continuous random shake — per-frame jitter for shake_duration seconds
            render = self.component_manager.get(eid, RenderComponent)
            if render:
                strength = 30.0 * (1 - dist / radius)
                self._tree_shakes[eid] = {
                    'orig_x': render.offset.x,
                    'orig_y': render.offset.y,
                    'strength': strength,
                    'timer': shake_duration,
                    'duration': shake_duration,
                }

            # Leaf particles using actual tree greens (bright, medium, dark)
            _LEAF_COLORS = [(96, 192, 64), (48, 128, 64), (32, 80, 64)]
            if p_sys:
                for _ in range(random.randint(25, 40)):
                    size = random.uniform(2.5, 6)
                    cr, cg, cb = random.choice(_LEAF_COLORS)
                    p_sys.emit_fast_particle(
                        x=tree_pos.x + random.uniform(-30, 30),
                        y=tree_pos.y + random.uniform(10, 45),
                        vx=random.uniform(-80, 80), vy=random.uniform(-90, -15),
                        lifetime=1.2 + size * 0.15,
                        r=cr, g=cg, b=cb, a=255,
                        size=size,
                        fade=True, shrink=True, friction=0.95,
                        sway=True, gravity=50,
                    )

    def _on_damage_vfx(self, entity_id, **kw):
        if self.vfx_manager and not kw.get('death'):
            self.vfx_manager.play('player_damage', entity_id=entity_id, **kw)
        if not kw.get('death'):
            self.ctx.audio_manager.play('player_hit', group='player', priority=200)

    def _on_death_vfx(self, entity_id, **kw):
        # Player death is handled by the respawn system
        if self.vfx_manager and entity_id != self.player:
            self.vfx_manager.play('enemy_death', entity_id=entity_id, **kw)
        if entity_id != self.player:
            self.ctx.audio_manager.play('explosion', priority=200)

    def _on_projectile_vfx(self, **kw):
        if self.vfx_manager:
            self.vfx_manager.play('projectile_impact', **kw)
        self.ctx.audio_manager.play('enemy_hit', priority=150)

    # ------------------------------------------------------------------
    # Main update
    # ------------------------------------------------------------------

    def update(self, fps, dt):
        # Debug overlay toggle
        self._handle_debug_toggles()
        self.profiler.begin_frame()

        # Death gate — skip all updates while dead
        if self.respawn_manager.update_death_gate(dt, self._respawn):
            return

        # Save unscaled dt before applying time-scale effects
        raw_dt = dt

        # Apply hit-stop / slow-motion time scale on game logic
        if self.gamefeel:
            dt *= self.gamefeel.time_scale.scale

        # Visual tweens use real time so squash/stretch animates even
        # during hit-stop
        self.tween_system.update(raw_dt)
        self._update_tree_shakes(raw_dt)

        if dt > 0:
            self.profiler.begin('ai')
            self.ai_system.update(dt)
            self.profiler.end('ai')

            self.profiler.begin('physics')
            self.timer_system.update(dt)
            self._update_water_status()
            dynamic_quadtree = self._build_dynamic_quadtree()
            self.player_input_system.update(self.component_manager, dt)
            self.physics_engine.update(
                self.camera.scroll, fps, dt,
                is_dashing=self.player_input_system.is_dashing,
                player_id=self.player,
                static_quadtree=self.level.static_quadtree,
                dynamic_quadtree=dynamic_quadtree
            )
            self.profiler.end('physics')

            self.profiler.begin('combat')
            self.combat_system.update(
                event_manager=self.ctx.event_manager,
                component_manager=self.component_manager,
                scroll=self.camera.scroll, dt=dt, fps=fps,
                static_quadtree=self.level.static_quadtree,
                dynamic_quadtree=dynamic_quadtree,
                particle_system=self.render_system.particle_effect_system,
                is_dashing=self.player_input_system.is_dashing,
                player_id=self.player,
                camera_center=self.camera.center,
                game_time=self._game_time
            )
            self._game_time += dt
            self.destructible_system.update(dt, self.player)
            self.profiler.end('combat')

            self.profiler.begin('particles')
            self._update_water_ripples(raw_dt)
            self.profiler.end('particles')

            self.profiler.begin('animation')
            self.animation_system.update(fps, dt, camera_rect=self.camera.rect)
            self.profiler.end('animation')

            self.profiler.begin('rendering')
            scaled_mouse = screen_to_virtual(pygame.mouse.get_pos())
            self.render_system.update(dt, tilemap=self.level.tilemap, camera=self.camera, mouse_pos=scaled_mouse)
            self.entity_manager.refresh_entities(dt=dt)
            if self.level and self.level.tilemap:
                try:
                    self.level.tilemap.update(dt)
                except Exception:
                    pass
            self.camera.update(dt, self.component_manager, lerp=True, mouse=scaled_mouse, mouse_ratio=0.1)
            self.profiler.end('rendering')

        # Always run — HUD and time-scale stack use unscaled time
        self.profiler.begin('gamefeel')
        self.hud.update(raw_dt)
        if self.gamefeel:
            self.gamefeel.update(raw_dt)
        self.profiler.end('gamefeel')

    # ------------------------------------------------------------------
    # Sub-updates
    # ------------------------------------------------------------------

    def _handle_debug_toggles(self):
        if self.debug_overlay and self.ctx.input_system:
            if pygame.K_F3 in self.ctx.input_system.keys_pressed:
                self.debug_overlay.toggle()
            if pygame.K_F4 in self.ctx.input_system.keys_pressed:
                self.debug_overlay.toggle_profiler()

    def _update_water_status(self):
        if not hasattr(self, 'player_input_system'):
            return
        p_pos = self.component_manager.get(self.player, Position)
        p_col = self.component_manager.get(self.player, CollisionComponent)
        if not p_pos or not p_col:
            return

        left = p_pos.x + p_col.offset.x
        top = p_pos.y + p_col.offset.y
        right = left + p_col.size.x
        bottom = top + p_col.size.y
        points = [
            (left + p_col.size.x / 2.0, top + p_col.size.y / 2.0),
            (left + 2, top + 2), (right - 2, top + 2),
            (left + 2, bottom - 2), (right - 2, bottom - 2)
        ]
        water_count = self.respawn_manager.count_pos_in_water(points)
        self.player_input_system.is_touching_water = (water_count > 0)
        self.player_input_system.on_water_completely = (water_count == len(points))
        self.player_input_system.on_land_completely = (water_count == 0)

    def _build_dynamic_quadtree(self):
        qtree_bounds = (*self.camera.scroll, *VIRTUAL_WINDOW_SIZE)
        if self._dynamic_quadtree is None:
            self._dynamic_quadtree = Quadtree(0, qtree_bounds)
        else:
            self._dynamic_quadtree.clear()
            self._dynamic_quadtree.bounds = qtree_bounds
        for entity in self.component_manager.get_entities_with(CollisionComponent, Position):
            comp = self.component_manager.get(entity, CollisionComponent)
            pos = self.component_manager.get(entity, Position)
            rect = pygame.Rect(pos.x + comp.offset.x, pos.y + comp.offset.y,
                               comp.size.x, comp.size.y)
            self._dynamic_quadtree.insert(entity, rect)
        return self._dynamic_quadtree

    def _update_water_ripples(self, dt):
        if not self.level or not self.level.tilemap:
            return
        tilemap = self.level.tilemap
        self._ripple_timer += dt
        if self._ripple_timer < 0.1 or len(tilemap.ripples) >= 12:
            return
        self._ripple_timer = 0.0
        p_sys = self.combat_system.projectile_system
        if hasattr(p_sys, 'active_indices'):
            for idx in p_sys.active_indices:
                p = p_sys.pool[idx]
                if self.respawn_manager.is_pos_in_water((p.x, p.y)):
                    tilemap.add_ripple(p.x, p.y, vx=p.vx, vy=p.vy)
        if self.player_input_system.is_dashing:
            p_pos = self.component_manager.get(self.player, Position)
            if p_pos and self.respawn_manager.is_pos_in_water(p_pos.vec):
                tilemap.add_ripple(p_pos.x, p_pos.y)

    def _update_tree_shakes(self, dt):
        """Per-frame tree shake: random x/y offset with decaying intensity."""
        dead = []
        for eid, shake in self._tree_shakes.items():
            shake['timer'] -= dt
            if shake['timer'] <= 0:
                dead.append(eid)
                continue

            render = self.component_manager.get(eid, RenderComponent)
            if not render:
                dead.append(eid)
                continue

            progress = 1.0 - (shake['timer'] / shake['duration'])
            decay = 1.0 - progress  # linear decay
            jitter = shake['strength'] * decay
            render.offset.x = shake['orig_x'] + random.uniform(-jitter, jitter)
            render.offset.y = shake['orig_y'] + random.uniform(-jitter * 0.5, jitter * 0.3)

            if shake['timer'] <= 0.15:
                # Spring back smoothly near the end
                t = shake['timer'] / 0.15
                render.offset.x += (shake['orig_x'] - render.offset.x) * (1.0 - t * t)

        for eid in dead:
            shake = self._tree_shakes.pop(eid, None)
            if shake:
                render = self.component_manager.get(eid, RenderComponent)
                if render:
                    render.offset.x = shake['orig_x']
                    render.offset.y = shake['orig_y']

    # ------------------------------------------------------------------
    # Respawn
    # ------------------------------------------------------------------

    def _respawn(self):
        self.component_manager.clear_all()
        self.entity_manager.entities.clear()
        self.entity_manager.to_remove.clear()
        self.entity_manager.dead_entities.clear()
        self.entity_manager.player_id = None

        ps = self.render_system.particle_effect_system
        ps.active_indices.clear()
        ps.pool.reset()
        ps._particle_cache.clear()

        fpps = self.combat_system.projectile_system
        fpps.active_indices.clear()
        fpps.pool.reset()
        fpps._pulse_cache.clear()
        fpps._shared_hits.clear()
        fpps._shared_seen.clear()

        self.render_system._pulse_cache.clear()
        self.render_system._sprite_transform_cache.clear()
        self.render_system.grass_system.blades.clear()
        self.render_system.grass_system._render_cache.clear()
        self._tree_shakes.clear()

        self.camera = Camera()

        self.level = Level(self.ctx)
        self.player = self.level.load(
            self.current_level, self.component_manager,
            self.entity_factory, self.entity_manager, self.render_system
        )
        self.player_input_system = PlayerInputSystem(
            entity_id=self.player, event_manager=self.ctx.event_manager
        )
        self.ai_system = AISystem(
            player_entity_id=self.player,
            component_manager=self.component_manager,
            event_manager=self.ctx.event_manager
        )
        self.camera.set_target(self.player)

        # Re-wire sub-managers with new player reference
        self.hud.set_player(self.player, self.player_input_system, self.render_system)
        self.hud.reset()
        self.respawn_manager.set_player(self.player, self.player_input_system)
        self.respawn_manager.reset()

        # Update camera references in subsystems after respawn
        self.combat_system.weapon_system.camera = self.camera
        if self.gamefeel:
            self.gamefeel.set_camera(self.camera)
            self.gamefeel.clear_flashes()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, surface):
        self.render_system.render(surface, self.level.tilemap, self.camera)
        if hasattr(self, 'combat_system') and self.combat_system.attack_pattern_system:
            self.combat_system.attack_pattern_system.render_telegraphs(surface, self.camera)

    def render_ui(self, screen):
        if self.hud:
            self.hud.render_ui(screen, self.ctx)
        if self.gamefeel:
            self.gamefeel.render_flash(screen)

        # Debug overlay
        if self.debug_overlay:
            self.debug_overlay.render(screen, self.ctx, self)

        # DEBUG: entity bounding boxes — red=sprite, blue=collision, green dot=Position
        # Uses the same virtual→screen math as render_system (int truncation then scale).
        if hasattr(self, 'camera') and self.camera:
            from ..utils import VIRTUAL_WINDOW_SIZE
            vsize = VIRTUAL_WINDOW_SIZE
            dsize = screen.get_size()
            sf = (dsize[0] / vsize[0], dsize[1] / vsize[1])
            scroll = self.camera.scroll
            from ..components.animation import RenderComponent
            from ..components.render_effect import WindAffectedComponent
            for eid in self.component_manager.get_entities_with(Position, WindAffectedComponent):
                pos = self.component_manager.get(eid, Position)
                render = self.component_manager.get(eid, RenderComponent)
                collision = self.component_manager.get(eid, CollisionComponent)
                # Virtual-space coords (same truncation as render_system)
                sx_v = int(pos.x - scroll.x)
                sy_v = int(pos.y - scroll.y)
                # Green dot at Position (centre of entity)
                pygame.draw.circle(screen, (0, 255, 0),
                                   (int(sx_v * sf[0]), int(sy_v * sf[1])), 3 * int(sf[0]))
                if render and render.surface:
                    dr = render.offset
                    rx_v = sx_v + int(dr.x)
                    ry_v = sy_v + int(dr.y)
                    r = pygame.Rect(
                        int(rx_v * sf[0]), int(ry_v * sf[1]),
                        int(render.surface.get_width() * sf[0]),
                        int(render.surface.get_height() * sf[1])
                    )
                    pygame.draw.rect(screen, (255, 0, 0), r, 1)
                if collision:
                    c_off = collision.offset
                    c_sz = collision.size
                    cx_v = sx_v + int(c_off.x)
                    cy_v = sy_v + int(c_off.y)
                    col_rect = pygame.Rect(
                        int(cx_v * sf[0]), int(cy_v * sf[1]),
                        int(c_sz[0] * sf[0]), int(c_sz[1] * sf[1])
                    )
                    pygame.draw.rect(screen, (0, 100, 255), col_rect, 1)
