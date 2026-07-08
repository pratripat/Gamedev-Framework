# OptimizedGamedevFramework

A reusable 2D action game engine built on **Pygame-CE 2.5+** with ECS architecture, built-in VFX, audio, and debug tooling. Designed for pixel-art bullet-hell games.

**Engine v1.0.0 — frozen.** Game-specific work (Pawn's Gambit) lives in a separate repository.

---

## Quick Start

```bash
./run.sh
```

Auto-creates a virtual environment, installs `pygame-ce`, and launches the game.

### Controls

| Key | Action |
|-----|--------|
| WASD | Move |
| Left-click (hold) | Shoot |
| L-Shift | Dash |
| Space | Bomb |
| R | Respawn after death |
| F3 | Debug overlay (stats panel) |
| F4 | Profiler breakdown (inside overlay) |

---

## Features

- **ECS** — Entity-component-system with query caching, JSON factory, and schema validation
- **Audio** — 32 channels, 8 volume groups, voice limiting, cooldowns, priority preemption, queue-based batching, music with crossfade. 11 placeholder WAVs included
- **Particles** — 4000 pooled slots with gravity, friction, wind, sway, shape emitters
- **Combat** — Projectile pool (4000), hitbox/hurtbox with bitmask layers, knockback, iframes, 13 bullet patterns
- **GameFeel** — Stack-safe hit-stop and slow-motion, screen shake, full-screen flash, entity squash/stretch
- **VFX** — Data-driven profiles dispatched on game events (dash, bomb, damage, death, projectile impact)
- **Tween** — 30+ easing functions, chaining, ping-pong, property targeting
- **Camera** — Smooth lerp follow, screen shake, mouse offset
- **Debug** — Toggleable stats overlay (F3) and per-system profiler (F4)
- **Tiled levels** — JSON level files with layered tilemaps, y-sort, and auto-tiling
- **Grass system** — Perlin-noise clumping, wind interaction, physics
- **Water** — Animated frames, ripples, splash particles
- **Object pooling** — Generic pool with free-list, auto-growth, and stats
- **Entity editor** — Tkinter-based standalone editor

---

## Architecture

```
scripts/
  game.py                  Main loop
  scenes/game_scene.py     System orchestrator (~615 lines)
  scenes/game_hud.py       HUD rendering
  ecs/                     EntityManager, ComponentManager, EntityFactory
  components/              All ECS component types
  systems/
    core/                  GameContext, EventManager, ResourceManager, PhysicsEngine
    audio/                 Full audio framework (9 modules)
    combat/                Combat, projectiles, AI, hitbox, destructible
    rendering/             RenderSystem, Camera, Tilemap, Particles, Grass
    animation/             Animation handler, state machine, event handler
    gamefeel/              TimeScale, GameFeelManager
    vfx/                   VFXManager + data-driven profiles
    debug/                 Profiler, DebugOverlay
    input/                 Input system + player input
    scene/                 SceneManager, LevelManager
  utils/                   TweenSystem, ObjectPool, JSON validator/events
```

---

## Documentation

| File | Content |
|------|---------|
| `docs/ENGINE.md` | Full architecture reference |
| `docs/DEVELOPMENT_GUIDE.md` | How to add components, sounds, events, VFX |
| `docs/LIMITATIONS.md` | Intentional gaps and known issues |
| `docs/TRANSITION_PROMPT.md` | Complete handoff for Pawn's Gambit |
| `docs/SPRINT_REPORT.md` | Final sprint report |
| `AGENTS.md` | Convention cheat sheet |

---

## Requirements

- Python 3.10+
- `pygame-ce >= 2.5` (installed automatically by `run.sh`)
- On Linux: `python3-tk` for the entity editor (optional, `sudo apt install python3-tk`)
