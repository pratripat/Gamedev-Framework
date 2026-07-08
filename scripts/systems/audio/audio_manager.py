from __future__ import annotations
import pygame
import random
import time
from typing import Optional

from .sound_config import SoundConfig, SoundDefinition
from .sound_cache import SoundCache
from .channel_pool import ChannelPool
from .voice_limiter import VoiceLimiter
from .debouncer import Debouncer
from .mixer_group import MixerGroupManager
from .request_queue import RequestQueue, AudioRequest
from .music_manager import MusicManager


class AudioManager:
    """
    Central audio facade. Event-driven interface: external systems call play() or
    emit events that AudioManager subscribes to. Processes all requests once per frame
    in flush().
    """

    def __init__(self, config_path: str = "data/config/sounds.json",
                 audio_base: str = "data/audio",
                 channel_count: int = 32):
        pygame.mixer.init()

        self.config = SoundConfig(config_path)
        self.cache = SoundCache(self.config, audio_base)
        self.pool = ChannelPool(channel_count)
        self.limiter = VoiceLimiter()
        self.debouncer = Debouncer()
        self.groups = MixerGroupManager()
        self.queue = RequestQueue(self.config)
        self.music = MusicManager()

        # pygame.mixer.music has its own dedicated channel — no reservation needed

        # Stats
        self._requests_this_frame = 0
        self._played_this_frame = 0
        self._dropped_this_frame = 0
        self._total_played = 0

    # ---------- Public API ----------

    def play(self, sound_id: str, group: Optional[str] = None,
             priority: Optional[int] = None, source_entity: Optional[int] = None,
             x: float = 0.0, y: float = 0.0, force: bool = False):
        """Enqueue a sound request. Safe to call from any system."""
        sd = self.config.get(sound_id)
        if sd is None:
            return
        self.queue.enqueue(AudioRequest(
            sound_id=sound_id,
            group=group or sd.group,
            priority=priority if priority is not None else sd.priority,
            source_entity=source_entity, x=x, y=y, force=force,
        ))

    def play_music(self, filepath: str, fade_ms: int = 0):
        self.music.load_and_play(filepath, fade_ms)

    def play_music_by_index(self, index: int, fade_ms: int = 0):
        self.music.play(index, fade_ms)

    def crossfade_music(self, index: int, duration_ms: int = 2000):
        self.music.crossfade(index, duration_ms)

    def stop_music(self, fade_ms: int = 0):
        self.music.stop(fade_ms)

    def set_group_volume(self, group: str, volume: float):
        self.groups.set_volume(group, volume)

    def set_master_volume(self, volume: float):
        self.groups.set_volume("master", volume)

    def update_music(self):
        self.music.update()

    # ---------- Per-frame processing ----------

    def flush(self, now: Optional[float] = None):
        """
        Process all queued requests. Must be called once per frame after all
        systems have submitted their audio requests.
        """
        if now is None:
            now = time.time()
        requests = self.queue.drain()
        self._requests_this_frame = len(requests)

        # Deduplicate: keep only the last request per sound_id
        requests = self.queue.deduplicate(requests)

        played = 0
        dropped = 0

        for req in requests:
            sd = self.config.get(req.sound_id)
            if sd is None:
                continue

            # 1. Debounce
            if not req.force and not self.debouncer.can_play(sd, now):
                dropped += 1
                continue

            # 2. Find channel (priority + group stored internally by ChannelPool)
            effective_prio = req.priority if req.force else sd.priority
            channel = self.pool.acquire(effective_prio, req.group)
            if channel is None:
                dropped += 1
                continue

            # 3. Voice limit
            if not self.limiter.try_acquire(sd, channel, now):
                dropped += 1
                continue

            # 4. Select variation
            variations = self.cache.get_variation_list(req.sound_id)
            if not variations:
                dropped += 1
                continue
            if len(variations) == 1:
                snd = variations[0]
            else:
                weights = [v.weight for v in sd.variations] if sd.variations else None
                snd = random.choices(variations, weights=weights, k=1)[0] if weights else random.choice(variations)

            # 5. Compute effective volume
            group_vol = self.groups.effective_volume(req.group)
            vol = sd.volume * group_vol
            if sd.volume_variation > 0:
                vol *= 1.0 + random.uniform(-sd.volume_variation, sd.volume_variation)
            vol = max(0.0, min(1.0, vol))

            # 6. Play (ChannelPool stores alloc metadata — no dynamic attrs on Channel)
            snd.set_volume(vol)
            channel.play(snd)

            self.debouncer.mark_played(sd.sound_id, now)
            played += 1
            self._total_played += 1

        self._played_this_frame = played
        self._dropped_this_frame = dropped

        # Update music
        self.update_music()

    # ---------- Stats ----------

    @property
    def stats(self) -> dict:
        return {
            "requests": self._requests_this_frame,
            "played": self._played_this_frame,
            "dropped": self._dropped_this_frame,
            "total_played": self._total_played,
            "active_channels": self.pool.active_count,
            "pending": self.queue.pending,
            "cached_sounds": self.cache.loaded_count,
        }

    def print_stats(self):
        s = self.stats
        print(f"[AUDIO] req={s['requests']} played={s['played']} dropped={s['dropped']} "
              f"active_ch={s['active_channels']} pending={s['pending']} cached={s['cached_sounds']}")

    # ---------- Cleanup ----------

    def shutdown(self):
        self.pool.stop_all()
        self.music.stop()
        self.limiter.reset()
        self.debouncer.reset()
