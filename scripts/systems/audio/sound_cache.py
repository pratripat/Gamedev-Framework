from __future__ import annotations
import pygame
import os
import warnings
from typing import Optional
from .sound_config import SoundConfig, SoundDefinition

class SoundCache:
    """Preloads all Sound objects at init. Never creates Sound objects during gameplay."""

    def __init__(self, config: SoundConfig, base_path: str = "data/audio"):
        self._base = base_path
        self._sounds: dict[str, list[pygame.mixer.Sound]] = {}
        self._single_sounds: dict[str, pygame.mixer.Sound] = {}
        self._load_all(config)

    def _load_all(self, config: SoundConfig):
        for sid in config.sound_ids:
            sd = config.get(sid)
            if sd is None:
                continue
            if not sd.variations:
                continue
            loaded = []
            for var in sd.variations:
                full = os.path.join(self._base, var.file)
                if not os.path.isfile(full):
                    warnings.warn(f"Sound file not found: {full}")
                    continue
                snd = pygame.mixer.Sound(full)
                snd.set_volume(sd.volume)
                loaded.append(snd)
            if len(loaded) == 1:
                self._single_sounds[sid] = loaded[0]
            elif loaded:
                self._sounds[sid] = loaded

    def get_sound(self, sound_id: str, variation_index: int = -1) -> Optional[pygame.mixer.Sound]:
        if sound_id in self._single_sounds:
            return self._single_sounds[sound_id]
        variants = self._sounds.get(sound_id)
        if not variants:
            return None
        if variation_index < 0 or variation_index >= len(variants):
            return variants[0]
        return variants[variation_index]

    def get_variation_list(self, sound_id: str):
        if sound_id in self._single_sounds:
            return [self._single_sounds[sound_id]]
        return self._sounds.get(sound_id, [])

    @property
    def loaded_count(self) -> int:
        return len(self._single_sounds) + sum(len(v) for v in self._sounds.values())
