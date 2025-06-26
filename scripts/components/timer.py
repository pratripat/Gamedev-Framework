class TimerComponent:
    def __init__(self, duration, *callbacks, destroy=True):
        self.duration = duration
        self.callbacks = [callback for callback in callbacks]
        self.destroy = destroy

    def update(self, fps, dt):
        self.duration -= dt / fps
        if self.duration <= 0:
            self.duration = 0
            self.trigger()
    
    def trigger(self):
        for callback in self.callbacks:
            callback()