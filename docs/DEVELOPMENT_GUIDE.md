# Development Guide

## Quick Start

```bash
python main.py
```

Toggle debug overlay: **F3** (stats panel), **F4** (profiler details inside the panel).

## Adding a New Component

1. Create class in `scripts/components/` following existing patterns (e.g., `scripts/components/physics.py`)
2. Add builder method in `EntityFactory` (`scripts/ecs/entity_factory.py`) if the component should load from JSON
3. Register in any system that needs to process it

## Adding a New Sound

1. Place `.wav` files in `data/audio/sfx/`
2. Add entry to `data/config/sounds.json` with variations, volume, cooldown, max_instances, priority, group
3. Add the sound_id to `SOUND_IDS` list in `scripts/utils/json_schemas.py` (for schema validation)
4. Call `ctx.audio_manager.play('sound_id')` from event handlers or game systems

## Adding a New Game Event

1. Option A — Legacy (string-based): Use any unique string key; emit with `event_manager.emit('my_event', **kwargs)` and subscribe with `event_manager.subscribe('my_event', callback)`
2. Option B — Typed: Create dataclass subclassing `GameEvent` in `scripts/utils/events.py`, add to `TYPED_EVENT_MAP`, register in `TYPED_EVENT_CLASSES`; emit with `emit_typed(MyEvent(...))`

## Adding a New VFX Profile

1. Add profile dict to `scripts/systems/vfx/vfx_profiles.py` mapping sub-effect names → params
2. Add `_effect_<name>` handler to `GameFeelManager` if the effect doesn't exist
3. Wire event → profile dispatch in `GameScene._subscribe_events()` or call `vfx_manager.play('profile_name')` directly

## Profiling Practice

Call `profiler.begin('my_system')` before expensive operations and `profiler.end('my_system')` after. Results appear in the debug overlay when toggled with F4.

## Conventions

- **Never use truthiness checks on entity IDs** — `if entity_id:` is buggy (IDs start at 0). Use `is None` / `is not None`.
- **Two dt conventions**: game logic uses `dt` (scaled by hit-stop/slow-motion); visual systems (tweens, HUD, audio) use `raw_dt` (unscaled).
- **Audio requests are batched** — call `play()` from any system during update; `flush()` processes all at once after rendering.
- **ComponentManager private dict**: Avoid accessing `_components` directly. Use the public API: `get()`, `add()`, `remove()`, `get_entities_with()`.
- **Schema defaults must match builder defaults** in `EntityFactory` — otherwise `load_and_validate()` fills in schema defaults that conflict with Python code defaults.
