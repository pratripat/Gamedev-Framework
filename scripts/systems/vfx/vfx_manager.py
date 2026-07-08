"""High-level VFX orchestrator.

Gameplay code triggers named effects through this class which reads
profile data and delegates to the appropriate lower-level systems
(:class:`~scripts.systems.gamefeel.GameFeelManager` for juice effects,
:class:`~scripts.scenes.particle_event_coordinator.ParticleEventCoordinator`
for particles).
"""

from .vfx_profiles import VFX_PROFILES


class VFXManager:
    """Plays named visual-effect profiles.

    Args:
        gamefeel: ``GameFeelManager`` instance.
        particle_coordinator: Optional ``ParticleEventCoordinator``.
    """

    def __init__(self, gamefeel, particle_coordinator=None):
        self.gamefeel = gamefeel
        self.particle_coordinator = particle_coordinator
        self._profiles = dict(VFX_PROFILES)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def play(self, name: str, **context):
        """Execute a named VFX profile.

        Args:
            name: Profile name (key in :data:`VFX_PROFILES`).
            **context: Runtime data (``entity_id``, ``pos``, etc.)
                       merged into each sub-effect's params.
        """
        profile = self._profiles.get(name)
        if profile is None:
            return

        for effect_name, params in profile.items():
            merged = {**params, **context}
            self.gamefeel.play(effect_name, **merged)

    def reload_profiles(self, profiles: dict = None):
        """Replace the current profiles dict (useful for hot-reloading)."""
        self._profiles = dict(profiles) if profiles else dict(VFX_PROFILES)

    def stats(self) -> dict:
        return {"loaded_profiles": list(self._profiles)}
