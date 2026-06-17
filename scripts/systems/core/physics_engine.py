import pygame

from scripts.components.tags import EnemyTagComponent
from scripts.ecs.component_manager import ComponentManager
from ...components.physics import KnockbackComponent, Position, Velocity
from ...components.physics import CollisionComponent
from ...components.projectile import ProjectileComponent
from ...components.render_effect import RenderEffectComponent
from ...utils import Quadtree, INITIAL_WINDOW_SIZE, VIRTUAL_WINDOW_SIZE, GameSceneEvents, get_unit_direction_towards

class PhysicsEngine:
    def __init__(self, component_manager: ComponentManager, event_manager):
        self.component_manager = component_manager
        self.event_manager = event_manager
        self.player_dashing = False
        self.player_id = None

        self.event_manager.subscribe(GameSceneEvents.DAMAGE, self._knockback)
    
    def _knockback(self, entity_id, proj_id, **kwargs):
        if self.component_manager.get(entity_id, EnemyTagComponent):
            proj_vel = kwargs.get('proj_vel')
            if proj_vel and proj_vel.length_squared() > 0:
                proj_vel = proj_vel.normalize()
            else:
                proj_vel_comp = self.component_manager.get(proj_id, Velocity) if isinstance(proj_id, int) and proj_id in self.component_manager._components.get(Velocity, {}) else None
                if proj_vel_comp:
                    proj_vel = get_unit_direction_towards(pygame.Vector2(0, 0), proj_vel_comp.vec)
                else:
                    proj_pos_vec = kwargs.get('proj_pos')
                    if not proj_pos_vec:
                        proj_pos = self.component_manager.get(proj_id, Position) if isinstance(proj_id, int) and proj_id in self.component_manager._components.get(Position, {}) else None
                        proj_pos_vec = proj_pos.vec if proj_pos else None
                    target_pos = self.component_manager.get(entity_id, Position)
                    if proj_pos_vec and target_pos:
                        proj_vel = get_unit_direction_towards(proj_pos_vec, target_pos.vec)
                    else:
                        proj_vel = pygame.Vector2(0, 0)

            self.component_manager.add(entity_id, KnockbackComponent(proj_vel, 5, duration=0.2))

    def update(self, scroll, fps, dt, is_dashing=False, player_id=None, static_quadtree=None, dynamic_quadtree=None):
        self.player_dashing = is_dashing
        self.player_id = player_id
        scale = fps if (fps and fps > 0) else 60.0

        pos_dict = self.component_manager._components.get(Position, {})
        vel_dict = self.component_manager._components.get(Velocity, {})
        col_dict = self.component_manager._components.get(CollisionComponent, {})
        
        for entity in self.component_manager.get_entities_with(Position, Velocity):
            position = pos_dict.get(entity)
            velocity = vel_dict.get(entity)
            collision_component = col_dict.get(entity)
            if not collision_component:
                position += velocity.vec * dt * scale
                velocity.realistic_vel = velocity.vec.copy()

        for non_solid_component_entity in self.component_manager.get_entities_with(CollisionComponent):
            non_solid_component = col_dict.get(non_solid_component_entity)
            if non_solid_component.solid:
                continue
            if self.component_manager.get(non_solid_component_entity, ProjectileComponent):
                continue

            pos = pos_dict.get(non_solid_component_entity)
            vel = vel_dict.get(non_solid_component_entity)
            if not pos or not vel: continue

            rect = pygame.FRect(*(pos.vec + non_solid_component.offset), *non_solid_component.size)

            kvx, kvy = 0, 0
            kbc = self.component_manager.get(non_solid_component_entity, KnockbackComponent)
            if kbc:
                kvx, kvy = kbc.update(dt, self.component_manager, non_solid_component_entity)

            vel.realistic_vel = vel.vec.copy()

            # 1. Horizontal Movement & Collision
            total_dx = (vel.x + kvx) * dt * scale
            rect.x += total_dx

            rec = self.component_manager.get(non_solid_component_entity, RenderEffectComponent)
            in_air = rec and rec.z_offset > 5.0

            collisions = None
            if not in_air:
                colliding_entities = []
                if static_quadtree: static_quadtree.retrieve(colliding_entities, rect)
                if dynamic_quadtree: dynamic_quadtree.retrieve(colliding_entities, rect)
                
                seen_h = set()
                for entity, colliding_rect in colliding_entities:
                    collision_id = (entity, tuple(colliding_rect))
                    if collision_id in seen_h or entity == non_solid_component_entity: continue
                    seen_h.add(collision_id)
                    
                    layer_id = entity[0] if isinstance(entity, tuple) else entity
                    is_water = (layer_id == "water")
                    is_solid = (layer_id == "wall")
                    if entity is not None and not (is_water or is_solid):
                        comp = col_dict.get(entity)
                        if comp: is_solid = comp.solid

                    # Water logic: solid unless dashing
                    if is_water:
                        if self.player_dashing and non_solid_component_entity == self.player_id:
                            is_solid = False
                        else:
                            is_solid = True

                    if is_solid and rect.colliderect(colliding_rect):
                        if collisions is None: collisions = {"top": False, "right": False, "bottom": False, "left": False}
                        if total_dx > 0:
                            rect.right = colliding_rect.left
                            collisions["right"] = True
                            if kbc: kbc.vx = 0
                        elif total_dx < 0:
                            rect.left = colliding_rect.right
                            collisions["left"] = True
                            if kbc: kbc.vx = 0
                        vel.realistic_vel.x = 0

            # 2. Vertical Movement & Collision
            total_dy = (vel.y + kvy) * dt * scale
            rect.y += total_dy

            if not in_air:
                colliding_entities = []
                if static_quadtree: static_quadtree.retrieve(colliding_entities, rect)
                if dynamic_quadtree: dynamic_quadtree.retrieve(colliding_entities, rect)
                
                seen_v = set()
                for entity, colliding_rect in colliding_entities:
                    collision_id = (entity, tuple(colliding_rect))
                    if collision_id in seen_v or entity == non_solid_component_entity: continue
                    seen_v.add(collision_id)
                    
                    layer_id = entity[0] if isinstance(entity, tuple) else entity
                    is_water = (layer_id == "water")
                    is_solid = (layer_id == "wall")
                    if entity is not None and not (is_water or is_solid):
                        comp = col_dict.get(entity)
                        if comp: is_solid = comp.solid
                    
                    if is_water:
                        if self.player_dashing and non_solid_component_entity == self.player_id:
                            is_solid = False
                        else:
                            is_solid = True

                    if is_solid and rect.colliderect(colliding_rect):
                        if collisions is None: collisions = {"top": False, "right": False, "bottom": False, "left": False}
                        if total_dy > 0:
                            rect.bottom = colliding_rect.top
                            collisions["bottom"] = True
                            if kbc: kbc.vy = 0
                        elif total_dy < 0:
                            rect.top = colliding_rect.bottom
                            collisions["top"] = True
                            if kbc: kbc.vy = 0
                        vel.realistic_vel.y = 0

            if collisions is not None:
                self.event_manager.emit(GameSceneEvents.COLLISION, entity_id=non_solid_component_entity, collisions=collisions)

            # Particles WALK event
            if vel.vec.length_squared() > 0.1:
                if not hasattr(self, '_walk_timers'): self._walk_timers = {}
                self._walk_timers[non_solid_component_entity] = self._walk_timers.get(non_solid_component_entity, 0) + dt
                if self._walk_timers[non_solid_component_entity] > 0.15:
                    self._walk_timers[non_solid_component_entity] = 0
                    self.event_manager.emit(GameSceneEvents.WALK, pos=pos.vec, vel=vel.vec, entity_id=non_solid_component_entity)

            pos.vec.update(pygame.Vector2(rect.topleft) - non_solid_component.offset)
