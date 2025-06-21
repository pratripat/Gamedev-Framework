class SquashEffect:
    def __init__(self, start_scale, target_scale, duration, timer=0, return_to_normal=True):
        self.start_scale = start_scale
        self.target_scale = target_scale
        self.duration = duration
        self.timer = timer
        self.return_to_normal = return_to_normal
    
    