from collections import defaultdict

class EventManager:
    def __init__(self):
        # using defaultdict to simplify subscriber management
        # if an event_type is not found in the dictionary, it will return an empty list instead of raising a KeyError
        self.subscribers = defaultdict(list)
    
    def subscribe(self, event_type, *callbacks, source=None):
        for callback in callbacks:
            self.subscribers[event_type].append((callback, source))
    
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

    def emit(self, event_type, **kwargs):
        # print(f"[EVENT MANAGER] Emitting event '{event_type}' with kwargs: [{kwargs}] (DEBUG)")
        for callback, _ in self.subscribers[event_type]:
            if kwargs: callback(**kwargs)
            else: callback()