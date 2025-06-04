from collections import defaultdict

class EventManager:
    def __init__(self):
        # using defaultdict to simplify subscriber management
        # if an event_type is not found in the dictionary, it will return an empty list instead of raising a KeyError
        self.subscribers = defaultdict(list)
    
    def subscribe(self, event_type, callback):
        self.subscribers[event_type].append(callback)

    def emit(self, event_type, data=None):
        print(f"[EVENT MANAGER] Emitting event '{event_type}' with data: [{data}] (DEBUG)")
        for callback in self.subscribers[event_type]:
            if data: callback(data)
            else: callback()