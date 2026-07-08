"""
Generic Object Pool

Reusable pool with pre-allocation, free-list tracking, auto-growth,
and usage statistics.

The pool manages only storage and free-list allocation. Systems that use
the pool manage their own active-indices list (needed for write-pointer
compaction during iteration). This keeps the pool flexible and avoids
imposing a specific iteration strategy.

Usage:
    pool = ObjectPool(FastProjectile, capacity=4000, grow=True, max_capacity=8000)
    idx = pool.acquire()
    obj = pool[idx]
    pool.release(idx)

    # Systems manage their own active list:
    for idx in my_active_list:
        obj = pool[idx]
"""

from typing import Callable, TypeVar, Optional, List

T = TypeVar('T')


class ObjectPool:
    """A generic object pool using pre-allocation and free-index tracking.

    The caller owns the active-indices list; the pool only manages the
    storage array and the free-list.
    """

    def __init__(self, factory: Callable[[], T], capacity: int = 1000,
                 grow: bool = False, max_capacity: int = 0):
        self._factory = factory
        self._capacity = capacity
        self._grow = grow
        self._max_capacity = max_capacity if max_capacity > 0 else capacity
        self._objects: List[T] = [factory() for _ in range(capacity)]
        self._free: List[int] = list(range(capacity))

        # Statistics
        self._peak_active = 0
        self._total_acquired = 0
        self._total_released = 0
        self._grow_count = 0
        self._current_active = 0

    # -- Public API ---------------------------------------------------------

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def free_count(self) -> int:
        return len(self._free)

    @property
    def active_count(self) -> int:
        return self._current_active

    @property
    def utilization(self) -> float:
        if self._capacity == 0:
            return 0.0
        return self._current_active / self._capacity

    @property
    def peak_active(self) -> int:
        return self._peak_active

    @property
    def total_acquired(self) -> int:
        return self._total_acquired

    @property
    def total_released(self) -> int:
        return self._total_released

    @property
    def grow_count(self) -> int:
        return self._grow_count

    def acquire(self) -> Optional[int]:
        """Acquire an index from the pool. Returns None if exhausted."""
        if not self._free:
            if self._grow and self._capacity < self._max_capacity:
                self._grow_pool()
            else:
                return None
        idx = self._free.pop()
        self._current_active += 1
        self._total_acquired += 1
        if self._current_active > self._peak_active:
            self._peak_active = self._current_active
        return idx

    def release(self, idx: int):
        """Return an index to the pool. Safe to call multiple times for the same index."""
        if 0 <= idx < len(self._objects) and self._objects[idx].active:
            self._objects[idx].active = False
            self._free.append(idx)
            self._current_active -= 1
            self._total_released += 1

    def reset(self):
        """Reset pool to initial state: all objects freed and marked inactive."""
        for idx in range(len(self._objects)):
            self._objects[idx].active = False
        self._free = list(range(len(self._objects)))
        self._current_active = 0
        self._peak_active = 0

    def release_all(self, active_indices: List[int]):
        """Release all indices in the given active list."""
        for idx in active_indices:
            if idx is not None and 0 <= idx < len(self._objects):
                self._objects[idx].active = False
                self._free.append(idx)
        self._total_released += len(active_indices)
        self._current_active -= len(active_indices)

    def __getitem__(self, idx: int) -> T:
        return self._objects[idx]

    def __len__(self) -> int:
        return self._capacity

    def __contains__(self, idx: int) -> bool:
        return 0 <= idx < len(self._objects)

    # -- Statistics ---------------------------------------------------------

    def stats(self) -> dict:
        return {
            'capacity': self._capacity,
            'active': self._current_active,
            'free': len(self._free),
            'utilization': self.utilization,
            'peak_active': self._peak_active,
            'total_acquired': self._total_acquired,
            'total_released': self._total_released,
            'grow_count': self._grow_count,
        }

    def reset_stats(self):
        self._peak_active = self._current_active
        self._total_acquired = 0
        self._total_released = 0
        self._grow_count = 0

    # -- Internal -----------------------------------------------------------

    def _grow_pool(self):
        old = self._capacity
        self._capacity = min(self._capacity * 2, self._max_capacity)
        for _ in range(self._capacity - old):
            self._objects.append(self._factory())
            self._free.append(len(self._objects) - 1)
        self._grow_count += 1
