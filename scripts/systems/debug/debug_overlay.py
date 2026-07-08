from __future__ import annotations
import pygame


class DebugOverlay:
    """Engine debug overlay — toggled with F3, rendered on the display surface.

    Collects runtime statistics from game scene references each frame and
    displays them in a scrolling panel. Also exposes the Profiler results.
    """

    def __init__(self, font: pygame.font.Font):
        self._font = font
        self._visible = False
        self._profiler_visible = False
        self._bg_color = (0, 0, 0, 160)
        self._text_color = (200, 200, 200)
        self._header_color = (100, 255, 100)
        self._value_color = (255, 255, 255)

    def toggle(self):
        self._visible = not self._visible

    def toggle_profiler(self):
        self._profiler_visible = not self._profiler_visible

    @property
    def visible(self) -> bool:
        return self._visible

    def render(self, screen: pygame.Surface, ctx, game_scene):
        if not self._visible:
            return
        lines = []
        self._collect_general(ctx, game_scene, lines)
        self._collect_entities(ctx, game_scene, lines)
        self._collect_pools(game_scene, lines)
        self._collect_audio(ctx, lines)
        self._collect_events(ctx, lines)
        self._collect_camera(game_scene, lines)
        if self._profiler_visible:
            self._collect_profiler(game_scene, lines)

        self._draw_panel(screen, lines)

    def _collect_general(self, ctx, game_scene, lines):
        fps = int(getattr(ctx, 'fps', 0))
        dt = getattr(ctx, 'dt', 0)
        tween_count = game_scene.tween_system.count if hasattr(game_scene, 'tween_system') else 0
        lines.append(('FPS', f'{fps}'))
        lines.append(('Frame time', f'{dt*1000:.1f} ms'))

        time_scale = 1.0
        if hasattr(game_scene, 'gamefeel') and game_scene.gamefeel:
            time_scale = game_scene.gamefeel.time_scale.scale
        if time_scale < 1.0:
            lines.append(('Time scale', f'{time_scale:.2f}'))
        lines.append(('Tweens', f'{tween_count}'))
        lines.append(('', ''))

    def _collect_entities(self, ctx, game_scene, lines):
        em = game_scene.entity_manager
        entity_count = len(em.entities) if hasattr(em, 'entities') else 0
        lines.append(('Entities', f'{entity_count}'))
        cm = game_scene.component_manager

        proj_count = 0
        if hasattr(game_scene, 'combat_system') and game_scene.combat_system:
            fps = getattr(game_scene.combat_system, 'projectile_system', None)
            if fps and hasattr(fps, 'active_indices'):
                proj_count = len(fps.active_indices)

        particle_count = 0
        if hasattr(game_scene, 'render_system') and game_scene.render_system:
            ps = getattr(game_scene.render_system, 'particle_effect_system', None)
            if ps and hasattr(ps, 'active_indices'):
                particle_count = len(ps.active_indices)

        lines.append(('Projectiles', f'{proj_count}'))
        lines.append(('Particles', f'{particle_count}'))

        # Collision grid size
        cg = getattr(game_scene, 'level', None)
        if cg and hasattr(cg, 'collision_grid'):
            lines.append(('Collision cells', f'{len(cg.collision_grid)}'))

    def _collect_pools(self, game_scene, lines):
        lines.append(('', ''))

        pools = []
        if hasattr(game_scene, 'combat_system') and game_scene.combat_system:
            fps = getattr(game_scene.combat_system, 'projectile_system', None)
            if fps and hasattr(fps, 'pool'):
                pools.append(('Proj pool', fps.pool))
        if hasattr(game_scene, 'render_system') and game_scene.render_system:
            ps = getattr(game_scene.render_system, 'particle_effect_system', None)
            if ps and hasattr(ps, 'pool'):
                pools.append(('Part pool', ps.pool))

        for label, pool in pools:
            u = pool.utilization if hasattr(pool, 'utilization') else 0
            lines.append((label, f'{pool.active_count}/{pool.capacity} ({u*100:.0f}%)'))

    def _collect_audio(self, ctx, lines):
        audio = getattr(ctx, 'audio_manager', None)
        if audio:
            s = audio.stats
            lines.append(('', ''))
            lines.append(('Audio req/s', f'{s.get("requests", 0)}'))
            lines.append(('Audio played', f'{s.get("played", 0)}'))
            lines.append(('Audio dropped', f'{s.get("dropped", 0)}'))
            lines.append(('Audio active ch', f'{s.get("active_channels", 0)}'))
            lines.append(('Audio cached', f'{s.get("cached_sounds", 0)}'))

    def _collect_events(self, ctx, lines):
        em = getattr(ctx, 'event_manager', None)
        if em:
            s = em.stats() if hasattr(em, 'stats') else {}
            lines.append(('', ''))
            lines.append(('Legacy subs', f'{s.get("legacy_subscribers", 0)}'))
            lines.append(('Typed subs', f'{s.get("typed_subscribers", 0)}'))

    def _collect_camera(self, game_scene, lines):
        camera = getattr(game_scene, 'camera', None)
        if camera:
            scroll = getattr(camera, 'scroll', None)
            if scroll:
                lines.append(('', ''))
                lines.append(('Camera', f'({int(scroll.x)}, {int(scroll.y)})'))
            shake = getattr(camera, 'shake_offset', None)
            if shake and (shake.x != 0 or shake.y != 0):
                lines.append(('Shake', f'({shake.x:.1f}, {shake.y:.1f})'))

    def _collect_profiler(self, game_scene, lines):
        profiler = getattr(game_scene, 'profiler', None)
        if not profiler:
            return
        lines.append(('', ''))
        lines.append(('-- Profiler --', ''))
        for tag, data in profiler.stats.items():
            avg = data.get('avg_ms', 0)
            last = data.get('last_ms', 0)
            if avg > 0:
                lines.append((tag, f'{avg:.2f} avg  {last:.2f} ms'))

    def _draw_panel(self, screen, lines):
        if not self._font:
            return
        line_h = self._font.get_height() + 2
        x, y = 10, 30
        # Background panel
        panel_w = 260
        panel_h = len(lines) * line_h + 10
        if panel_h > 0:
            bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 180))
            screen.blit(bg, (x, y - 4))

        for label, value in lines:
            if not label and not value:
                y += 4
                continue
            if value == '':
                # Header line
                text = self._font.render(label, True, self._header_color)
            else:
                text = self._font.render(f'{label}: {value}', True, self._text_color)
            screen.blit(text, (x + 4, y))
            y += line_h

    @classmethod
    def should_toggle(cls, ctx) -> bool:
        inp = getattr(ctx, 'input_system', None)
        if inp and hasattr(inp, 'was_pressed'):
            return inp.was_pressed(pygame.K_F3)
        return False

    @classmethod
    def should_toggle_profiler(cls, ctx) -> bool:
        inp = getattr(ctx, 'input_system', None)
        if inp and hasattr(inp, 'was_pressed'):
            return inp.was_pressed(pygame.K_F4)
        return False
