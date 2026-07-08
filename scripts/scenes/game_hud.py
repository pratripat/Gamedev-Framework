import pygame
import random
from ..components.combat import HealthComponent
from ..utils import GameSceneEvents


class GameHUD:
    """Manages all HUD/UI rendering: health bar, ability info, death overlay, text cache."""

    def __init__(self, component_manager, font, health_bar_img, event_manager):
        self.component_manager = component_manager
        self.font = font
        self.health_bar_img = health_bar_img
        if self.health_bar_img:
            self.health_bar_img.set_colorkey((0, 0, 0))

        self.player = None
        self.player_input_system = None
        self.render_system = None

        self.health_drain = 100.0
        self.health_red = (228, 59, 68)
        self.health_orange = (247, 118, 34)
        self.hb_scale_juice = 1.0
        self.hb_rot_juice = 0.0
        self.is_dead = False

        self._ui_text_cache = None

        # Health bar juice trigger
        def trigger_hb_juice(entity_id, **kwargs):
            if entity_id == self.player:
                self.hb_scale_juice = 1.1
                self.hb_rot_juice = random.uniform(-3, 3)

        event_manager.subscribe(GameSceneEvents.DAMAGE, trigger_hb_juice)

    def set_player(self, player, player_input_system, render_system):
        self.player = player
        self.player_input_system = player_input_system
        self.render_system = render_system
        p_health = self.component_manager.get(player, HealthComponent)
        if p_health:
            self.health_drain = p_health.health

    def set_dead(self, dead):
        self.is_dead = dead

    def update(self, dt):
        if self.player is None:
            return
        p_health = self.component_manager.get(self.player, HealthComponent)
        if p_health:
            if self.health_drain > p_health.health:
                self.health_drain = max(p_health.health, self.health_drain - 40.0 * dt)
            else:
                self.health_drain = p_health.health

        self.hb_scale_juice = 1.0 + (self.hb_scale_juice - 1.0) * (0.9 ** (dt * 60))
        self.hb_rot_juice *= (0.9 ** (dt * 60))

    def reset(self):
        self.health_drain = 100.0
        self.hb_scale_juice = 1.0
        self.hb_rot_juice = 0.0
        self.is_dead = False

    def render_ui(self, screen, ctx):
        if self.font:
            if self._ui_text_cache is None:
                self._ui_text_cache = {}

            def get_cached_text(text, color):
                key = (text, color)
                if key not in self._ui_text_cache:
                    self._ui_text_cache[key] = self.font.render(text, True, color)
                return self._ui_text_cache[key]

            if len(self._ui_text_cache) > 200:
                self._ui_text_cache.clear()

            ui_blits = []

            fps_val = int(getattr(ctx, 'fps', 0))
            fps_text = f"FPS: {fps_val}"
            text_surf = get_cached_text(fps_text, (255, 255, 255))
            shadow = get_cached_text(fps_text, (0, 0, 0))
            ui_blits.append((shadow, (11, 11)))
            ui_blits.append((text_surf, (10, 10)))

            if self.player_input_system:
                bomb_timer = getattr(self.player_input_system, 'bomb_timer', 0.0)
                if bomb_timer and bomb_timer > 0:
                    bomb_text = f"Bomb CD: {bomb_timer:.1f}s"
                else:
                    bomb_text = "Bomb: Ready"
                bomb_surf = get_cached_text(bomb_text, (255, 200, 0))
                bomb_shadow = get_cached_text(bomb_text, (0, 0, 0))
                ui_blits.append((bomb_shadow, (11, 31)))
                ui_blits.append((bomb_surf, (10, 30)))

                dash_charges = getattr(self.player_input_system, 'dash_charges', 0)
                dash_refill = getattr(self.player_input_system, 'dash_refill_timer', 0.0)
                is_dashing = getattr(self.player_input_system, 'is_dashing', False)
                dash_text = f"Dashes: {dash_charges} | Refill: {dash_refill:.1f}s"
                if is_dashing:
                    dash_text += " [DASHING]"
                dash_surf = get_cached_text(dash_text, (0, 255, 255))
                dash_shadow = get_cached_text(dash_text, (0, 0, 0))
                ui_blits.append((dash_shadow, (11, 51)))
                ui_blits.append((dash_surf, (10, 50)))

            if self.render_system and hasattr(self.render_system, 'wind_system'):
                wind_mag = getattr(self.render_system.wind_system, 'magnitude_x', 0.0)
                wind_text = f"Wind X: {wind_mag:+.2f}"
                wind_surf = get_cached_text(wind_text, (200, 255, 200))
                wind_shadow = get_cached_text(wind_text, (0, 0, 0))
                ui_blits.append((wind_shadow, (11, 71)))
                ui_blits.append((wind_surf, (10, 70)))

            if ui_blits:
                screen.blits(ui_blits)

        # Health Bar
        if self.player is not None and self.health_bar_img:
            p_health = self.component_manager.get(self.player, HealthComponent)
            if p_health:
                hb_base_scale = 0.5
                bw, bh = int(self.health_bar_img.get_width() * hb_base_scale), int(self.health_bar_img.get_height() * hb_base_scale)
                temp_hb_surf = pygame.Surface((bw, bh))
                MASK_COLOR = (0, 0, 1)
                temp_hb_surf.fill(MASK_COLOR)

                inner_padding_x = 4 * hb_base_scale
                inner_padding_y = 4 * hb_base_scale
                inner_w = bw - (inner_padding_x * 2)
                inner_h = bh - (inner_padding_y * 2)

                health_ratio = p_health.health / p_health.max_health
                drain_ratio = self.health_drain / p_health.max_health

                if drain_ratio > health_ratio:
                    drain_rect = pygame.Rect(inner_padding_x, inner_padding_y, int(inner_w * drain_ratio), inner_h)
                    pygame.draw.rect(temp_hb_surf, self.health_orange, drain_rect)

                health_rect = pygame.Rect(inner_padding_x, inner_padding_y, int(inner_w * health_ratio), inner_h)
                pygame.draw.rect(temp_hb_surf, self.health_red, health_rect)

                scaled_frame = pygame.transform.scale(self.health_bar_img, (bw, bh))
                scaled_frame.set_colorkey((0, 0, 0))
                temp_hb_surf.blit(scaled_frame, (0, 0))

                final_hb_scale = 1.5 * self.hb_scale_juice
                if final_hb_scale != 1.0:
                    new_w = int(bw * (final_hb_scale / hb_base_scale))
                    new_h = int(bh * (final_hb_scale / hb_base_scale))
                    temp_hb_surf = pygame.transform.scale(temp_hb_surf, (new_w, new_h))

                if self.hb_rot_juice != 0:
                    temp_hb_surf = pygame.transform.rotate(temp_hb_surf, self.hb_rot_juice)

                temp_hb_surf.set_colorkey(MASK_COLOR)

                pos_x = (screen.get_width() - temp_hb_surf.get_width()) // 2
                pos_y = screen.get_height() - temp_hb_surf.get_height() - 10
                screen.blit(temp_hb_surf, (pos_x, pos_y))

        # Death overlay
        if self.is_dead:
            self._render_death_overlay(screen)

    def _render_death_overlay(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        try:
            big_font = pygame.font.SysFont(None, 72)
            small_font = pygame.font.SysFont(None, 36)
        except Exception:
            big_font = self.font
            small_font = self.font
        if big_font:
            death_text = big_font.render("YOU DIED", True, (200, 50, 50))
            death_shadow = big_font.render("YOU DIED", True, (0, 0, 0))
            dw, dh = death_text.get_size()
            sx = (screen.get_width() - dw) // 2
            sy = (screen.get_height() - dh) // 2 - 40
            screen.blit(death_shadow, (sx + 2, sy + 2))
            screen.blit(death_text, (sx, sy))
        if small_font:
            respawn_text = small_font.render("Press R to Respawn", True, (255, 255, 255))
            respawn_shadow = small_font.render("Press R to Respawn", True, (0, 0, 0))
            rw, rh = respawn_text.get_size()
            rx = (screen.get_width() - rw) // 2
            ry = (screen.get_height() - rh) // 2 + 20
            screen.blit(respawn_shadow, (rx + 2, ry + 2))
            screen.blit(respawn_text, (rx, ry))
