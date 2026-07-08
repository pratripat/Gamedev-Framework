# Engine Architecture

## Overview

OptimizedGamedevFramework is a 2D action game engine built on Pygame-CE 2.5 with an ECS (Entity-Component-System) architecture. Designed for pixel-art bullet-hell games with heavy particle/VFX emphasis.

---

## ECS Core

### `ComponentManager` (`scripts/ecs/component_manager.py`)
Stores components as `{type: {entity_id: instance}}`. Supports AND/OR entity queries with caching.

```python
cm.add(entity_id, SomeComponent(...))
cm.get(entity_id, SomeComponent)  # -> Optional[SomeComponent]
cm.get_entities_with(ComponentA, ComponentB)  # -> list[int]
```

Component queries are cached; cache invalidates on `add()`/`remove()`.

### `EntityManager` (`scripts/ecs/entity_manager.py`)
Auto-incrementing IDs (`itertools.count()`), lifecycle tracking via `entities` (set), `to_remove` (list), `dead_entities` (set). `refresh_entities(dt)` processes removals and death timers.

### `EntityFactory` (`scripts/ecs/entity_factory.py`)
Builds entities from `data/config/entities.json` using `load_and_validate()` for JSON schema validation. 17+ builder methods covering player, enemies, destructibles, foliage, collision boxes, items.

Key convention: Schema defaults must match builder defaults. Entity IDs start at `0` — use `is None` / `is not None` checks, never truthiness.

---

## Event System

### `EventManager` (`scripts/systems/core/event_manager.py`)
Dual subscription system:

| Method | Description |
|--------|-------------|
| `subscribe(event_type, callback, source)` | Legacy string-based (kwargs) |
| `subscribe_typed(event_class, callback, source)` | Typed event dataclasses |
| `emit(event_type, **kwargs)` | Fire legacy event |
| `emit_typed(event_object)` | Fire typed event |

Events defined in `scripts/utils/events.py` (typed dataclasses) and `scripts/utils/__init__.py` (`GameSceneEvents` enum).

---

## Core Loop

`scripts/game.py` — main loop:

```
calculate_dt() → update() → render() → audio_manager.flush()
```

- `render()`: renders virtual surface (550×300) → scales 2× to display (1100×600) → renders UI on display surface
- `ctx.fps` and `ctx.dt` are set on the context before scene rendering

---

## Update Order (GameScene.update)

1. **Profiler begin_frame** + debug overlay toggle
2. **Death gate** — skip if dead
3. **Time scale** — apply GameFeel hit-stop/slow-motion to game dt
4. **Tweens** — run with unscaled `raw_dt`
5. **Physics** — timer, water status, quadtree, player input, physics engine
6. **Combat** — combat system, destructible system
7. **AI** — enemy AI update
8. **Particles** — water ripples
9. **Animation** — animation system
10. **Rendering** — render system, entity refresh, tilemap, camera
11. **GameFeel / VFX** — HUD, gamefeel update (with raw_dt)

Systems receive **scaled dt** (affected by hit-stop/slow-motion). Visual systems (tweens, HUD, time-scale stack) receive **raw unscaled dt**.

---

## Systems Overview

### `scripts/systems/`

| Directory | Purpose |
|-----------|---------|
| `animation/` | Animation data, handler, state machine, event handler |
| `audio/` | AudioManager, SoundCache, ChannelPool, MixerGroup, MusicManager, etc. |
| `combat/` | Combat, projectile, AI, hitbox, destructible, weapon systems |
| `core/` | GameContext, EventManager, ResourceManager, PhysicsEngine, CollisionGrid, TimerSystem |
| `debug/` | Profiler, DebugOverlay |
| `gamefeel/` | TimeScale (hit-stop/slow-motion), GameFeelManager (shake, flash, squash) |
| `input/` | Input, PlayerInputSystem |
| `rendering/` | RenderSystem, Camera, Tilemap, Grass, Particles, Effects |
| `scene/` | SceneManager, LevelManager |
| `vfx/` | VFXManager, VFXProfiles (data-driven effect profiles) |

### Audio System

Central facade `AudioManager` owns:
- `SoundConfig` — loads `sounds.json` with validation
- `SoundCache` — preloads all Sound objects at init
- `ChannelPool` — 32 channels with priority preemption
- `VoiceLimiter` — max instances per sound, drops oldest
- `Debouncer` — cooldown-based duplicate suppression
- `MixerGroupManager` — 8 groups (master, music, sfx, ui, ambient, player, enemy, boss)
- `RequestQueue` — per-frame batching with deduplication
- `MusicManager` — background music with fade in/out/crossfade, playlist rotation

Wired: `GameContext.init()` creates `AudioManager`, `game.py` calls `flush()` after render, `GameScene` event handlers call `play()` for damage/death/dash/explosion/water splash.

### GameFeel System

- **TimeScale** (`scripts/systems/gamefeel/time_scale.py`): Stack-safe time manipulation. `push(duration, scale)` queues effects; `scale` property returns effective scale.
- **GameFeelManager** (`scripts/systems/gamefeel/gamefeel_manager.py`): Central juice coordinator. `play(name, **kwargs)` dispatches to `_effect_<name>` handlers for shake, flash, squash, hit-stop, slow-motion.

### VFX System

- **VFXProfiles** (`scripts/systems/vfx/vfx_profiles.py`): Dict-based data-driven profiles mapping sub-effects to params.
- **VFXManager** (`scripts/systems/vfx/vfx_manager.py`): `play(name, **context)` reads profile, merges context, delegates to GameFeelManager.

### Debug System

- **Profiler** (`scripts/systems/debug/profiler.py`): Per-frame timing with `begin(tag)`/`end(tag)` API. Tags: physics, rendering, animation, particles, audio, ai, gamefeel, vfx, combat.
- **DebugOverlay** (`scripts/systems/debug/debug_overlay.py`): Toggleable (F3) stats panel showing FPS, entity/projectile/particle/tween counts, pool utilization, audio stats, event subs, camera info, and profiler results (F4).

---

## Resource Management

- **ResourceManager** (`scripts/systems/core/resource_manager.py`): Caches images, spritesheets, tilemaps. Audio uses its own `SoundCache`.
- **AnimationHandler** (`scripts/systems/animation/animation_handler.py`): Loads animation configs from `data/graphics/animations/`.
- JSON configs in `data/config/`: `entities.json`, `sounds.json`, level files, animation config.

---

## Rendering Pipeline

1. Virtual resolution (550×300) — all game rendering
2. Scaled 2× to display (1100×600) via `pygame.transform.scale`
3. UI/debug HUD rendered directly on display surface

Y-sort rendering: single sorted queue of `(sort_y, type, surface, position, ...)` tuples. Tilemap layers pre-baked per chunk.

---

## Object Pooling

- Generic `ObjectPool` in `scripts/utils/object_pool.py` with free-list, pre-allocation, stats tracking.
- Used by: `FastProjectileSystem` (4000), `ParticleEffectSystem` (4000), `ChannelPool` (32).

---

## JSON Validation

`scripts/utils/json_validator.py` provides `load_and_validate(path, schema)` used for entities, animations, levels, sounds. Schemas in `json_schemas.py`.

---

## Input System

`Input` class processes raw Pygame events → maps to `Inputs` enum values → emits via EventManager. Supports keys_pressed, keys_released, keys_held, mouse_clicked, mouse_held binds.
