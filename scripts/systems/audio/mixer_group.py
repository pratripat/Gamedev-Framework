from __future__ import annotations

GROUP_NAMES = ["master", "music", "sfx", "ui", "ambient", "player", "enemy", "boss"]


class MixerGroup:
    """Volume group with independent volume level. Applies as a multiplier on playback."""

    def __init__(self, name: str, volume: float = 1.0):
        self.name = name
        self._volume = volume

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = max(0.0, min(2.0, value))


class MixerGroupManager:
    """Manages all volume groups and computes effective volume for a group."""

    def __init__(self):
        self.groups: dict[str, MixerGroup] = {}
        for name in GROUP_NAMES:
            self.groups[name] = MixerGroup(name, 1.0)

    def get(self, name: str) -> MixerGroup:
        return self.groups.get(name, self.groups["sfx"])

    def set_volume(self, name: str, value: float):
        grp = self.get(name)
        grp.volume = value

    def effective_volume(self, group_name: str) -> float:
        grp = self.get(group_name)
        return self.groups["master"].volume * grp.volume
