import math
import random
import pygame
from ..components.physics import Position
from ..components.render_effect import RenderEffectComponent, YSortRender
from ..components.animation import RenderComponent
from ..components.timer import TimerComponent
from ..utils import GameSceneEvents


class ParticleEventCoordinator:
    """Subscribes to game events and spawns particles / visual effects.

    Keeps particle response logic out of GameScene so it can be reused
    across scenes and tested independently.
    """

    def __init__(self, render_system, component_manager, entity_manager):
        self.render_system = render_system
        self.component_manager = component_manager
        self.entity_manager = entity_manager

    def subscribe_all(self, event_manager):
        event_manager.subscribe(GameSceneEvents.PROJECTILE_COLLISION, self._on_projectile_collision)
        event_manager.subscribe(GameSceneEvents.WALK, self._on_walk)
        event_manager.subscribe(GameSceneEvents.WATER_SPLASH, self._on_water_splash)
        event_manager.subscribe(GameSceneEvents.SPAWN_GHOST, self._on_spawn_ghost)
        event_manager.subscribe(GameSceneEvents.DAMAGE, self._on_damage_particles)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _emit_particles(particle_system, pos, vel, color, count, size_range,
                        spread_deg=60.0, lifetime=0.6, friction=0.8, shrink=True,
                        y_offset_range=(-5, 5)):
        if particle_system is None:
            return
        impact_speed = vel.length() * 0.4
        for _ in range(count):
            spread_rad = math.radians(spread_deg)
            if vel.length_squared() > 0:
                impact_dir = -vel.normalize()
                base_angle = math.atan2(impact_dir.y, impact_dir.x)
            else:
                base_angle = random.uniform(0, math.pi * 2)
            angle = base_angle + random.uniform(-spread_rad / 2, spread_rad / 2)
            speed = random.uniform(impact_speed * 0.8, impact_speed * 1.4)
            particle_system.emit_fast_particle(
                x=pos.x + random.uniform(-5, 5), y=pos.y + random.uniform(*y_offset_range),
                vx=math.cos(angle) * speed, vy=math.sin(angle) * speed,
                lifetime=lifetime,
                r=color[0], g=color[1], b=color[2], a=255,
                size=random.uniform(*size_range),
                fade=False, shrink=shrink, friction=friction
            )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_projectile_collision(self, **kwargs):
        pos = kwargs.get('pos')
        vel = kwargs.get('vel')
        target_type = kwargs.get('target_type')
        size = kwargs.get('size', 10.0)
        if not pos or not vel:
            return

        if target_type == "environment":
            color = random.choice([(116, 73, 56), (155, 103, 80), (184, 111, 80)])
            count = 12
            size_range = (1.5, 4.5)
        else:
            color = (255, 255, 255)
            count = 8
            size_range = (4.0, 8.0)

        # Scale size by projectile size
        size_range = (size_range[0] * (size / 15.0), size_range[1] * (size / 15.0))

        self._emit_particles(
            self.render_system.particle_effect_system,
            pos, vel, color, count, size_range,
            spread_deg=60.0, lifetime=0.6, friction=0.8, shrink=True
        )

    def _on_walk(self, **kwargs):
        pos = kwargs.get('pos')
        vel = kwargs.get('vel')
        if not pos or not vel:
            return

        if self.render_system.particle_effect_system:
            for _ in range(2):
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
        if not pos or not vel:
            return

        count = max(1, int(1.5 * (size / 15.0)))
        size_scale = size / 15.0
        self._emit_particles(
            self.render_system.particle_effect_system,
            pos, vel, (255, 255, 255), count,
            (4.0 * size_scale, 8.0 * size_scale),
            spread_deg=90.0, lifetime=0.3, friction=0.9, shrink=True,
            y_offset_range=(-2, 0)
        )

    def _on_spawn_ghost(self, **kwargs):
        image = kwargs.get('image')
        pos = kwargs.get('pos')
        offset = kwargs.get('offset')
        if not image or not pos:
            return

        ghost_id = self.entity_manager.create_entity()
        self.component_manager.add(ghost_id, Position(ghost_id, pos.x, pos.y))
        self.component_manager.add(ghost_id, RenderComponent(ghost_id, surface=image.copy(), offset=offset, center=True))
        rec = RenderEffectComponent()
        rec.alpha = 150
        self.component_manager.add(ghost_id, rec)
        self.render_system.render_effect_system.add_effect(ghost_id, "fade", {"duration": 0.4, "start_alpha": 150, "target_alpha": 0})
        self.component_manager.add(ghost_id, YSortRender(ghost_id, offset=(0, 0)))
        self.component_manager.add(ghost_id, TimerComponent(0.4, lambda: self.entity_manager.delete_entity(ghost_id)))

    def _on_damage_particles(self, entity_id, proj_id, **args):
        pos_comp = self.component_manager.get(entity_id, Position)
        if not pos_comp:
            return
        self._on_projectile_collision(
            pos=pos_comp.vec.copy(),
            vel=args.get('proj_vel', pygame.Vector2(0, 0)),
            target_type="enemy",
            size=10.0
        )
