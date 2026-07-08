from __future__ import annotations
import pygame
from typing import Optional


class _AllocInfo:
    __slots__ = ('priority', 'group')
    def __init__(self, priority: int = 128, group: str = 'sfx'):
        self.priority = priority
        self.group = group


class ChannelPool:
    """Fixed pool of mixer channels with priority-based allocation.

    Allocation metadata (priority, group) is stored internally rather than as
    dynamic attrs on pygame.mixer.Channel (C extension — no arbitrary attrs).
    """

    def __init__(self, channel_count: int = 32):
        pygame.mixer.set_num_channels(channel_count)
        self._count = channel_count
        self._channels = [pygame.mixer.Channel(i) for i in range(channel_count)]
        self._alloc: list[_AllocInfo] = [_AllocInfo() for _ in range(channel_count)]
        self._reserved: set[int] = set()

    def reserve(self, count: int) -> list[int]:
        """Reserve channels for a specific group (e.g. music). Returns their indices."""
        reserved = []
        for i in range(min(count, self._count)):
            if i not in self._reserved:
                self._reserved.add(i)
                reserved.append(i)
        return reserved

    def release(self, *indices: int):
        for idx in indices:
            self._reserved.discard(idx)

    def acquire(self, priority: int, group: str = 'sfx') -> Optional[pygame.mixer.Channel]:
        """Find the best available channel for a sound of given priority and group."""
        best_idx = -1
        best_playing_prio = 9999

        for i in range(self._count):
            if i in self._reserved:
                continue
            ch = self._channels[i]
            if not ch.get_busy():
                self._alloc[i].priority = priority
                self._alloc[i].group = group
                return ch
            current = self._alloc[i].priority
            if current < best_playing_prio:
                best_playing_prio = current
                best_idx = i

        if best_idx >= 0 and priority > best_playing_prio:
            ch = self._channels[best_idx]
            ch.stop()
            self._alloc[best_idx].priority = priority
            self._alloc[best_idx].group = group
            return ch

        return None

    def get_channel(self, index: int) -> Optional[pygame.mixer.Channel]:
        if 0 <= index < self._count:
            return self._channels[index]
        return None

    @property
    def alloc_info(self) -> list[_AllocInfo]:
        return self._alloc

    def stop_all(self):
        for ch in self._channels:
            ch.stop()

    def stop_group(self, group: str):
        for i in range(self._count):
            if self._alloc[i].group == group:
                self._channels[i].stop()

    @property
    def active_count(self) -> int:
        return sum(1 for ch in self._channels if ch.get_busy())

    @property
    def available_count(self) -> int:
        return self._count - len(self._reserved) - self.active_count
