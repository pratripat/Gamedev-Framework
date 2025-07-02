from ...components.timer import TimerComponent

class TimerSystem:
    def __init__(self, component_manager):
        self.cm = component_manager
    
    def update(self, dt):
        for eid in self.cm.get_entities_with(TimerComponent):
            timer_comp = self.cm.get(eid, TimerComponent)
            timer_comp.update(dt)

            if timer_comp.destroy and timer_comp.duration <= 0:
                self.cm.remove(eid, TimerComponent)