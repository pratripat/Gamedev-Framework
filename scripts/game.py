from .scene_manager import SceneManager
from .scenes.game_scene import GameScene
from .input_system import Input
from .event_manager import EventManager
import pygame

class Game():
    def __init__(self):
        # TEMP
        pygame.init()

        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Game")
        # TEMP

        self.game_scene = GameScene()
        self.scene_manager = SceneManager()
        self.input_system = Input()
        self.event_manager = EventManager()

        self.setup()

    def setup(self):
        self.scene_manager.add_scene(self.game_scene)
        self.scene_manager.set_current_scene("game")

        self.event_manager.subscribe("game_start", self.scene_manager.play_scene)

        # TEMP
        # keybinds

        self.event_manager.subscribe("player_up", lambda: print("Player moving up"))
        self.event_manager.subscribe("player_down", lambda: print("Player moving down"))
        self.event_manager.subscribe("player_left", lambda: print("Player moving left"))
        self.event_manager.subscribe("player_right", lambda: print("Player moving right"))

        self.input_system.set_keybinds(
            keys_held = {
                pygame.K_w: "player_up",
                pygame.K_s: "player_down",
                pygame.K_a: "player_left",
                pygame.K_d: "player_right"
            }
        )

        # TEMP

    def run(self):
        # self.scene_manager.play_scene()

        self.event_manager.emit("game_start")

        while 1:
            self.update()

    def update(self):
        self.input_system.update(self.event_manager)
