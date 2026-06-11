import pygame, math
from ...utils import CENTER, INITIAL_WINDOW_SIZE

from ...components.physics import Position, Velocity
from ...components.animation import RenderComponent, AnimationComponent
from ...components.render_effect import RenderEffectComponent, YSortRender, ShadowComponent, WindAffectedComponent, PulseComponent

from .wind_system import WindSystem
from ..animation.animation_state_machine import AnimationStateMachine
from .render_effect_system import RenderEffectSystem
from .particle_effect_system import ParticleEffectSystem
from .proximity_fade_system import ProximityFadeSystem

class AnimationSystem:
    def __init__(self, component_manager):
        self.component_manager = component_manager
    
    def update(self, fps, dt):
        for eid in self.component_manager.get_entities_with(AnimationStateMachine):
            animation_state_machine = self.component_manager.get(eid, AnimationStateMachine)

            if animation_state_machine.animation_component.entity_type == "chess_piece":
                vel = self.component_manager.get(eid, Velocity).vec
                is_moving = vel.x != 0 or vel.y != 0
                
                suggested_anim = "moving" if is_moving else "idle"

                animation_state_machine.set_animation(suggested_anim)
        
        for eid in self.component_manager.get_entities_with(AnimationComponent):
            animation_comp = self.component_manager.get(eid, AnimationComponent)

            animation_comp.update(fps, dt)

class RenderSystem:
    def __init__(self, event_manager, component_manager, entity_manager, surface_size=INITIAL_WINDOW_SIZE):
        self.component_manager = component_manager

        self.render_effect_system = RenderEffectSystem(event_manager, component_manager)
        self.particle_effect_system = ParticleEffectSystem(component_manager, entity_manager)
        self.proximity_fade_system = ProximityFadeSystem(component_manager)

        self.temp_surf = pygame.Surface(surface_size).convert_alpha()
        # Wind and atmosphere
        self.wind_system = WindSystem()
        self.atmosphere_overlay = None

    def update(self, dt):
        self.render_effect_system.update(dt)
        self.particle_effect_system.update(dt)
        self.proximity_fade_system.update()
        self.wind_system.update(dt)

        for eid in self.component_manager.get_entities_with(PulseComponent):
            pulse = self.component_manager.get(eid, PulseComponent)
            pulse.time += dt
    
    def render(self, surface, tilemap, camera):
        self.temp_surf.fill((0, 0, 0))

        scroll = camera.scroll
        temp_surf_offset = pygame.Vector2(0, 0)
        screen_rect = self.temp_surf.get_rect()

        # Queues
        normal_queue = []
        ysort_queue = []

        # 1. Render tilemap (background layers like grass, water, path)
        tilemap.render(self.temp_surf, camera)

        # 2. Render particle effects UNDERNEATH Y-sorted objects (for projectile trails and death bursts)
        from ...components.particle import Particle
        for eid in self.component_manager.get_entities_with(Particle, Position):
            particle = self.component_manager.get(eid, Particle)
            
            # Skip deactivated particles from the pool
            if math.isinf(particle.age) or particle.age >= particle.lifetime:
                continue

            pos = self.component_manager.get(eid, Position)

            size = particle.size
            if particle.shrink:
                size *= max(0.0, 1.0 - (particle.age / particle.lifetime))
            elif particle.oscillate_size:
                size *= (0.8 + 0.4 * abs(math.sin(particle.age * 15.0)))

            if size > 0:
                p_surf = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, particle.color, (int(size), int(size)), int(size))
                self.temp_surf.blit(p_surf, (pos.x - scroll.x - size, pos.y - scroll.y - size))

        # 3. Collect Y-sorted tiles (e.g. walls)
        ysort_queue.extend(tilemap.get_ysort_items(camera.rect))

        for eid in self.component_manager.get_entities_with(Position):
            pos = self.component_manager.get(eid, Position)
            world_pos = pygame.Vector2(pos.x, pos.y)
            screen_pos = world_pos - scroll

            # Components
            render = self.component_manager.get(eid, RenderComponent)
            anim = self.component_manager.get(eid, AnimationComponent)
            rec = self.component_manager.get(eid, RenderEffectComponent)
            ysort = self.component_manager.get(eid, YSortRender)
            shadow = self.component_manager.get(eid, ShadowComponent)
            wind_affected = self.component_manager.get(eid, WindAffectedComponent)
            pulse = self.component_manager.get(eid, PulseComponent)

            # Effects state
            scale = rec.scale if rec and not rec.disabled else None
            tint = rec.tint if rec and not rec.disabled else None
            alpha = rec.alpha if rec and not rec.disabled and rec.alpha else None
            rotation = rec.rotation if rec and not rec.disabled else 0.0

            # Determine sorting Y for entities
            entity_sort_y = world_pos.y + (ysort.offset[1] if ysort else 0)

            # Pulse render (underneath sprite, but relative to entity screen pos)
            if pulse:
                pulse_val = (math.sin(pulse.time * pulse.speed) + 1) / 2 # 0 to 1
                dynamic_radius = pulse.radius * (0.8 + 0.4 * pulse_val)
                pulse_surf = pygame.Surface((dynamic_radius * 2, dynamic_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(pulse_surf, (*pulse.color, pulse.alpha), (dynamic_radius, dynamic_radius), dynamic_radius)
                self.temp_surf.blit(pulse_surf, screen_pos - pygame.Vector2(dynamic_radius, dynamic_radius))

            # Shadow render (added to Y-sort queue)
            if shadow:
                shadow_pos = screen_pos + pygame.Vector2(shadow.offset)
                shadow_surf = shadow.surface
                if screen_rect.colliderect(pygame.Rect(shadow_pos, shadow_surf.get_size())):
                    # Stable sort keeps it behind the entity if added first
                    ysort_queue.append((entity_sort_y, "shadow", shadow_surf, shadow_pos, shadow.alpha))

            # Skip entities with no visible component
            if render is None and anim is None:
                continue

            # Sprite render preparation
            if render:
                surf = render.surface
                # wind sway for foliage
                if wind_affected and render.surface:
                    img_id = str(id(render.surface))
                    if not hasattr(self, 'wind_cache'): self.wind_cache = {}
                    if img_id not in self.wind_cache:
                        # Try to get focal points from config if it's a foliage image
                        focal_points = None
                        if "foliage.png" in render.image_file:
                            try:
                                # We need to know which tile index this is
                                # This is a bit tricky, let's assume we can get it or use img_id
                                # Prioritize custom user-defined config from the editor
                                custom_path = "data/config/foliage_wind_custom.json"
                                if os.path.exists(custom_path):
                                    with open(custom_path, "r") as f:
                                        self._foliage_config = json.load(f)
                                else:
                                    # Fallback to calculated config
                                    with open("data/config/foliage_wind.json", "r") as f:
                                        self._foliage_config = json.load(f)
                                
                                # Find index by matching surface to spritesheet images
                                if not hasattr(self, '_foliage_images'):
                                    from ...utils import load_images_from_spritesheet
                                    self._foliage_images = load_images_from_spritesheet("data/graphics/spritesheets/foliage.png")
                                
                                for idx, fimg in enumerate(self._foliage_images):
                                    if fimg.get_size() == render.surface.get_size():
                                        # Best effort: compare a few pixels? Or just use idx
                                        focal_points = self._foliage_config.get(str(idx))
                                        break
                            except Exception: pass

                        try: self.wind_cache[img_id] = self.wind_system.generate_sway_frames(render.surface, num_frames=24, amplitude=6, focal_points=focal_points)
                        except Exception: self.wind_cache[img_id] = None
                    
                    frames = self.wind_cache.get(img_id)
                    if frames:
                        # Render static base first to avoid gaps
                        draw_pos = screen_pos + render.offset
                        if screen_rect.colliderect(pygame.Rect(draw_pos, render.surface.get_size())):
                            if ysort:
                                ysort_queue.append((entity_sort_y, "sprite", render.surface, draw_pos, alpha, tint))
                            else:
                                normal_queue.append(("sprite", render.surface, draw_pos, alpha, tint))

                        # Then render the swaying overlay on top (higher sort_y or just after)
                        # Reduced playback speed to 10 FPS for a slower wiggle
                        sway_surf = frames[int((self.wind_system.time * 10) % len(frames))]
                        surf = sway_surf
                    else:
                        surf = render.surface
                else:
                    surf = render.surface

                offset = render.offset.copy()
                if rotation:
                    surf = pygame.transform.rotate(surf, rotation)
                if scale and (scale[0] != 1 or scale[1] != 1):
                    offset[0] *= scale[0]; offset[1] *= scale[1]
                    surf = pygame.transform.scale(surf, (int(surf.get_width() * scale[0]), int(surf.get_height() * scale[1])))

                draw_pos = screen_pos + offset
                if screen_rect.colliderect(pygame.Rect(draw_pos, surf.get_size())):
                    if ysort:
                        ysort_queue.append((entity_sort_y, "sprite", surf, draw_pos, alpha, tint))
                    else:
                        normal_queue.append(("sprite", surf, draw_pos, alpha, tint))

            # Animation render preparation
            if anim:
                anim_pos = screen_pos + anim.offset
                # Approximate size check
                if screen_rect.colliderect(pygame.Rect(anim_pos.x, anim_pos.y, 32, 32)):
                    if ysort:
                        ysort_queue.append((entity_sort_y, "animation", anim, anim_pos, scale, tint, alpha, rotation))
                    else:
                        normal_queue.append(("animation", anim, anim_pos, scale, tint, alpha, rotation))

        # Sort and draw ysort_queue
        ysort_queue.sort(key=lambda item: item[0])
        for item in ysort_queue:
            q_type = item[1]
            if q_type == "tile":
                _, _, surf, tile_pos = item
                self.temp_surf.blit(surf, (tile_pos[0] - scroll.x, tile_pos[1] - scroll.y))
            elif q_type == "shadow":
                _, _, surf, pos, alpha = item
                surf.set_alpha(alpha)
                self.temp_surf.blit(surf, pos)
            elif q_type == "sprite":
                _, _, surf, pos, alpha, tint = item
                if tint:
                    ts = pygame.Surface(surf.get_size(), pygame.SRCALPHA); ts.fill(tint)
                    surf = surf.copy(); surf.blit(ts, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                if alpha:
                    surf = surf.copy(); surf.set_alpha(alpha)
                self.temp_surf.blit(surf, pos)
            elif q_type == "animation":
                _, _, anim, pos, scale, tint, alpha, rotation = item
                anim.animation.render(self.temp_surf, pos, scale=scale, tint=tint, alpha=alpha, angle=rotation)

        # Draw non-ysorted (always on top)
        for item in normal_queue:
            q_type = item[0]
            if q_type == "sprite":
                _, surf, pos, alpha, tint = item
                self.temp_surf.blit(surf, pos)
            elif q_type == "animation":
                _, anim, pos, scale, tint, alpha, rotation = item
                anim.animation.render(self.temp_surf, pos, scale=scale, tint=tint, alpha=alpha, angle=rotation)

        # Apply camera zoom
        if camera.zoom != 1:
            self.temp_surf = pygame.transform.scale(
                self.temp_surf,
                (int(surface.get_width() * camera.zoom), int(surface.get_height() * camera.zoom))
            )
            temp_surf_offset = pygame.Vector2(surface.get_width() / 2, surface.get_height() / 2) - pygame.Vector2(
                self.temp_surf.get_size()
            ) / 2

        surface.blit(self.temp_surf, temp_surf_offset)
