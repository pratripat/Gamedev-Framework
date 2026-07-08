from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Optional
from ...utils.json_validator import load_and_validate
from ...utils.json_schemas import SOUND_SCHEMA

@dataclass
class SoundVariation:
    file: str
    weight: float = 1.0

@dataclass
class SoundDefinition:
    sound_id: str
    variations: list[SoundVariation] = field(default_factory=list)
    volume: float = 1.0
    cooldown: float = 0.0
    max_instances: int = 0
    priority: int = 128
    group: str = "sfx"
    volume_variation: float = 0.0
    pitch_variation: float = 0.0
    max_distance: float = 0.0

class SoundConfig:
    def __init__(self, path: str = "data/config/sounds.json"):
        self._defs: dict[str, SoundDefinition] = {}
        self.load(path)

    def load(self, path: str):
        raw = load_and_validate(path, SOUND_SCHEMA)
        for sid, entry in raw.items():
            vars_list = []
            for v in entry.get("variations", []):
                vars_list.append(SoundVariation(**v))
            self._defs[sid] = SoundDefinition(
                sound_id=sid,
                variations=vars_list,
                volume=entry.get("volume", 1.0),
                cooldown=entry.get("cooldown", 0.0),
                max_instances=entry.get("max_instances", 0),
                priority=entry.get("priority", 128),
                group=entry.get("group", "sfx"),
                volume_variation=entry.get("volume_variation", 0.0),
                pitch_variation=entry.get("pitch_variation", 0.0),
                max_distance=entry.get("max_distance", 0.0),
            )

    def get(self, sound_id: str) -> Optional[SoundDefinition]:
        return self._defs.get(sound_id)

    @property
    def sound_ids(self):
        return list(self._defs.keys())
