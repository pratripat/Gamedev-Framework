from collections import defaultdict

class EventManager:
    def __init__(self):
        # using defaultdict to simplify subscriber management
        # if an event_type is not found in the dictionary, it will return an empty list instead of raising a KeyError
        self.subscribers = defaultdict(list)
    
    def subscribe(self, event_type, callback):
        self.subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type, callback):
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
            except ValueError:
                print(f"[EVENT MANAGER] Callback '{callback}' was not found for event '{event_type}'. (DEBUG)")
        else:
            print(f"[EVENT MANAGER] No subscribers for event '{event_type}'. (DEBUG)")

    def emit(self, event_type, **kwargs):
        # print(f"[EVENT MANAGER] Emitting event '{event_type}' with kwargs: [{kwargs}] (DEBUG)")
        for callback in self.subscribers[event_type]:
            if kwargs: callback(**kwargs)
            else: callback()