from __future__ import annotations
import pygame
from typing import Optional
from .sound_config import SoundDefinition

class VoiceLimiter:
    """Limits simultaneous instances per sound_id. Drops oldest when over limit."""

    def __init__(self):
        self._active: dict[str, list[tuple[pygame.mixer.Channel, float]]] = {}

    def try_acquire(self, sd: SoundDefinition, channel: pygame.mixer.Channel, now: float) -> bool:
        if sd.max_instances <= 0:
            return True
        entries = self._active.setdefault(sd.sound_id, [])
        entries[:] = [(ch, t) for ch, t in entries if ch.get_busy()]

        if len(entries) >= sd.max_instances:
            oldest = entries.pop(0)
            oldest[0].stop()

        entries.append((channel, now))
        return True

    def release(self, sound_id: str, channel: pygame.mixer.Channel):
        entries = self._active.get(sound_id)
        if not entries:
            return
        entries[:] = [(ch, t) for ch, t in entries if ch is not channel]

    def reset(self):
        self._active.clear()
