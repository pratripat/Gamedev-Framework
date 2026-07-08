# Sprint 4 (Final) — Completion Report

**Date:** 2026-07-08
**Engine Version:** v1.0.0
**Status:** FROZEN — ready for Pawn's Gambit to branch into its own repository.

---

## Changes Made

### 1. Audio Framework — Polish & Integration

**Pre-existing system** — the audio framework was already present but had bugs and was never wired into gameplay.

**Fixes applied:**
- `AudioManager.play_music()` was ignoring its `filepath` parameter; added `MusicManager.load_and_play()` and fixed the dispatch
- Removed unnecessary music channel reservation (`pygame.mixer.music` has its own dedicated channel)
- Removed dead code in `MixerGroup` (`add_channel()`, `channel_indices`) and `ChannelPool` (`set_volume()` by group — duplicates `MixerGroupManager`)
- Fixed `pygame.mixer.Channel` AttributeError: C extension types don't support dynamic attribute assignment. Rewrote `ChannelPool` to store allocation metadata (priority, group) internally in a typed `_AllocInfo` list instead of monkey-patching Channel objects
- `SoundCache` now emits a `warnings.warn()` on missing files instead of silently skipping

**Integration:**
- Wired `audio_manager.play()` into all 5 existing VFX event handlers: `DASH_START` → `dash`, `bomb_burst` → `explosion`, `DAMAGE` → `player_hit`, `DEATH` → `explosion`, `PROJECTILE_COLLISION` → `enemy_hit`
- Added `WATER_SPLASH` subscription for water splash sound

**Assets:**
- Generated 11 placeholder sine-wave `.wav` files in `data/audio/sfx/` matching all 9 sound IDs in `sounds.json`

### 2. Debug & Profiling Tools (New)

**Profiler** (`scripts/systems/debug/profiler.py`):
- `begin(tag)` / `end(tag)` per-frame timing API
- 60-frame rolling average per tag
- Tags: physics, rendering, animation, particles, audio, ai, gamefeel, vfx, combat
- Stats: avg_ms, last_ms, max_ms per tag; pause/resume/reset

**DebugOverlay** (`scripts/systems/debug/debug_overlay.py`):
- F3 toggles stats panel: FPS, frame time, entity count, projectile count, particle count, tween count, pool utilization (projectile + particle pools), audio stats (requests/played/dropped/active channels), event subscriber counts, camera scroll position
- F4 toggles profiler breakdown inside the panel
- Semi-transparent dark panel rendered on display surface

**Wired into GameScene:**
- `profiler.begin_frame()` at start of `update()`
- `profiler.begin(tag)` / `end(tag)` wrapping each system section
- `debug_overlay.render()` called in `render_ui()` after HUD
- F3/F4 key detection via `pygame.K_F3 in ctx.input_system.keys_pressed`

### 3. Level Path Fix (Portability)

**Problem:** Levels 1–5 stored tilemap image paths as absolute filesystem paths (e.g., `/home/user/.../data/graphics/tilemaps/grass.png`), making the project non-portable.

**Editor fixes:**
- Added `relativize()` / `absolutize()` helpers in `Level_Editor/scripts/funcs.py` using `__file__`-derived project root
- `tilemaps_manager.py`: Now stores paths relative to project root (was absolute from file dialog)
- `workspace.py` save: Relativizes tilemap keys and `autotile_config` before writing JSON
- `workspace.py` load: Resolves relative paths back to absolute for the editor's internal image loading

**Data fix:** All 5 level files (`data/levels/1.json`–`5.json`) rewritten with relative paths.

### 4. Tree Shake Rework

**Problem:** The bomb blast tree shake was a single tween kick (shift `offset.x` once, spring back). No y-axis jitter, no continuous shake feel.

**Fix:**
- Replaced one-time tween with per-frame random jitter on both x and y
- Added `_tree_shakes` dict tracking `{orig_x, orig_y, strength, timer, duration}` per entity
- `_update_tree_shakes(dt)` runs every frame: applies random offset within decaying radius, spring-back in last 0.15s
- Cleared on respawn

### 5. Tree Leaf Particles

**Problem:** Particles were small, short-lived, and used random colors.

**Fix:**
- Colors sampled from actual `foliage.png`: bright green `(96, 192, 64)`, medium `(48, 128, 64)`, dark `(32, 80, 64)` — randomly chosen per particle
- Size halved to 2.5–6 (was 5–12)
- Alpha removed (fully opaque `a=255`)
- Count increased: 25–40 (was 15–25)
- Lifetime increased: `1.2 + size * 0.15` (was `0.4 + size * 0.12`)

### 6. Bug Fix: Duplicate System Updates

**Problem:** Profiler edit accidentally duplicated `animation_system.update()` and `_update_water_ripples()` — each was called twice per frame. This caused 2x animation speed.

**Fix:** Removed duplicate blocks. Also restored AI system order (AI before physics, matching original behavior).

### 7. Setup Script (New)

- `requirements.txt`: `pygame-ce>=2.5` only (tkinter is stdlib, noted in comment)
- `run.sh`: Creates `.venv` if missing, installs deps, launches `main.py` — idempotent, works on fresh clone

### 8. Documentation (New)

| File | Content |
|------|---------|
| `docs/ENGINE.md` | Full architecture: ECS, events, update order, all 15 systems, audio pipeline, rendering pipeline, object pooling, input system, JSON validation |
| `docs/DEVELOPMENT_GUIDE.md` | Extension patterns: adding components, sounds, events, VFX profiles, profiling practice, conventions |
| `docs/LIMITATIONS.md` | Intentional gaps: no save/load, no menus, no UI framework, no lighting, no status effects, no hot reload, placeholder audio, etc. |
| `docs/TRANSITION_PROMPT.md` | Complete handoff for Pawn's Gambit AI agent: quick start, directory map, 7 critical conventions, what NOT to build, what TO build, feature checklist |
| `docs/SPRINT_REPORT.md` | This file |
| `AGENTS.md` | Updated with both Sprint 3 and Sprint 4, engine-wide conventions, frozen status |

---

## Engine v1.0.0 Assessment

### Production-Ready Systems ✅
- ECS core (component manager with query caching, entity lifecycle, JSON factory with schema validation)
- Event system (legacy kwargs + typed dataclasses)
- Audio (32 channels, 8 volume groups, cooldown/debounce, voice limiting, priority preemption, queue-based batching, music with fade/crossfade/shuffle)
- Particle system (4000 pooled, gravity/friction/wind/sway/shape emitters)
- Combat (projectile pool, hitbox/hurtbox with bitmask layers, knockback, iframes)
- Camera (smooth lerp follow, screen shake, mouse offset)
- GameFeel (stack-safe hit-stop, stack-safe slow-motion, screen shake, full-screen flash, entity squash/stretch)
- VFX (data-driven profiles, event-dispatched via 5 event bindings)
- Tween system (30+ easing functions, chaining, ping-pong, property targeting)
- ObjectPool (generic, auto-growing, with stats)
- Layered tilemap rendering with y-sort, chunk-based
- Grass system, water system with ripples, destructible environment, wind effect
- AI (FSM: idle/chase/attack/flee with data-driven configuration)
- Attack pattern system (13 bullet patterns)
- Debug overlay (toggleable stats + per-system profiler)
- Input system (keyboard + mouse, rebindable)
- Respawn system with full state reset
- Entity editor (Tkinter-based)

### Intentional Gaps (belongs in Pawn's Gambit) 🔶
- Save/load, checkpoint system
- Menu system (main menu, pause, settings, game-over)
- UI framework (widgets, layout, animations)
- Boss AI, phase transitions
- Status effects (poison, stun, burn — field exists but unprocessed)
- Production audio assets (replace placeholder beeps)
- Damage numbers, floating text
- Material/impact system
- Lighting, post-processing
- Hot reloading
- Dialogue, quests, inventory
- Loot/drop system
- Network/multiplayer

### Known Engine Issues (frozen, documented in LIMITATIONS.md) ⚠️
- `GameScene` god class (~615 lines) despite sub-manager extraction
- Service Locator anti-pattern (`GameContext`)
- No unit testing infrastructure
- `AnimationData` shared mutable state
- Single flat y-sort (O(n log n) per frame)
- 6+ late imports for circular dependency workarounds
- No component pooling (frequent add/remove GC pressure)

---

## File Inventory

```
scripts/
  game.py                        — 87 lines  | Main loop
  scenes/game_scene.py           — 615 lines | System orchestrator
  scenes/game_hud.py             — 197 lines | HUD rendering
  scenes/particle_event_coordinator.py         | VFX particle triggers
  scenes/respawn_manager.py                   | Death/respawn
  systems/audio/                 — 9 files   | Full audio framework
  systems/debug/                 — 3 files   | Profiler + DebugOverlay
  systems/gamefeel/              — 2 files   | TimeScale + GameFeelManager
  systems/vfx/                   — 2 files   | VFXManager + profiles
  systems/core/                  — 6 files   | Context, events, resources, physics
  systems/combat/                — 6+ files  | Combat, projectiles, AI
  systems/rendering/             — 5+ files  | Render, camera, particles, grass
  systems/scene/                 — 2 files   | Scene manager, level
  systems/input/                 — 2 files   | Input system
  systems/animation/             — 4 files   | Animation handler, state machine
  ecs/                           — 3 files   | Entity, component, factory
  components/                    — 10+ files | All component types
  utils/                         — 7 files   | Tween, pool, events, validator

docs/
  ENGINE.md                      — Architecture reference
  DEVELOPMENT_GUIDE.md           — Extension patterns
  LIMITATIONS.md                 — Intentional gaps
  TRANSITION_PROMPT.md           — Pawn's Gambit handoff
  SPRINT_REPORT.md               — This file

data/
  audio/sfx/                     — 11 placeholder .wav files
  config/                        — entities.json, sounds.json, level files
  graphics/                      — Sprites, animations, tilemaps
  levels/                        — 1.json through 5.json

AGENTS.md                        — Project guide
requirements.txt                 — pygame-ce>=2.5
run.sh                           — Venv setup + launch
```

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Python files | ~60 |
| Total lines of code (engine) | ~9500 |
| Engine systems | 15 |
| Documentation files | 5 + AGENTS.md |
| Sound configs | 9 sound IDs, 11 variations |
| Placeholder audio files | 11 `.wav` |
| Level files | 5 (all portable) |
| Profiler tags | 9 |
| VFX profiles | 5 |
| Bullet patterns | 13 |
| Particle pool capacity | 4000 |
| Projectile pool capacity | 4000 |
| Audio channels | 32 |
| Audio volume groups | 8 |
| Tween easing functions | 30+ |

Engine is frozen at **v1.0.0**. Future development in **Pawn's Gambit** should branch into a separate repository. See `docs/TRANSITION_PROMPT.md` for the complete handoff.
