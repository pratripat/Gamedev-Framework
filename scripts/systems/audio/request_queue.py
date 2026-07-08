from __future__ import annotations
import random
from typing import Optional
from .sound_config import SoundDefinition, SoundConfig

class AudioRequest:
    """Represents a request to play a sound. Created by event handlers, consumed once per frame."""

    __slots__ = ("sound_id", "group", "priority", "source_entity", "x", "y", "force")

    def __init__(self, sound_id: str, group: str = "sfx", priority: int = 128,
                 source_entity: Optional[int] = None, x: float = 0.0, y: float = 0.0,
                 force: bool = False):
        self.sound_id = sound_id
        self.group = group
        self.priority = priority
        self.source_entity = source_entity
        self.x = x
        self.y = y
        self.force = force


class RequestQueue:
    """
    Thread-safe(ish) queue of audio requests processed once per frame.
    Filters duplicates, applies debounce, voice limits, then dispatches to ChannelPool.
    """

    def __init__(self, config: SoundConfig):
        self._config = config
        self._queue: list[AudioRequest] = []

    def enqueue(self, req: AudioRequest):
        self._queue.append(req)

    def drain(self) -> list[AudioRequest]:
        items = list(self._queue)
        self._queue.clear()
        return items

    def deduplicate(self, requests: list[AudioRequest]) -> list[AudioRequest]:
        if len(requests) < 2:
            return requests
        seen: set[str] = set()
        result = []
        for req in reversed(requests):
            key = req.sound_id
            if key in seen:
                continue
            seen.add(key)
            result.append(req)
        result.reverse()
        return result

    @property
    def pending(self) -> int:
        return len(self._queue)
