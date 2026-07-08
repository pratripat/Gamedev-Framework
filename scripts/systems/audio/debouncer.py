from __future__ import annotations
import time
from .sound_config import SoundDefinition

class Debouncer:
    """Suppresses duplicate requests for the same sound_id within a cooldown window."""

    def __init__(self):
        self._last_played: dict[str, float] = {}

    def can_play(self, sd: SoundDefinition, now: float) -> bool:
        if sd.cooldown <= 0.0:
            return True
        last = self._last_played.get(sd.sound_id, -1e9)
        return (now - last) >= sd.cooldown

    def mark_played(self, sound_id: str, now: float):
        self._last_played[sound_id] = now

    def reset(self):
        self._last_played.clear()
