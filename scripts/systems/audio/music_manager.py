from __future__ import annotations
import pygame
import os
import random
from typing import Optional

_FADE_NONE = 0
_FADE_IN = 1
_FADE_OUT = 2
_CROSSFADE = 3


class Track:
    def __init__(self, filepath: str, volume: float = 1.0):
        self.filepath = filepath
        self.volume = volume
        self.name = os.path.splitext(os.path.basename(filepath))[0]


class MusicManager:
    """
    Manages background music independently of game FPS using pygame.mixer.music.
    Supports play, stop, fade in/out, crossfade, and playlist rotation.
    """

    def __init__(self):
        self._tracks: list[Track] = []
        self._index: int = -1
        self._shuffle: bool = False
        self._volume: float = 1.0
        self._state: int = _FADE_NONE
        self._fade_start: float = 0.0
        self._fade_duration: float = 0.0
        self._fade_from_vol: float = 0.0
        self._crossfade_next: Optional[Track] = None
        self._paused: bool = False
        self._loop: bool = True

    def load_playlist(self, directory: str, extensions=(".ogg", ".mp3", ".wav")):
        files = []
        for f in sorted(os.listdir(directory)):
            if any(f.lower().endswith(ext) for ext in extensions):
                files.append(os.path.join(directory, f))
        if not files:
            return
        self._tracks = [Track(f) for f in files]
        self._index = -1

    def set_volume(self, volume: float):
        self._volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self._volume)

    def load_and_play(self, filepath: str, fade_ms: int = 0):
        """Load and immediately play a single track by filepath."""
        if not os.path.isfile(filepath):
            return
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.set_volume(self._volume)
        pygame.mixer.music.play(0, fade_ms=fade_ms)

    def play(self, index: int = -1, fade_ms: int = 0):
        if not self._tracks:
            return
        if index < 0 or index >= len(self._tracks):
            index = 0
        self._index = index
        track = self._tracks[self._index]
        pygame.mixer.music.load(track.filepath)
        pygame.mixer.music.set_volume(self._volume * track.volume)
        pygame.mixer.music.play(0, fade_ms=fade_ms)

    def stop(self, fade_ms: int = 0):
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()

    def pause(self):
        pygame.mixer.music.pause()
        self._paused = True

    def resume(self):
        pygame.mixer.music.unpause()
        self._paused = False

    def next(self, fade_ms: int = 500):
        if not self._tracks:
            return
        if self._shuffle:
            nxt = random.randint(0, len(self._tracks) - 1)
            while nxt == self._index and len(self._tracks) > 1:
                nxt = random.randint(0, len(self._tracks) - 1)
        else:
            nxt = (self._index + 1) % len(self._tracks)
        self.play(nxt, fade_ms)

    def crossfade(self, index: int, duration_ms: int = 2000):
        if not self._tracks or index < 0 or index >= len(self._tracks):
            return
        self._state = _CROSSFADE
        self._fade_duration = duration_ms / 1000.0
        self._fade_start = pygame.time.get_ticks() / 1000.0
        self._fade_from_vol = self._volume
        self._crossfade_next = self._tracks[index]
        # Start the next track at zero volume
        pygame.mixer.music.queue(self._crossfade_next.filepath)

    def update(self):
        if self._state == _FADE_NONE:
            # Auto-advance if track ended
            if not pygame.mixer.music.get_busy() and self._loop and not self._paused:
                self.next()
            return

        now = pygame.time.get_ticks() / 1000.0
        elapsed = now - self._fade_start
        progress = min(elapsed / self._fade_duration, 1.0)

        if self._state == _FADE_OUT:
            vol = self._volume * (1.0 - progress)
            pygame.mixer.music.set_volume(max(0.0, vol))
            if progress >= 1.0:
                pygame.mixer.music.stop()
                self._state = _FADE_NONE

        elif self._state == _FADE_IN:
            vol = self._volume * progress
            pygame.mixer.music.set_volume(max(0.0, vol))
            if progress >= 1.0:
                self._state = _FADE_NONE

        elif self._state == _CROSSFADE:
            out_vol = self._volume * (1.0 - progress)
            in_vol = self._volume * progress
            pygame.mixer.music.set_volume(max(0.0, out_vol))
            if progress >= 1.0:
                pygame.mixer.music.stop()
                if self._crossfade_next:
                    self._index = self._tracks.index(self._crossfade_next)
                    pygame.mixer.music.load(self._crossfade_next.filepath)
                    pygame.mixer.music.set_volume(self._volume)
                    pygame.mixer.music.play(0)
                    self._crossfade_next = None
                self._state = _FADE_NONE

    @property
    def is_playing(self) -> bool:
        return pygame.mixer.music.get_busy()

    @property
    def current_track(self) -> Optional[str]:
        if 0 <= self._index < len(self._tracks):
            return self._tracks[self._index].name
        return None

    @property
    def shuffle(self) -> bool:
        return self._shuffle

    @shuffle.setter
    def shuffle(self, value: bool):
        self._shuffle = value
