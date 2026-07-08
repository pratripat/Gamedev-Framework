"""
Typed Event System

Provides typed event dataclasses to replace ad-hoc kwargs-based event
dispatching. All existing GameSceneEvents have a corresponding typed event.

Design:
- Each event is a dataclass extending GameEvent
- The EventManager maps typed events to their GameSceneEvents enum value
  so existing subscribers still work
- New code should emit_typed() and can subscribe via subscribe_typed()
"""

from dataclasses import dataclass, field
from typing import Any, Optional
import pygame

from scripts.utils import GameSceneEvents


class GameEvent:
    """Base class for all typed game events."""
    _event_type: Any = None

    @classmethod
    def event_type(cls):
        return cls._event_type


# ---------------------------------------------------------------------------
# Typed event definitions
# ---------------------------------------------------------------------------

@dataclass
class DamageEvent(GameEvent):
    entity_id: int
    proj_id: int = -1
    damage: float = 0.0
    effects: list = field(default_factory=list)
    proj_vel: Optional[pygame.Vector2] = None
    proj_pos: Optional[pygame.Vector2] = None
    death: bool = False


@dataclass
class DeathEvent(GameEvent):
    entity_id: int
    proj_vel: Optional[pygame.Vector2] = None
    proj_pos: Optional[pygame.Vector2] = None
    death: bool = True


@dataclass
class ShootEvent(GameEvent):
    entity_id: int


@dataclass
class ProjectileCollisionEvent(GameEvent):
    pos: Any
    vel: Any
    target_type: str = "environment"
    size: float = 10.0


@dataclass
class WalkEvent(GameEvent):
    pos: Any
    vel: Any
    entity_id: int


@dataclass
class WaterSplashEvent(GameEvent):
    pos: Any
    vel: Any
    size: float = 10.0


@dataclass
class ScreenShakeEvent(GameEvent):
    intensity: float = 5.0
    duration: float = 0.5


@dataclass
class DashStartEvent(GameEvent):
    entity_id: int
    duration: float


@dataclass
class AnimationFinishedEvent(GameEvent):
    entity_id: int
    animation_id: str


@dataclass
class CollisionEvent(GameEvent):
    entity_id: int
    collisions: dict


@dataclass
class SpawnGhostEvent(GameEvent):
    entity_id: int


@dataclass
class RemoveEntityEvent(GameEvent):
    entity_id: int


@dataclass
class BombBurstEvent(GameEvent):
    entity_id: int


@dataclass
class AnimationEvent(GameEvent):
    """Generic animation-frame event (footstep, shoot, etc.)."""
    entity_id: int
    animation_id: str
    event: str


# ---------------------------------------------------------------------------
# Map typed events to their GameSceneEvents enum values
# ---------------------------------------------------------------------------

TYPED_EVENT_MAP: dict[type, GameSceneEvents] = {
    DamageEvent: GameSceneEvents.DAMAGE,
    DeathEvent: GameSceneEvents.DEATH,
    ShootEvent: GameSceneEvents.SHOOT,
    ProjectileCollisionEvent: GameSceneEvents.PROJECTILE_COLLISION,
    WalkEvent: GameSceneEvents.WALK,
    WaterSplashEvent: GameSceneEvents.WATER_SPLASH,
    ScreenShakeEvent: GameSceneEvents.SCREEN_SHAKE,
    DashStartEvent: GameSceneEvents.DASH_START,
    AnimationFinishedEvent: GameSceneEvents.ANIMATION_FINISHED,
    CollisionEvent: GameSceneEvents.COLLISION,
    SpawnGhostEvent: GameSceneEvents.SPAWN_GHOST,
    RemoveEntityEvent: GameSceneEvents.REMOVE_ENTITY,
    AnimationEvent: GameSceneEvents.ANIMATION_EVENT,
}

TYPED_EVENT_CLASSES: dict[GameSceneEvents, type] = {
    v: k for k, v in TYPED_EVENT_MAP.items()
}
