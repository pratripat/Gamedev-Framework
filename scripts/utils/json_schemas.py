"""Pre-defined schemas for all game-configuration JSON files.

All schemas use `required=False` for entries that may or may not be
present in a given file.  Only structurally critical fields (like
``layers`` in level JSON) are required.
"""

from .json_validator import Schema as S

# ---------------------------------------------------------------------------
# Entity definitions  (data/config/entities.json)
# ---------------------------------------------------------------------------

ENTITY_NAMES = [
    "player", "enemy_pawn", "enemy_knight", "enemy_bishop", "enemy_rook",
    "collision_box", "destructible", "foliage",
]

ENTITY_TYPES = ["chess_piece"]
AI_BEHAVIORS = ["chase", "aggressive", "kiting", "sniper"]
SHOOT_FUNCTIONS = [
    "shoot_single", "shoot_radial", "shoot_aimed_burst", "shoot_knight_l",
    "shoot_cross", "shoot_spinning_ring", "shoot_wall", "shoot_spread",
]
ATTACK_TIERS = ["light", "heavy", "signature"]
ANIMATION_STATES = ["idle", "idleflipped", "moving", "movingflipped",
                    "shoot", "shootflipped", "damage", "damageflipped", "death"]
PROXIMITY_TARGETS = ["player", "enemy"]


# -- Component-level schemas (all optional — entities only include relevant ones) --

COMPONENT_SCHEMAS = {
    "Position": S.field(type=dict, required=False, schema={
        "x": S.number(), "y": S.number(),
    }),
    "Velocity": S.field(type=dict, required=False, schema={
        "x": S.number(), "y": S.number(), "speed": S.number(),
    }),
    "AnimationComponent": S.field(type=dict, required=False, schema={
        "entity": S.string(), "animation_id": S.string(),
        "center": S.boolean(), "entity_type": S.enum(ENTITY_TYPES),
    }),
    "RenderComponent": S.field(type=dict, required=False, schema={
        "image_file": S.string(), "offset_x": S.number(),
        "offset_y": S.number(),
        "center": S.field(type=bool, required=False, default=False),
    }),
    "CollisionComponent": S.field(type=dict, required=False, schema={
        "offset_x": S.number(), "offset_y": S.number(),
        "width": S.number(), "height": S.number(),
        "solid": S.boolean(),
        "center": S.field(type=bool, required=False, default=True),
        "blocks_projectiles": S.field(type=bool, required=False, default=True),
    }),
    "HurtBoxComponent": S.field(type=dict, required=False, schema={
        "offset_x": S.number(), "offset_y": S.number(),
        "width": S.number(), "height": S.number(), "center": S.boolean(),
    }),
    "HealthComponent": S.field(type=dict, required=False, schema={
        "max_health": S.integer(),
    }),
    "AIComponent": S.field(type=dict, required=False, schema={
        "behavior": S.enum(AI_BEHAVIORS),
    }),
    "WeaponComponent": S.field(type=dict, required=False, schema={
        "cooldown": S.number(), "shoot_fn": S.enum(SHOOT_FUNCTIONS),
        "projectile_data": S.field(type=dict, required=False),
    }),
    "AttackPatternComponent": S.field(type=dict, required=False, schema={
        "patterns": S.array({
            "cooldown": S.number(),
            "shoot_fn": S.enum(SHOOT_FUNCTIONS),
            "projectile_data": S.dict({
                "damage": S.number(), "speed": S.number(),
                "range": S.number(),
                "range_min": S.field(type=(int, float), required=False),
                "size": S.number(), "image_file": S.string(),
                "projectile_color": S.field(required=False),
                "effects": S.field(type=list, required=False),
                "pulse_speed": S.field(type=(int, float), required=False),
                "bounce": S.field(type=int, required=False, default=0),
                "penetration": S.field(type=int, required=False, default=0),
                "number": S.field(type=int, required=False, default=1),
                "towards_player": S.field(type=bool, required=False, default=False),
                "angle": S.field(type=(int, float), required=False, default=0),
                "spread": S.field(type=(int, float), required=False),
                "spacing": S.field(type=(int, float), required=False),
                "spin_speed": S.field(type=(int, float), required=False),
                "ring_radius": S.field(type=int, required=False, default=0),
                "dash_speed": S.field(type=(int, float), required=False),
                "modifiers": S.field(type=dict, required=False),
            }),
            "duration": S.number(),
            "warmup": S.field(type=(int, float), required=False),
            "tier": S.field(type=str, required=False, enum=ATTACK_TIERS),
            "tier_cooldown": S.field(type=(int, float), required=False, default=0),
        }),
        "loop": S.field(type=bool, required=False),
    }),
    "AnimationStateMachine": S.field(type=dict, required=False, schema={
        "animation_priority_list": S.field(type=list, required=False),
        "transitions": S.field(type=dict, required=False),
    }),
    "YSortComponent": S.field(type=dict, required=False),
    "ShadowComponent": S.field(type=dict, required=False),
    "ProximityFadeComponent": S.field(type=dict, required=False, schema={
        "targets": S.field(type=list, required=False),
        "min_dist": S.number(), "max_dist": S.number(),
        "alpha_range": S.field(type=list, required=False),
    }),
    "WindAffectedComponent": S.field(type=dict, required=False),
    "DestructibleComponent": S.field(type=dict, required=False, schema={
        "width": S.number(), "height": S.number(),
    }),
    "PlayerTagComponent": S.field(type=dict, required=False),
    "EnemyTagComponent": S.field(type=dict, required=False),
}

ENTITY_SCHEMA = {
    name: S.field(type=dict, required=False,
                  schema=COMPONENT_SCHEMAS)
    for name in ENTITY_NAMES
}

# ---------------------------------------------------------------------------
# Animation config  (data/graphics/animations/config.json)
# ---------------------------------------------------------------------------

ANIMATION_ENTRY_SCHEMA = {
    'frames':   S.field(type=list, required=True),
    'loop':     S.field(type=(bool, list), required=False, default=False),
    'speed':    S.field(type=(int, float), required=False, default=1),
    'scale':    S.field(type=(int, float), required=False, default=1),
    'centered': S.field(type=bool, required=False, default=False),
    'flip':     S.field(type=bool, required=False, default=False),
    'offset':   S.field(type=list, required=False, default=[0, 0]),
    'frame_events': S.field(type=list, required=False, item_schema={
        'frame': S.number(), 'event': S.string(),
    }),
}

# ---------------------------------------------------------------------------
# Level schema  (data/levels/*.json)
# ---------------------------------------------------------------------------

LAYER_NAMES = ["grass", "wall", "water", "player", "enemies",
               "foliage", "destructibles", "path"]

LEVEL_SCHEMA = {
    'layers': S.field(type=dict, schema={
        name: S.field(required=False) for name in LAYER_NAMES
    }),
    'tilemaps': S.dict({
        name: S.field(type=str, required=False) for name in LAYER_NAMES
    }),
}

# ---------------------------------------------------------------------------
# Sound config  (data/config/sounds.json)
# ---------------------------------------------------------------------------

SOUND_GROUPS = ["player", "enemy", "sfx", "ui", "boss", "ambient"]

SOUND_ENTRY_SCHEMA = {
    'variations':        S.field(type=list, required=False, default=[],
                                  item_schema={'file': S.string(), 'weight': S.number()}),
    'volume':            S.field(type=(int, float), required=False, default=1.0),
    'cooldown':          S.field(type=(int, float), required=False, default=0.0),
    'max_instances':     S.field(type=int, required=False, default=0),
    'priority':          S.field(type=int, required=False, default=128),
    'group':             S.field(type=str, required=False, default="sfx",
                                  enum=SOUND_GROUPS),
    'volume_variation':  S.field(type=(int, float), required=False, default=0.0),
    'pitch_variation':   S.field(type=(int, float), required=False, default=0.0),
    'max_distance':      S.field(type=(int, float), required=False, default=0.0),
}

SOUND_IDS = [
    "player_shoot", "enemy_shoot", "player_hit", "enemy_hit",
    "explosion", "dash", "ui_click", "boss_warn", "water_splash",
]

SOUND_SCHEMA = {
    sid: S.field(type=dict, required=False, default={},
                 schema=SOUND_ENTRY_SCHEMA)
    for sid in SOUND_IDS
}
