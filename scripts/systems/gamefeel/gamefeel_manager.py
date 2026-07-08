"""Central coordinator for all gameplay-juice / game-feel effects.

Gameplay code requests effects by name::

    self.gamefeel.play('hit_stop', duration=0.08)
    self.gamefeel.play('squash', entity_id=eid, scale_x=1.2, scale_y=0.8)

The manager looks up the effect profile and delegates to the appropriate
sub-system (camera, tween system, render effects, time scale, etc.).
"""

from ...utils.tween import Tween
from .time_scale import TimeScale

import pygame


class GameFeelManager:
    """Owns TimeScale and provides named juice effects.

    Args:
        camera:       ``Camera`` instance (for shake).
        tween_system: ``TweenSystem`` instance (for tweens).
        component_manager: ``ComponentManager`` (for entity lookups).
        event_manager: ``EventManager`` (for emitting events).
    """

    def __init__(self, camera, tween_system, component_manager, event_manager):
        self.camera = camera
        self.tween_system = tween_system
        self.component_manager = component_manager
        self.event_manager = event_manager

        self.time_scale = TimeScale()

        # Screen flash state — list of [color, remaining, total]
        self._flashes: list = []

    # ------------------------------------------------------------------
    # Named effects
    # ------------------------------------------------------------------

    def play(self, name: str, **kwargs):
        """Execute a named game-feel effect.

        Supported effect names:

        * ``hit_stop``       — brief time freeze (duration, time_scale)
        * ``screen_shake``   — camera shake (intensity, duration)
        * ``screen_flash``   — full-screen colour flash (duration, color)
        * ``squash``         — entity squash/stretch (entity_id, scale_x, scale_y, duration)
        * ``slow_motion``    — brief slow-mo (duration, time_scale)
        * ``impact``         — shake + hit_stop + squash combo
        """
        handler = getattr(self, f'_effect_{name}', None)
        if handler:
            handler(**kwargs)

    # ------------------------------------------------------------------
    # Effect implementations
    # ------------------------------------------------------------------

    def _effect_hit_stop(self, duration=0.08, time_scale=0.0, **kw):
        self.time_scale.push(duration, time_scale)

    def _effect_slow_motion(self, duration=0.5, time_scale=0.3, **kw):
        self.time_scale.push(duration, time_scale)

    def _effect_screen_shake(self, intensity=5.0, duration=0.3, **kw):
        if self.camera:
            self.camera.trigger_shake(intensity, duration)

    def _effect_screen_flash(self, duration=0.1, color=(255, 255, 255), **kw):
        self._flashes.append([list(color[:3]), duration, duration])

    def _effect_squash(self, entity_id=None, scale_x=0.9, scale_y=1.1,
                       duration=0.06, **kw):
        if entity_id is None:
            return
        from ...components.render_effect import RenderEffectComponent
        rec = self.component_manager.get(entity_id, RenderEffectComponent)
        if rec is None:
            return
        self.tween_system.cancel_tweens_for(rec, 'scale')
        rec.scale = pygame.Vector2(1.0, 1.0)
        target = pygame.Vector2(scale_x, scale_y)
        t1 = Tween(rec, 'scale', pygame.Vector2(1.0, 1.0), target,
                   duration, easing='out_quad')
        t1.on_complete = lambda: self.tween_system.from_to(
            rec, 'scale', target, pygame.Vector2(1.0, 1.0),
            duration * 1.5, easing='out_quad'
        )
        self.tween_system.add(t1)

    def _effect_impact(self, entity_id=None, intensity=6.0, shake_duration=0.15,
                       hit_stop=0.06, squash_x=0.85, squash_y=1.15, **kw):
        """Combo: shake + hit_stop + squash on an entity."""
        self._effect_screen_shake(intensity=intensity, duration=shake_duration)
        self._effect_hit_stop(duration=hit_stop)
        if entity_id is not None:
            self._effect_squash(entity_id=entity_id, scale_x=squash_x,
                                scale_y=squash_y)

    # ------------------------------------------------------------------
    # Update & render
    # ------------------------------------------------------------------

    def update(self, raw_dt: float):
        """Advance the time-scale stack and flash timers.

        Call **after** the game loop, passing the *unscaled* frame dt.
        """
        self.time_scale.update(raw_dt)
        self._update_flashes(raw_dt)

    def _update_flashes(self, dt: float):
        for flash in self._flashes[:]:
            _, remaining, total = flash
            remaining -= dt
            if remaining <= 0:
                self._flashes.remove(flash)
            else:
                flash[1] = remaining

    def render_flash(self, surface: pygame.Surface):
        """Draw active screen-flash overlays onto *surface*."""
        if not self._flashes:
            return
        size = surface.get_size()
        for color, remaining, total in self._flashes:
            t = remaining / total if total > 0 else 1.0
            alpha = max(0, min(255, int(255 * t)))
            flash_surf = pygame.Surface(size, pygame.SRCALPHA)
            flash_surf.fill((*color, alpha))
            surface.blit(flash_surf, (0, 0))

    def clear_flashes(self):
        self._flashes.clear()

    def set_camera(self, camera):
        """Update camera reference (used on respawn)."""
        self.camera = camera
