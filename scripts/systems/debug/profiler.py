from __future__ import annotations
import time


class Profiler:
    """Lightweight per-frame profiler tracking execution time per tagged system.

    Usage:
        profiler.begin('physics')
        self.physics_engine.update(...)
        profiler.end('physics')
    """

    TAGS = [
        'physics', 'rendering', 'animation', 'particles', 'audio',
        'ai', 'gamefeel', 'vfx', 'combat',
    ]

    def __init__(self, history: int = 60):
        self.history = history
        self._frame_records: dict[str, list[float]] = {}
        self._current: dict[str, float] = {}
        for tag in self.TAGS:
            self._frame_records[tag] = []
        self._paused = False

    def begin_frame(self):
        self._current.clear()
        self._frame_start = time.perf_counter()

    def begin(self, tag: str):
        if self._paused:
            return
        self._current[tag] = time.perf_counter()

    def end(self, tag: str):
        if self._paused or tag not in self._current:
            return
        elapsed = (time.perf_counter() - self._current.pop(tag)) * 1000.0
        records = self._frame_records.get(tag)
        if records is not None:
            records.append(elapsed)
            if len(records) > self.history:
                records.pop(0)

    @property
    def frame_time_ms(self) -> float:
        if not hasattr(self, '_frame_start') or self._frame_start is None:
            return 0.0
        return (time.perf_counter() - self._frame_start) * 1000.0

    @property
    def stats(self) -> dict[str, dict]:
        result = {}
        for tag, records in self._frame_records.items():
            if not records:
                result[tag] = {'avg_ms': 0.0, 'last_ms': 0.0, 'max_ms': 0.0}
                continue
            result[tag] = {
                'avg_ms': sum(records) / len(records),
                'last_ms': records[-1],
                'max_ms': max(records),
            }
        return result

    @property
    def active(self) -> bool:
        return bool(self._current)

    def pause(self):
        self._paused = True
        self._current.clear()

    def resume(self):
        self._paused = False

    def reset(self):
        self._current.clear()
        for tag in self.TAGS:
            self._frame_records[tag] = []
