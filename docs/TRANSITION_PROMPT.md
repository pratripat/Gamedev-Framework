# Project Transition Prompt

You are starting work on **Pawn's Gambit**, a 2D pixel-art action game built on the **OptimizedGamedevFramework**. This document gives you complete architectural context to work effectively.

---

## Quick Start

```bash
python main.py
```
- Movement: WASD
- Shoot: Hold left-click
- Dash: L-Shift
- Bomb: Space
- Debug overlay: F3 (stats) / F4 (profiler inside overlay)
- Respawn after death: R

---

## Where Everything Lives

```
scripts/
  game.py                  — Main loop, audio flush, rendering
  scenes/
    game_scene.py          — ~570 lines: orchestrates ALL systems (the god class)
    game_hud.py            — HUD rendering (health, abilities, death overlay)
    particle_event_coordinator.py — VFX particle triggers per event
    respawn_manager.py     — Death/respawn logic
  systems/
    animation/             — Animation data, handler, state machine, event handler
    audio/                 — AudioManager + 8 supporting modules (FULL)
    combat/                — Combat, projectile, AI, hitbox, destructible, weapon
    core/                  — GameContext, EventManager, ResourceManager, PhysicsEngine
    debug/                 — Profiler, DebugOverlay (F3/F4 toggle)
    gamefeel/              — TimeScale, GameFeelManager (hit-stop, slow-motion, shake, flash)
    input/                 — Input system, PlayerInputSystem
    rendering/             — RenderSystem, Camera, Tilemap, Grass, Particles
    scene/                 — SceneManager, LevelManager
    vfx/                   — VFXManager, VFXProfiles (data-driven juice effects)
  ecs/
    entity_manager.py      — Entity lifecycle (IDs from itertools.count())
    component_manager.py   — Component storage with query caching
    entity_factory.py      — Build entities from JSON config
  components/              — All ECS components (physics, combat, animation, etc.)
  utils/                   — TweenSystem, ObjectPool, JSON validator, events, water_animator
data/
  config/                  — entities.json, sounds.json, level files, animation configs
  audio/sfx/               — Placeholder .wav files (replace with production audio)
  graphics/                — Sprites, animations, tilemaps
  levels/                  — Level JSON files (1.json - 5.json)
```

---

## Architecture in 30 Seconds

- **ECS** — Components are data dicts, Systems are update logic, Entities are int IDs
- **Event-driven** — Systems communicate through EventManager (legacy kwargs + typed dataclasses)
- **Audio** — `audio_manager.play()` → queued → `flush()` processes once per frame
- **VFX/GameFeel** — VFXManager reads data profiles → delegates to GameFeelManager → TimeScale/Camera shake/flash/squash
- **Rendering** — 550×300 virtual → scaled 2× to 1100×600 display; UI on display surface
- **Update order matters** — physics → combat → AI → particles → animation → rendering → gamefeel

---

## Critical Conventions (DO NOT VIOLATE)

1. **Entity ID zero trap**: IDs start at `0` from `itertools.count()`. NEVER write `if self.player:` — use `if self.player is not None`.
2. **Two dt values**: `dt` = scaled (affected by hit-stop/slow-motion), `raw_dt` = unscaled. Visual tweens, HUD, audio, time-scale stack use `raw_dt`. Game logic uses scaled `dt`.
3. **Audio is batched**: Call `audio_manager.play()` from any system. Do NOT call `pygame.mixer.Sound.play()` directly. The `flush()` processes all requests after render.
4. **No schema-default mismatches**: `load_and_validate()` fills schema defaults. They must match builder defaults in `EntityFactory`.
5. **No private-component access**: Use `component_manager.get()` / `.add()` / `.remove()`, not `_components`.
6. **No direct audio file playback in game code**: Always go through AudioManager with a sound_id from `sounds.json`.
7. **Entity IDs are NOT global**: They're per-session. Don't persist them, don't compare across `_respawn()` boundaries.

---

## What NOT to Build (Engine Is Frozen)

This engine repository is **frozen at v1.0**. Do NOT:

- Modify engine systems (ECS core, audio, VFX, GameFeel, rendering pipeline, event system, input, resource manager, debug tools)
- Add new systems to `scripts/systems/`
- Change engine architecture or update order
- Modify `sounds.json`, `entities.json` schemas, or core config

**Pawn's Gambit work belongs in a separate repository** that imports or forks this framework.

---

## What TO Build (Pawn's Gambit)

Pawn's Gambit should build **game-specific content** in its own repository:

- **Game logic**: story/dialogue system, quests, inventory, bosses, levels, NPCs
- **UI**: main menu, pause menu, settings, game-over screen
- **Audio**: production `.wav`/`.ogg` files replacing placeholders
- **Content**: level design, entity configurations, attack patterns, enemy behaviors
- **Game systems**: save/load, progression, unlockables, shop/upgrade system
- **Per-game polish**: custom shaders, lighting, damage numbers, floating text, impact system

---

## Engine Feature Summary (Post-Sprint 3 + Final Sprint)

### Present ✅
- ECS with query caching, entity lifecycle, JSON factory
- Event system (legacy + typed)
- Audio manager (32 channels, groups, cooldowns, voice limits, priority, dedup, music with crossfade)
- Particle system (4000 pooled, with gravity/friction/wind/shape emitters)
- Combat (projectile pool, hitbox/hurtbox with bitmask layers, knockback, iframes)
- Enemy AI (FSM: idle/chase/attack/flee)
- GameFeel (hit-stop stack, slow-motion stack, screen shake, flash, entity squash)
- VFX (data-driven profiles, event-dispatched)
- Tween system (30+easing functions, chaining, ping-pong)
- Camera (smooth lerp, shake, mouse offset)
- ObjectPool (generic, with stats)
- JSON validation (for entities, animations, levels, sounds)
- Grass system, water system, destructible environment, wind effect
- Debug overlay (toggleable stats panel + per-system profiler)
- Attack pattern system (13 bullet patterns)
- Respawn system
- Layered tilemap rendering with y-sort

### Intentional Gaps (Don't Fix Here)
- Save/load system — belongs in Pawn's Gambit
- Menu system — belongs in Pawn's Gambit
- UI framework — belongs in Pawn's Gambit
- Boss AI — belongs in Pawn's Gambit
- Status effects — belongs in Pawn's Gambit
- Production audio — belongs in Pawn's Gambit (replace placeholder beeps)
- Lighting/post-processing — future engine upgrade
- Hot reloading — future engine upgrade
- Network/multiplayer — out of scope
- Dialogue system — belongs in Pawn's Gambit
- Inventory/items — belongs in Pawn's Gambit
- Damage numbers — belongs in Pawn's Gambit
