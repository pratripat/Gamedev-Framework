"""Maps generic animation frame events to concrete game actions.

Animation data can define ``frame_events`` — a list of
``{frame: number, event: string}`` entries.  When the animation crosses
a threshold, the ``AnimationEvent`` typed event is emitted.

This handler subscribes to ``ANIMATION_EVENT`` and dispatches based on
the ``event`` string so that animation authors do not need to know about
the engine's internal event types.

Registered event names (extensible):
    - footstep        →  emit GameSceneEvents.WALK (dust particles)
    - shoot           →  emit SHOOT event (legacy path)
    - spawn_particle  →  spawn a simple particle burst
    - play_sound      →  play a named sound
"""

from ...components.physics import Position, Velocity
from ...utils import GameSceneEvents
from ...utils.events import AnimationEvent


class AnimationEventHandler:
    """Listens for ``AnimationEvent`` and dispatches to game systems."""

    def __init__(self, component_manager, event_manager, render_system=None,
                 resource_manager=None):
        self.component_manager = component_manager
        self.event_manager = event_manager
        self.render_system = render_system
        self.resource_manager = resource_manager

    def handle(self, event: AnimationEvent):
        handler = self._dispatch.get(event.event)
        if handler:
            handler(event)

    def handle_kwargs(self, **kwargs):
        """Bridge for string-based emit events (from Animation.run())."""
        event = AnimationEvent(
            entity_id=kwargs.get('entity_id', -1),
            animation_id=kwargs.get('animation_id', ''),
            event=kwargs.get('event', ''),
        )
        self.handle(event)

    # ------------------------------------------------------------------
    # Event dispatchers  (extend this dict to add new event types)
    # ------------------------------------------------------------------

    @property
    def _dispatch(self):
        return {
            'footstep':        self._on_footstep,
            'shoot':           self._on_shoot,
            'spawn_particle':  self._on_spawn_particle,
            'play_sound':      self._on_play_sound,
        }

    def _on_footstep(self, event: AnimationEvent):
        pos = self.component_manager.get(event.entity_id, Position)
        vel = self.component_manager.get(event.entity_id, Velocity)
        if pos:
            self.event_manager.emit(
                GameSceneEvents.WALK,
                pos=pos.vec,
                vel=vel.vec if vel else (0, 0),
                entity_id=event.entity_id,
            )

    def _on_shoot(self, event: AnimationEvent):
        self.event_manager.emit(
            GameSceneEvents.SHOOT,
            entity_id=event.entity_id,
        )

    def _on_spawn_particle(self, event: AnimationEvent):
        if not self.render_system or not self.render_system.particle_effect_system:
            return
        p_sys = self.render_system.particle_effect_system
        pos = self.component_manager.get(event.entity_id, Position)
        if not pos:
            return
        p_sys.emit_fast_particle(
            x=pos.x, y=pos.y,
            vx=0, vy=0,
            lifetime=0.3,
            r=255, g=255, b=200, a=200,
            size=3,
            fade=True, shrink=True, friction=0.9,
        )

    def _on_play_sound(self, event: AnimationEvent):
        if not self.resource_manager:
            return
        try:
            self.resource_manager.play_sound(event.event)
        except Exception:
            pass
