"""Stack-safe time-scale manipulation (hit stop, slow motion).

Usage::

    ts = TimeScale()
    ts.push(0.1, 0.0)       # 100 ms full freeze
    ts.push(0.5, 0.3)       # 500 ms at 30 % speed (on top of freeze)

    # In update loop:
    raw_dt = dt
    dt *= ts.scale           # apply current time scale
    ts.update(raw_dt)        # tick down stacks using *unscaled* time
"""


class TimeScale:
    """Maintains a stack of (remaining, scale) entries.

    The effective ``scale`` is the top entry's scale, or ``1.0`` when
    the stack is empty.  Pushing a new entry stacks on top — when it
    expires the previous entry resumes.
    """

    def __init__(self):
        self._stack: list[list[float]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def scale(self) -> float:
        """Current global time scale (1.0 = normal)."""
        return self._stack[-1][1] if self._stack else 1.0

    @property
    def is_paused(self) -> bool:
        """True when the effective scale is 0.0 (full freeze)."""
        return self.scale == 0.0

    @property
    def active(self) -> bool:
        """True when any time-scale effect is active."""
        return bool(self._stack)

    def push(self, duration: float, scale: float = 0.0):
        """Push a new time-scale effect.

        Args:
            duration: Real-time seconds the effect lasts (unscaled).
            scale:    Target time scale (0.0 = full freeze, 1.0 = normal).
        """
        if duration > 0:
            self._stack.append([duration, scale])

    def update(self, raw_dt: float):
        """Tick down the stack using *unscaled* delta time.

        Call **after** the game loop has consumed ``raw_dt * self.scale``.
        """
        if not self._stack:
            return
        self._stack[-1][0] -= raw_dt
        while self._stack and self._stack[-1][0] <= 0:
            self._stack.pop()

    def clear(self):
        """Instantly remove all time-scale effects."""
        self._stack.clear()

    def stats(self) -> dict:
        return {
            'active': self.active,
            'scale': self.scale,
            'stack_depth': len(self._stack),
        }
