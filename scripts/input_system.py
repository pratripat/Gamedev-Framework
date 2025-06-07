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
        self.keybinds = {"keys_pressed": {}, "keys_released": {}, "keys_held": {}}

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

                # handles events based on keybinds pressed
                if event.key in self.keybinds['keys_pressed']:
                    # print(f"[INPUT] the following key is held '{event.key}' (DEBUG)")
                    event_type = self.keybinds['keys_pressed'][event.key]
                    event_manager.emit(event_type)

            if event.type == pygame.KEYUP:
                if event.key in self.keys_held:
                    self.keys_held.remove(event.key)
                
                # handles events based on keybinds released
                if event.key in self.keybinds['keys_released']:
                    # print(f"[INPUT] the following key is held '{event.key}' (DEBUG)")
                    event_type = self.keybinds['keys_released'][event.key]
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

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_states['left'] = False
                    self.mouse_states['left_held'] = False
                    self.mouse_states['left_release'] = True
                if event.button == 3:
                    self.mouse_states['right'] = False
                    self.mouse_states['right_held'] = False
                    self.mouse_states['right_release'] = True
        
        # Update keybinds for held keys
        for key in self.keys_held:
            if key in self.keybinds['keys_held']:
                # print(f"[INPUT] the following key is held '{key}' (DEBUG)")
                event_type = self.keybinds['keys_held'][key]
                event_manager.emit(event_type)

    def set_keybinds(self, keys_pressed={}, keys_released={}, keys_held={}):
        """
        Set keybinds for the input system.
            Dictionary mapping pygame key constants to event names.
        """
        self.keybinds["keys_pressed"] = keys_pressed
        self.keybinds["keys_released"] = keys_released
        self.keybinds["keys_held"] = keys_held

    @property
    def key_inputs(self) -> dict:
        return {'keys_pressed': self.keys_pressed, 'keys_held': self.keys_held}

    @property
    def mouse_inputs(self) -> dict:
        return self.mouse_states