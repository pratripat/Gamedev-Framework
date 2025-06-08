from .scene_manager import SceneManager
from .scenes.game_scene import GameScene
from .input_system import Input
from .event_manager import EventManager
from .utils import INTIAL_WINDOW_SIZE
import pygame

class Game():
    def __init__(self):
        # TEMP
        pygame.init()

        self.screen = pygame.display.set_mode(INTIAL_WINDOW_SIZE, pygame.RESIZABLE | pygame.SCALED)
        pygame.display.set_caption("Game")
        # TEMP

        self.clock = pygame.time.Clock()
        self.fps = 60

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
            self.clock.tick(self.fps)
            self.calculate_dt()
            self.update()
            self.render()
    
    def render(self):
        self.screen.fill((0, 0, 0))
        self.scene_manager.render_scene(self.screen)
        pygame.display.update()

    def update(self):
        self.input_system.update(self.event_manager)

        # TEMP
        self.scene_manager.update_scene(self.dt)

    def calculate_dt(self):
        fps = self.clock.get_fps()
        # print(fps)
        
        if fps == 0: 
            self.dt = 0
        else: 
            self.dt = (1 / fps) * self.fps