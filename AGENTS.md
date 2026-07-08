# Project Guide for AI Agents

This is the **OptimizedGamedevFramework** repository — a reusable 2D action game engine built on Pygame-CE 2.5. **Do NOT add Pawn's Gambit game logic here.** Pawn's Gambit work belongs in a separate repository.

The engine is frozen at **v1.0** after the final sprint. All changes below document both Sprint 3 and the Final Sprint (Sprint 4).

---

## Sprint 3 — Game Feel & VFX Framework

### Systems Created

#### `scripts/systems/gamefeel/time_scale.py`
- Stack-safe time scale manipulation (hit stop, slow motion).
- `push(duration, scale=0.0)` to queue an effect; `scale` property returns effective scale.
- `update(raw_dt)` ticks stack with unscaled real time.

#### `scripts/systems/gamefeel/gamefeel_manager.py`
- Central coordinator for juice effects: hit stop, slow motion, screen shake, screen flash, entity squash.
- `play(name, **kwargs)` dispatches to `_effect_<name>` handler.
- Screen flash via `render_flash(surface)` called from `GameScene.render_ui`.
- Camera reference updated on respawn via `set_camera()`.

#### `scripts/systems/vfx/vfx_profiles.py`
- Data-driven VFX profiles as dicts (JSON-exportable schema).
- Each profile maps sub-effect names → their params.

#### `scripts/systems/vfx/vfx_manager.py`
- `play(name, **context)` reads profile, merges context with params, delegates to `GameFeelManager.play`.

### Event-to-Profile Mapping
| Event | Profile | Effects |
|---|---|---|
| `DASH_START` | `dash` | shake + slow motion |
| `bomb_burst` | `bomb` | shake + flash + hit stop + slow motion |
| `DAMAGE` (not death) | `player_damage` | shake + flash + hit stop + squash |
| `DEATH` (non-player) | `enemy_death` | shake + flash + hit stop |
| `PROJECTILE_COLLISION` | `projectile_impact` | shake + hit stop |

---

## Sprint 4 (Final) — Audio, Debug, Documentation

### Audio Framework (`scripts/systems/audio/`)

Professional audio architecture with all major features:

- **AudioManager** — central facade; `play()` queues requests, `flush()` processes once per frame after render
- **SoundConfig** — loads `data/config/sounds.json` with JSON schema validation
- **SoundCache** — preloads all Sound objects at init; warns on missing files
- **ChannelPool** — 32 channels with priority-based preemption
- **VoiceLimiter** — max simultaneous instances per sound (drops oldest)
- **Debouncer** — cooldown-based duplicate suppression per sound_id
- **MixerGroupManager** — 8 volume groups (master, music, sfx, ui, ambient, player, enemy, boss)
- **RequestQueue** — per-frame batch processing with deduplication
- **MusicManager** — playlist rotation, fade in/out, crossfade, shuffle

**Wired into**: `GameContext.init()`, `game.py` main loop (flush), `GameScene` event handlers (dash/damage/death/bomb/water splash sounds)

**Placeholder audio**: 11 `.wav` files with sine-wave beeps in `data/audio/sfx/`

### Debug & Profiling Tools (`scripts/systems/debug/`)

- **Profiler** — lightweight `begin(tag)`/`end(tag)` per-frame timing. Tracks physics, rendering, animation, particles, audio, ai, gamefeel, vfx, combat
- **DebugOverlay** — toggleable stats panel (F3) showing FPS, frame time, entity/projectile/particle/tween counts, pool utilization, audio stats, event subscriber counts, camera info; profiler breakdown toggled with F4
- Wired into `GameScene.update()` with profiler tags around each system; rendered in `render_ui()` on display surface

### Documentation (`docs/`)

- `ENGINE.md` — full architecture reference
- `DEVELOPMENT_GUIDE.md` — how to add components, sounds, events, VFX
- `LIMITATIONS.md` — honest list of intentional gaps and known issues
- `TRANSITION_PROMPT.md` — complete handoff for Pawn's Gambit AI agent

---

## Key Conventions (Engine-Wide)

1. **Entity IDs start at 0** — NEVER use truthiness checks (`if entity_id:` is a bug). Use `is None` / `is not None`.
2. **Two dt values**: `dt` = scaled (hit-stop/slow-motion), `raw_dt` = unscaled. Visual systems (tweens, HUD, time-scale) use `raw_dt`.
3. **Audio is batched**: call `play()` anytime; `flush()` processes after render.
4. **Schema defaults must match builder defaults** in `EntityFactory` — `load_and_validate()` fills schema defaults.
5. **Do NOT access `_components` directly** — use ComponentManager public API.
6. **Do NOT call `pygame.mixer.Sound.play()` directly** — always go through AudioManager.
