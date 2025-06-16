from .systems.scene.scene_manager import SceneManager
from .scenes.game_scene import GameScene
from .systems.input.input_system import Input
from .systems.core.event_manager import EventManager
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
        self.target_fps = 60

        self.event_manager = EventManager()
        self.input_system = Input()
        self.scene_manager = SceneManager()
        self.game_scene = GameScene(self.event_manager)

        self.setup()

    def setup(self):
        self.scene_manager.add_scene(self.game_scene)
        self.scene_manager.set_current_scene("game")

    def run(self):
        self.scene_manager.play_scene(input_system=self.input_system)

        while 1:
            self.clock.tick(self.target_fps)
            # self.clock.tick()
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
        self.scene_manager.update_scene(fps=self.target_fps, dt=self.dt)

    def calculate_dt(self):
        self.fps = self.clock.get_fps()
        # print(self.fps)
        
        if self.fps == 0: 
            self.dt = 0
        else: 
            self.dt = (1 / self.fps) * self.target_fps