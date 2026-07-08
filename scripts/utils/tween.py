"""
Universal Tween Framework

Provides:
- Easing functions (Robert Penner-style)
- Tween class for generic property animation
- TweenSystem for lifecycle management
- Chaining, delays, callbacks, cancellation, ping-pong, repeat

Usage:
    tween = Tween(player_pos, 'x', 100, 200, 1.0, ease_out_quad)
    tween.on_complete = lambda: print("done")
    tween_system.add(tween)

    # In update loop:
    tween_system.update(dt)
"""

import math
import pygame


# ---------------------------------------------------------------------------
# Easing Functions
# ---------------------------------------------------------------------------

def ease_linear(t):
    return t

def ease_in_quad(t):
    return t * t

def ease_out_quad(t):
    return t * (2 - t)

def ease_in_out_quad(t):
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t

def ease_in_cubic(t):
    return t * t * t

def ease_out_cubic(t):
    return (t - 1) ** 3 + 1

def ease_in_out_cubic(t):
    if t < 0.5:
        return 4 * t * t * t
    return (t - 1) * (2 * t - 2) * (2 * t - 2) + 1

def ease_in_quart(t):
    return t * t * t * t

def ease_out_quart(t):
    return 1 - (t - 1) ** 4

def ease_in_out_quart(t):
    if t < 0.5:
        return 8 * t * t * t * t
    return 1 - 8 * (t - 1) ** 4

def ease_in_quint(t):
    return t ** 5

def ease_out_quint(t):
    return 1 + (t - 1) ** 5

def ease_in_out_quint(t):
    if t < 0.5:
        return 16 * t ** 5
    return 1 + 16 * (t - 1) ** 5

def ease_in_sine(t):
    return 1 - math.cos(t * math.pi / 2)

def ease_out_sine(t):
    return math.sin(t * math.pi / 2)

def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2

def ease_in_expo(t):
    return 0 if t <= 0 else math.pow(2, 10 * (t - 1))

def ease_out_expo(t):
    return 1 if t >= 1 else 1 - math.pow(2, -10 * t)

def ease_in_out_expo(t):
    if t <= 0 or t >= 1:
        return t
    if t < 0.5:
        return math.pow(2, 20 * t - 10) / 2
    return (2 - math.pow(2, -20 * t + 10)) / 2

def ease_in_circ(t):
    return 1 - math.sqrt(1 - t * t)

def ease_out_circ(t):
    return math.sqrt(1 - (t - 1) * (t - 1))

def ease_in_out_circ(t):
    if t < 0.5:
        return (1 - math.sqrt(1 - 4 * t * t)) / 2
    return (1 + math.sqrt(1 - (2 * t - 2) ** 2)) / 2

def ease_in_elastic(t):
    if t <= 0 or t >= 1:
        return t
    return -(math.pow(2, 10 * (t - 1)) * math.sin((t - 1.075) * 2 * math.pi / 0.3))

def ease_out_elastic(t):
    if t <= 0 or t >= 1:
        return t
    return math.pow(2, -10 * t) * math.sin((t - 0.075) * 2 * math.pi / 0.3) + 1

def ease_in_out_elastic(t):
    if t <= 0 or t >= 1:
        return t
    t *= 2
    if t < 1:
        return -0.5 * (math.pow(2, 10 * (t - 1)) * math.sin((t - 1.075) * 2 * math.pi / 0.3))
    return 0.5 * (math.pow(2, -10 * (t - 1)) * math.sin((t - 1.075) * 2 * math.pi / 0.3)) + 1

def ease_in_back(t):
    return t * t * (2.70158 * t - 1.70158)

def ease_out_back(t):
    t -= 1
    return t * t * (2.70158 * t + 1.70158) + 1

def ease_in_out_back(t):
    t *= 2
    if t < 1:
        return 0.5 * t * t * (3.5949095 * t - 2.5949095)
    t -= 2
    return 0.5 * (t * t * (3.5949095 * t + 2.5949095) + 2)

def ease_out_bounce(t):
    if t < 1 / 2.75:
        return 7.5625 * t * t
    if t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    if t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    t -= 2.625 / 2.75
    return 7.5625 * t * t + 0.984375

def ease_in_bounce(t):
    return 1 - ease_out_bounce(1 - t)

def ease_in_out_bounce(t):
    if t < 0.5:
        return (1 - ease_out_bounce(1 - 2 * t)) / 2
    return (1 + ease_out_bounce(2 * t - 1)) / 2


EASING_FUNCTIONS = {
    'linear': ease_linear,
    'in_quad': ease_in_quad,
    'out_quad': ease_out_quad,
    'in_out_quad': ease_in_out_quad,
    'in_cubic': ease_in_cubic,
    'out_cubic': ease_out_cubic,
    'in_out_cubic': ease_in_out_cubic,
    'in_quart': ease_in_quart,
    'out_quart': ease_out_quart,
    'in_out_quart': ease_in_out_quart,
    'in_quint': ease_in_quint,
    'out_quint': ease_out_quint,
    'in_out_quint': ease_in_out_quint,
    'in_sine': ease_in_sine,
    'out_sine': ease_out_sine,
    'in_out_sine': ease_in_out_sine,
    'in_expo': ease_in_expo,
    'out_expo': ease_out_expo,
    'in_out_expo': ease_in_out_expo,
    'in_circ': ease_in_circ,
    'out_circ': ease_out_circ,
    'in_out_circ': ease_in_out_circ,
    'in_elastic': ease_in_elastic,
    'out_elastic': ease_out_elastic,
    'in_out_elastic': ease_in_out_elastic,
    'in_back': ease_in_back,
    'out_back': ease_out_back,
    'in_out_back': ease_in_out_back,
    'in_bounce': ease_in_bounce,
    'out_bounce': ease_out_bounce,
    'in_out_bounce': ease_in_out_bounce,
}


# ---------------------------------------------------------------------------
# Value interpolation helpers (handles Vector2, float, int, pygame.Color)
# ---------------------------------------------------------------------------

def _lerp_value(start, end, t):
    if isinstance(start, pygame.Vector2):
        return start.lerp(end, t)
    if isinstance(start, (list, tuple)):
        return type(start)(_lerp_value(s, e, t) for s, e in zip(start, end))
    if isinstance(start, pygame.Color):
        r = int(start.r + (end.r - start.r) * t)
        g = int(start.g + (end.g - start.g) * t)
        b = int(start.b + (end.b - start.b) * t)
        a = int(start.a + (end.a - start.a) * t)
        return pygame.Color(r, g, b, a)
    return start + (end - start) * t


# ---------------------------------------------------------------------------
# Tween
# ---------------------------------------------------------------------------

class Tween:
    """Animates a property on a target object from start to end value."""

    def __init__(self, target, prop_name, start_value, end_value, duration,
                 easing='out_quad', delay=0.0, repeat=0, ping_pong=False):
        self.target = target
        self.prop_name = prop_name
        self.start_value = start_value
        self.end_value = end_value
        self.duration = duration
        self.easing = EASING_FUNCTIONS[easing] if isinstance(easing, str) else easing
        self.delay = delay
        self.repeat = repeat          # 0 = no repeat, -1 = infinite
        self.ping_pong = ping_pong

        self.elapsed = 0.0
        self._alive = True
        self._finished = False
        self._direction = 1           # 1 = forward, -1 = backward (ping-pong)
        self._repeat_count = 0

        # Callbacks
        self.on_start = None
        self.on_update = None
        self.on_complete = None
        self.on_cancel = None

        # Chain: next tween starts when this one completes
        self._next_tween = None

        self._started = False

        # Apply initial value
        setattr(target, prop_name, start_value)

    @property
    def alive(self):
        return self._alive

    @property
    def finished(self):
        return self._finished

    def chain(self, next_tween):
        """Queue a tween to start after this one finishes."""
        self._next_tween = next_tween
        return next_tween

    def cancel(self):
        self._alive = False
        self._finished = True
        if self.on_cancel:
            self.on_cancel()

    def update(self, dt):
        if not self._alive or self._finished:
            return None

        # Delay phase
        if self.delay > 0:
            self.delay -= dt
            if self.delay > 0:
                return None
            dt = -self.delay
            self.delay = 0.0

        if not self._started:
            self._started = True
            if self.on_start:
                self.on_start()

        self.elapsed += dt

        t = min(self.elapsed / self.duration, 1.0)
        if self._direction == -1:
            t = 1.0 - t

        eased_t = self.easing(t)

        setattr(self.target, self.prop_name,
                _lerp_value(self.start_value, self.end_value, eased_t))

        if self.on_update:
            self.on_update()

        if t >= 1.0:
            return self._handle_complete()

        return None

    def _handle_complete(self):
        if self.ping_pong:
            self._direction *= -1
            self.elapsed = 0.0
            if self._direction == -1:
                self.start_value, self.end_value = self.end_value, self.start_value
            return self

        self._repeat_count += 1
        if self.repeat == -1 or self._repeat_count <= self.repeat:
            self.elapsed = 0.0
            return self

        self._alive = False
        self._finished = True

        if self.on_complete:
            self.on_complete()

        if self._next_tween:
            return self._next_tween

        return None

    def __repr__(self):
        return (f"Tween({self.prop_name}: {self.start_value} -> "
                f"{self.end_value}, {self.duration}s, "
                f"{'alive' if self._alive else 'dead'})")


# ---------------------------------------------------------------------------
# TweenSystem
# ---------------------------------------------------------------------------

def _make_nop_target():
    """Minimal object for delayed callbacks or duration-only tweens."""
    return type('_NopTarget', (object,), {'value': 0})()


class TweenSystem:
    """Manages all active tweens. Add/remove/cancel lifecycle."""

    def __init__(self):
        self._tweens = []
        self._completed_count = 0
        self._cancelled_count = 0

    def add(self, tween):
        if tween not in self._tweens:
            self._tweens.append(tween)
        return tween

    def remove(self, tween):
        if tween in self._tweens:
            self._tweens.remove(tween)
        tween.cancel()

    def cancel_all(self):
        for t in self._tweens:
            t._alive = False
            t._finished = True
            self._cancelled_count += 1
        self._tweens.clear()

    def cancel_tweens_for(self, target, prop_name=None):
        """Cancel all tweens for a given target object, optionally filtered by property."""
        kept = []
        for t in self._tweens:
            if t.target is target and (prop_name is None or t.prop_name == prop_name):
                t._alive = False
                t._finished = True
                self._cancelled_count += 1
            else:
                kept.append(t)
        self._tweens = kept

    def update(self, dt):
        spawned = []
        i = 0
        while i < len(self._tweens):
            t = self._tweens[i]
            result = t.update(dt)
            if result is not None and result is not t:
                spawned.append(result)
            if t.finished or not t.alive:
                if t.finished:
                    self._completed_count += 1
                else:
                    self._cancelled_count += 1
                self._tweens[i] = self._tweens[-1]
                self._tweens.pop()
                continue
            i += 1
        for nt in spawned:
            self._tweens.append(nt)

    def all_alive(self):
        return list(self._tweens)

    @property
    def count(self):
        return len(self._tweens)

    @property
    def completed_count(self):
        return self._completed_count

    @property
    def cancelled_count(self):
        return self._cancelled_count

    def stats(self) -> dict:
        return {
            'active': self.count,
            'completed': self._completed_count,
            'cancelled': self._cancelled_count,
        }

    def reset_stats(self):
        self._completed_count = 0
        self._cancelled_count = 0

    def to(self, target, prop_name, end_value, duration, **kwargs):
        """Create and add a tween from current value to end_value."""
        start = getattr(target, prop_name)
        t = Tween(target, prop_name, start, end_value, duration, **kwargs)
        return self.add(t)

    def from_to(self, target, prop_name, start_value, end_value, duration, **kwargs):
        """Create and add a tween from start_value to end_value."""
        t = Tween(target, prop_name, start_value, end_value, duration, **kwargs)
        return self.add(t)

    def after(self, delay, callback):
        """Schedule a callback after a delay (zero-duration tween)."""
        nop = _make_nop_target()
        t = Tween(nop, 'value', 0, 0, delay, easing='linear')
        t.on_complete = callback
        return self.add(t)
