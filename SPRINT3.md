# Sprint 3 — Game Feel & VFX Framework

## Goal

Deliver a data-driven game-feel / juice framework (hit stop, slow motion, screen shake, screen flash, entity squash) wired into the existing game loop, plus a VFX layer that maps game events to effect profiles. Fix pre-existing rendering/entity bugs uncovered during integration, and polish feedback for bomb blasts, destructibles, and water traversal.

---

## New Files

| File | Lines | Purpose |
|---|---|---|
| `scripts/systems/gamefeel/__init__.py` | 2 | Public exports |
| `scripts/systems/gamefeel/time_scale.py` | 76 | Stack-safe time-scale manipulation (hit stop, slow motion) |
| `scripts/systems/gamefeel/gamefeel_manager.py` | 142 | Central juice coordinator — owns TimeScale, flash state, delegates to camera/tweens |
| `scripts/systems/vfx/__init__.py` | 2 | Public exports |
| `scripts/systems/vfx/vfx_profiles.py` | 49 | Data-driven VFX profile dicts (JSON-exportable schema) |
| `scripts/systems/vfx/vfx_manager.py` | 51 | Profile dispatcher — merges context with profile params → GameFeelManager |
| `scripts/scenes/respawn_manager.py` | 243 | Extracted from GameScene: death gate, respawn flow, water rescue |
| `scripts/scenes/particle_event_coordinator.py` | 145 | Extracted from GameScene: particle responses to game events |
| `scripts/scenes/game_hud.py` | 197 | Extracted from GameScene: HUD/UI including health bar, text, death overlay |
| `scripts/utils/tween.py` | 445 | New generic tween system (ported in; supports float, Vector2, Color, easing, chaining) |
| `scripts/utils/events.py` | — | Typed event classes (`ScreenShakeEvent`, `AnimationEvent`) |
| `scripts/systems/animation/animation_event_handler.py` | — | Extracted animation frame-event handler |
| `AGENTS.md` | — | AI-agent project guide |

---

## Architecture

### Game Feel Stack

```
GameScene.update()
  │
  ├─ raw_dt saved before time-scale
  ├─ dt *= gamefeel.time_scale.scale     ← game logic runs at effective speed
  ├─ tween_system.update(raw_dt)         ← visual tweens use real time
  ├─ (systems use scaled dt)
  ├─ hud.update(raw_dt)                  ← HUD uses real time
  └─ gamefeel.update(raw_dt)             ← time-scale stack ticks with real time
```

### Event-to-VFX Pipeline

```
Game event (DASH_START, bomb_burst, DAMAGE, DEATH, PROJECTILE_COLLISION)
  → VFXManager.play(name, **context)
    → reads VFX_PROFILES[name]
      → for each sub-effect: GameFeelManager.play(effect, merged_params)
        → _effect_<name>(**params) — delegates to camera / TimeScale / tweens
```

### VFX Profiles

| Profile | Effects | Active |
|---|---|---|
| `dash` | shake + slow motion | ✅ |
| `bomb` | shake + flash | ✅ (hit_stop, slow_motion reserved, commented) |
| `player_damage` | squash | ✅ (shake, flash, hit_stop removed — too exaggerated) |
| `enemy_death` | (none active) | ❌ (all effects removed) |
| `projectile_impact` | (none active) | ❌ (all effects removed) |

### Integration Points in GameScene

| Method | Responsibility |
|---|---|
| `start()` | Creates GameFeelManager, VFXManager, wires all sub-managers |
| `update()` | Saves raw_dt, applies time-scale to game logic, passes raw_dt to tweens/HUD/time-scale |
| `render_ui()` | Calls HUD.render_ui, GameFeelManager.render_flash, debug overlay |
| `_respawn()` | Recreates camera/player, updates camera ref in gamefeel + weapon_system, clears flashes |
| `_subscribe_events()` | Wires VFX event handlers for DASH_START, bomb_burst, DAMAGE, DEATH, PROJECTILE_COLLISION |
| `_update_water_ripples()` | Throttled ripple spawning from projectiles over water + player dashing over water |

---

## Bugs Fixed

### 1. Entity Factory `None` Guard

`load_and_validate` injects `None` for every component type not present in JSON. Added `if component_data is None: continue` guard in `entity_factory.py` to skip missing components.

### 2. Combat `None` Guards

`range_min`, `range_max`, `warmup` can be `None` from schema defaults. Added guards in `combat.py`. `dash_speed` also needs protection in `attack_pattern_system.py`.

### 3. Tree Visual & Collision Offset

Root cause: `load_and_validate` schema defaults differ from builder code defaults.

| Component | Schema default | Code default | Fix |
|---|---|---|---|
| `RenderComponent.center` | `False` | `True` | Added `"center": true` to foliage in `entities.json` |
| `CollisionComponent.center` | `True` | `False` | Added `"center": false` to foliage in `entities.json` |

The collision box was shifted by `(-10, -9.5)` pixels due to `center=True` subtracting half-size from offset.

### 4. Health Bar Invisible (Player ID 0)

`itertools.count()` starts at `0`. `if self.player:` evaluates `0` as falsy, skipping health bar render and update.

| Location | Broken | Fixed |
|---|---|---|
| `game_hud.py:render_ui` | `if self.player and ...` | `if self.player is not None and ...` |
| `game_hud.py:update` | `if not self.player: return` | `if self.player is None: return` |

### 5. Respawn — Stale Closure References

`_subscribe_events` captured `pis = self.player_input_system` in lambdas. After respawn the lambdas still referenced the old dead instance.

Fix: use `self.player_input_system` directly in closures so they dynamically resolve to the current instance.

### 6. Respawn — Stale WeaponSystem Camera

`_respawn()` creates `Camera()` but `WeaponSystem.camera` still pointed to the old camera whose `scroll` was at the death position. Bullets aimed at `screen_to_virtual(mouse) + old_camera.scroll`.

Fix: add `self.combat_system.weapon_system.camera = self.camera` in `_respawn()`.

---

## Polish & Juice Effects

### Bomb Blast — Tree Sway + Leaf Particles

- Queries all foliage (`WindAffectedComponent`) within blast radius
- Shifts `RenderComponent.offset.x` by up to ±30px (proportional to proximity), tweens back with `out_elastic`
- Emits 15–25 leaf particles per tree:
  - Size 4–8px, lifetime `0.4 + size * 0.12` (bigger = longer)
  - Spawn from lower half of tree (`y + 5..35`)
  - `sway=True` for sine-wave horizontal drift, `gravity=50`

### Destructible Projectile Penetration

- Removed `p.active = False` and `p.lifetime = 0` — projectile passes through destructibles
- Emits 3 small debris particles per hit (brown/grey, gravity 120, short lifetime)
- `DestructibleSystem.particle_system` linked from GameScene init

### Water Ripple Enhancement

- Ripples now carry projectile velocity (`vx`, `vy`) and drift across water surface
- Velocity decays with friction (`0.92` per frame)
- Ripple throttle reduced: `0.2s → 0.1s`, cap raised: `6 → 12`
- Scaled dt → raw_dt (ripples work during slow-motion)
- Checks **all** active projectiles instead of first 2

### Water Splash Particles (Performance)

- Count reduced: `max(1, int(1.5 * size/15))` (down from `int(10 * size/15)`)
- Size increased: `4.0–8.0` scaled by bullet size (up from fixed `2.0–4.0`)
- Particles sort slightly behind projectile (`y_offset_range=(-2, 0)`)

### Trail Particles (Big Bullets)

- Big bullets (`size > 20`): rate reduced to 40%, trail particle size `size * 0.5` (up from `size * 0.2`)

---

## Debug Overlay

Added to `GameScene.render_ui()` for foliage entities:
- **Red rect** — sprite bounds (matches render_system virtual→display math)
- **Blue rect** — collision bounds
- **Green dot** — entity Position

Coordinates scaled by `display_size / virtual_size` ratio, matching `render_system` truncation-int-then-scale approach.

---

## Code Quality

### Refactoring

GameScene was ~600 lines of inline logic. Extracted sub-managers:

| Sub-manager | Extracted from GameScene lines |
|---|---|
| `GameHUD` | FPS, bomb, dash, wind info; health bar; death overlay |
| `RespawnManager` | Death gate, respawn flow, water drowning rescue |
| `ParticleEventCoordinator` | Impact/walk/water-splash/ghost particles |
| `AnimationEventHandler` | Frame-event callbacks (footstep, shoot, etc.) |
| `TweenSystem` | New generic tween system |

### Event Manager

Added `subscribe_typed` / `emit_typed` for typed event objects alongside legacy kwargs-based emit. Added `unsubscribe_all_for(source)` for clean teardown. Added stats properties.

### Resource Manager

Added `scale` parameter to `get_image` for cursor/UI scaling.
