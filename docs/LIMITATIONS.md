# Limitations & Intentional Gaps

## Critical Gaps

- **No save/load system** — game state cannot be persisted. `_respawn()` reloads the entire level.
- **No menu system** — no main menu, pause menu, settings, or inventory.
- **No UI framework** — all UI is procedural `pygame.font.Font.render()` + `blit()`.
- **Single scene** (`GameScene`) is a ~570-line orchestrator; no other scenes exist.
- **No lighting or post-processing** — render pipeline is direct blit with no lighting pass.

## Audio

- Placeholder `.wav` files only — simple sine-wave beeps, not production sound effects.
- Crossfade uses `pygame.mixer.music.queue()` which doesn't overlap tracks (pygame limitation).
- `pitch_variation` defined in config but never applied (pygame has no native pitch control).
- `max_distance` defined but never used for spatial audio attenuation.
- No audio pausing/resuming lifecycle tied to game pause.

## Combat

- No status effects (`effects` field on projectiles is dead data).
- No damage types or modifier pipeline.
- Iframes are player-only in `HitBoxSystem`.
- Knockback is enemy-only.
- No material/impact system — all collisions generate same VFX.

## AI

- Single FSM-based AI with hardcoded transitions. No behavior tree.
- No perception system — enemies always know player position globally.
- PATROL state is a stub (print-only, never transitioned to).
- O(n²) ally search in support behavior.
- No boss AI — zero boss-specific code exists.

## Animation

- No blend transitions — animations hard-swap.
- `AnimationData` mutates shared spritesheet state (cross-entity mutation risk).
- Render cache clears at 60 entries (periodic thrash).
- Flip is handled with separate animation entries instead of programmatic flip.

## Rendering

- Single flat y-sort queue — O(n log n) per frame.
- Sort key is `pos.y` not bottom-of-sprite (tall sprites sort incorrectly).
- No GPU acceleration for particles.
- No per-layer blend mode configuration.

## Engine

- `GameContext` is a Service Locator anti-pattern — hard to mock for testing.
- 6+ late imports work around circular dependencies.
- No hot-reloading — config/code changes require restart.
- Entity IDs are raw ints with no wrapper type.
- No entity hierarchy/parenting.
- Component queries cache invalidates on every single add/remove.
- `EntityManager` has knowledge of `ParticleEmitter` (ECS violation).

## Debug Tools

- Debug overlay renders on display surface (not virtual) — may not scale perfectly.
- Profiler is opt-in — only systems with `begin()`/`end()` calls are tracked.
- No collision visualization or quadtree debug rendering.
- No network support — local single-player only.
