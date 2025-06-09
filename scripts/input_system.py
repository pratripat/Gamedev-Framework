import pygame, sys

class Input:
    def __init__(self):
        self.keys_pressed = []
        self.keys_held = []
        self.mouse_position = [0, 0]
        self.mouse_states = {
            'left': False,
            'right': False,
            'left_held': False,
            'right_held': False,
            'left_release': True,
            'right_release': True
        }
        self.input_binds = {"keys_pressed": {}, "keys_released": {}, "keys_held": {}, "mouse_clicked": {}, "mouse_held": {}}

        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP])

    def update(self, event_manager):
        self.mouse_position = list(pygame.mouse.get_pos())
        self.keys_pressed.clear()
        self.mouse_states['left'] = self.mouse_states['right'] = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                # key pressed logic
                self.keys_pressed.append(event.key)

                # key held logic
                if event.key not in self.keys_held:
                    self.keys_held.append(event.key)

                # handles events based on input_binds pressed
                if event.key in self.input_binds['keys_pressed']:
                    # print(f"[INPUT] the following key is held '{event.key}' (DEBUG)")
                    event_type = self.input_binds['keys_pressed'][event.key]
                    event_manager.emit(event_type)

            if event.type == pygame.KEYUP:
                if event.key in self.keys_held:
                    self.keys_held.remove(event.key)
                
                # handles events based on input_binds released
                if event.key in self.input_binds['keys_released']:
                    # print(f"[INPUT] the following key is held '{event.key}' (DEBUG)")
                    event_type = self.input_binds['keys_released'][event.key]
                    event_manager.emit(event_type)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_states['left'] = not self.mouse_states['left']

                    self.mouse_states['left_held'] = True
                    self.mouse_states['left_release'] = False
                    
                if event.button == 3:
                    self.mouse_states['right'] = not self.mouse_states['right']

                    self.mouse_states['right_held'] = True
                    self.mouse_states['right_release'] = False

                # handles events based on input_binds mouse events
                if event.button in self.input_binds['mouse_clicked']:
                    # print(f"[INPUT] the following mouse button is pressed '{event.button}' (DEBUG)")
                    event_type = self.input_binds['mouse_clicked'][event.button]
                    event_manager.emit(event_type)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_states['left'] = False
                    self.mouse_states['left_held'] = False
                    self.mouse_states['left_release'] = True
                if event.button == 3:
                    self.mouse_states['right'] = False
                    self.mouse_states['right_held'] = False
                    self.mouse_states['right_release'] = True
        
        # Update input_binds for held keys
        for key in self.keys_held:
            if key in self.input_binds['keys_held']:
                # print(f"[INPUT] the following key is held '{key}' (DEBUG)")
                event_type = self.input_binds['keys_held'][key]
                event_manager.emit(event_type)
        
        # Update input_binds for held mouse 
        if self.mouse_inputs["left_held"]: 
            if 1 in self.input_binds["mouse_held"]:
                event_type = self.input_binds["mouse_held"][1]
                event_manager.emit(event_type)
        if self.mouse_inputs["right_held"]:
            if 3 in self.input_binds["mouse_held"]:
                event_type = self.input_binds["mouse_held"][3]
                event_manager.emit(event_type)     


    def set_input_binds(self, keys_pressed={}, keys_released={}, keys_held={}, mouse_clicked={}, mouse_held={}):
        """
        Set input_binds for the input system.
            Dictionary mapping pygame key constants to event names.
        """
        self.input_binds["keys_pressed"] = keys_pressed
        self.input_binds["keys_released"] = keys_released
        self.input_binds["keys_held"] = keys_held
        self.input_binds["mouse_clicked"] = mouse_clicked
        self.input_binds["mouse_held"] = mouse_held

    @property
    def key_inputs(self) -> dict:
        return {'keys_pressed': self.keys_pressed, 'keys_held': self.keys_held}

    @property
    def mouse_inputs(self) -> dict:
        return self.mouse_states