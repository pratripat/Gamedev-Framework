from .ecs.component import AnimationComponent

class AnimationStateMachine:
    def __init__(self, entity_id, component_manager, animation_priority_list, transitions={}):
        self.entity_id = entity_id
        self.component_manager = component_manager
        self.animation_priority_list = animation_priority_list
        self.transitions = transitions
    
    def update(self, dt):
        """
        Updates the animation state machine, checking for transitions and updating the current animation.
        :param dt: The elapsed time since the last update.
        """
        current_animation_id = self.animation_component.animation_id 
        if current_animation_id in self.transitions:
            to_animation = self.transitions[current_animation_id]["to_animation"]
            cond = self.transitions[current_animation_id]["cond"]

            if cond():
                if to_animation:
                    self.animation_component.set_animation(to_animation)
                
                if self.transitions[current_animation_id]["self_dest"]:
                    del self.transitions[current_animation_id]
        
        self.animation_component.update(dt)

    def add_transition(self, from_animation, to_animation, cond, self_dest=True):
        """
        Adds a transition from one animation to another based on a condition.
        
        :param from_animation: The animation to transition from.
        :param to_animation: The animation to transition to.
        :param condition: A callable that returns True if the transition should occur.
        """
        if from_animation in self.transitions:
            # print("[ANIMATION STATE MACHINE] Requested transition from animation {from_animation} to {to_animation}, but a preexisting transition is present (DEBUG)")
            return
        
        self.transitions[from_animation] = {
            "to_animation": to_animation,
            "cond": cond,
            "self_dest": self_dest
        }
    
    def set_animation(self, animation_id):
        if animation_id not in self.animation_priority_list:
            print(f"[ANIMATION STATE MACHINE] Animation {animation_id} not found in priority list. (DEBUG)")
            return
    
        if self.animation_priority_list.index(animation_id) > self.animation_priority_list.index(self.animation_component.animation_id):
            print(f"[ANIMATION STATE MACHINE] Setting animation {animation_id} (DEBUG)")
            self.animation_component.set_animation(animation_id)

    @property
    def animation_component(self):
        return self.component_manager.get(self.entity_id, AnimationComponent)