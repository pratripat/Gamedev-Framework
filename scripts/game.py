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

    def run(self):
        self.scene_manager.play_scene({
            "event_manager": self.event_manager,
            "input_system": self.input_system
        })

        self.event_manager.emit("game_start")

        while 1:
            self.update()

    def update(self):
        self.input_system.update(self.event_manager)

        # TEMP
        dt = 1/60
        self.scene_manager.update_scene(dt)
