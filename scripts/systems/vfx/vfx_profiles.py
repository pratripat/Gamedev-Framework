"""Data-driven VFX profiles.

Each profile maps an effect name → params dict.  Profile names are
used by ``VFXManager.play(name, **context)``.

When ``VFXManager`` dispatches an effect it merges the profile params
with the runtime context (e.g. ``entity_id``, ``pos``).  Context keys
**override** profile defaults so gameplay callers can customise on the
fly::

    vfx.play('player_damage', entity_id=eid, intensity=5.0)

Profiles can eventually be moved to JSON files without changing any
gameplay code.  Schema:

    {
        "<effect_name>": {
            "<sub_effect>": {<param>: <value>, …},
            …
        }
    }

Available sub-effects and their default params are defined in
:class:`~scripts.systems.gamefeel.GameFeelManager`.
"""

VFX_PROFILES = {
    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------
    "dash": {
        "screen_shake": {"intensity": 1.5, "duration": 0.05},
        "slow_motion": {"duration": 0.1, "time_scale": 0.6},
    },

    "bomb": {
        "screen_shake": {"intensity": 8.0, "duration": 0.3},
        "screen_flash": {"duration": 0.15, "color": (255, 255, 255)},
        # "hit_stop": {"duration": 0.08},         # reserved for later
        # "slow_motion": {"duration": 0.25, "time_scale": 0.3},
    },

    # ------------------------------------------------------------------
    # Damage / hits — keep only what existed before (squash on hit)
    # ------------------------------------------------------------------
    "player_damage": {
        "squash": {"scale_x": 0.85, "scale_y": 1.15, "duration": 0.04},
    },
}
