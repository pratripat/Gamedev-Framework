from collections import defaultdict
from ...utils import GameSceneEvents
from ...utils.events import TYPED_EVENT_MAP, GameEvent

class EventManager:
    def __init__(self):
        # using defaultdict to simplify subscriber management
        # if an event_type is not found in the dictionary, it will return an empty list instead of raising a KeyError
        self.subscribers = defaultdict(list)
        self._typed_subscribers = defaultdict(list)
    
    def subscribe(self, event_type, *callbacks, source=None):
        for callback in callbacks:
            self.subscribers[event_type].append((callback, source))
    
    def subscribe_typed(self, event_class, callback, source=None):
        """Subscribe to a typed event class (e.g. DamageEvent).
        
        Typed subscribers receive the event object directly.
        They are NOT mixed with legacy kwargs-based subscribers.
        """
        self._typed_subscribers[event_class].append((callback, source))
    
    def unsubscribe_typed(self, event_class, callback, source=None):
        """Remove a typed subscriber."""
        if event_class in self._typed_subscribers:
            try:
                self._typed_subscribers[event_class].remove((callback, source))
            except ValueError:
                pass
    
    def unsubscribe(self, event_type, callback, source=None):
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove((callback, source))
            except ValueError:
                print(f"[EVENT MANAGER] Callback '{callback}' was not found for event '{event_type}'. (DEBUG)")
        else:
            print(f"[EVENT MANAGER] No subscribers for event '{event_type}'. (DEBUG)")

    def unsubscribe_all_for(self, source):
        for event_type in list(self.subscribers):
            original = self.subscribers[event_type]
            self.subscribers[event_type] = [
                (cb, src) for cb, src in original if src != source
            ]
        for event_class in list(self._typed_subscribers):
            original = self._typed_subscribers[event_class]
            self._typed_subscribers[event_class] = [
                (cb, src) for cb, src in original if src != source
            ]

    def emit(self, event_type, **kwargs):
        for callback, _ in self.subscribers[event_type]:
            if kwargs: callback(**kwargs)
            else: callback()

    def emit_typed(self, event):
        """Emit a typed event object. Only typed subscribers receive it.
        Legacy kwargs-based subscribers are NOT notified to avoid signature
        mismatches. Systems should migrate from emit()/subscribe() to
        emit_typed()/subscribe_typed() gradually."""
        for callback, _ in self._typed_subscribers[type(event)]:
            callback(event)

    # -- Statistics / Debug -------------------------------------------------

    @property
    def subscriber_count(self) -> int:
        return sum(len(cbs) for cbs in self.subscribers.values())

    @property
    def typed_subscriber_count(self) -> int:
        return sum(len(cbs) for cbs in self._typed_subscribers.values())

    def stats(self) -> dict:
        return {
            'legacy_event_types': len(self.subscribers),
            'legacy_subscribers': self.subscriber_count,
            'typed_event_types': len(self._typed_subscribers),
            'typed_subscribers': self.typed_subscriber_count,
        }