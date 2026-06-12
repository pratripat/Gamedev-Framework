from .systems.scene.scene_manager import SceneManager
from .scenes.game_scene import GameScene
from .systems.input.input_system import Input
from .systems.core.event_manager import EventManager
from .systems.core.game_context import GameContext
from .utils import INITIAL_WINDOW_SIZE
import pygame

class Game():
    def __init__(self):
        # TEMP
        pygame.init()

        self.screen = pygame.display.set_mode(INITIAL_WINDOW_SIZE, pygame.RESIZABLE | pygame.SCALED)
        pygame.display.set_caption("Game")
        pygame.mouse.set_visible(False)
        self.time = 1
        # TEMP

        # Internal pixel-art resolution (half size)
        self.virtual_size = (INITIAL_WINDOW_SIZE[0] // 2, INITIAL_WINDOW_SIZE[1] // 2)
        self.virtual_surface = pygame.Surface(self.virtual_size).convert()

        self.clock = pygame.time.Clock()
        self.target_fps = 60

        self.ctx = GameContext()

        self.setup()

    def setup(self):
        self.ctx.init()
        # Ensure the Context/Utils know about the virtual center if needed
        # We pass virtual_size to GameScene if it needs it, or just use it here
        self.game_scene = GameScene(self.ctx)

        self.ctx.scene_manager.add_scene(self.game_scene)
        self.ctx.scene_manager.set_current_scene("game")

    def run(self):
        self.ctx.scene_manager.play_scene()

        while True:
            # Calculate frame time (ms -> seconds) and current FPS
            self.calculate_dt()
            self.update()
            self.render()
    
    def render(self):
        # expose timing info to scenes for diagnostics (fps, dt)
        self.ctx.fps = getattr(self, 'fps', 0)
        self.ctx.dt = getattr(self, 'dt', 0)

        # Render world to virtual surface
        self.ctx.scene_manager.render_scene(self.virtual_surface)
        
        # Scale up 2x using nearest-neighbor (fast and crisp)
        scaled_up = pygame.transform.scale(self.virtual_surface, self.screen.get_size())
        self.screen.blit(scaled_up, (0,0))

        # Render UI to the screen
        self.ctx.scene_manager.render_ui(self.screen)

        # Render custom cursor on top of everything (on the actual screen)
        cursor_img = self.ctx.resource_manager.get_image("data/graphics/images/cursor.png", scale=3)
        if cursor_img:
            # We don't divide by 2 here because we are drawing on the unscaled screen
            mx, my = pygame.mouse.get_pos()
            cw, ch = cursor_img.get_size()
            self.screen.blit(cursor_img, (mx - cw // 2, my - ch // 2))

        pygame.display.update()

    def update(self):
        self.ctx.input_system.update(self.ctx.event_manager)

        # TEMP
        self.ctx.scene_manager.update_scene(fps=self.target_fps, dt=self.dt)

    def calculate_dt(self):
        # tick() returns milliseconds passed since last call; convert to seconds
        ms = self.clock.tick(self.target_fps)
        self.dt = ms / 1000.0
        # current smoothed FPS (may be 0 briefly on startup)
        self.fps = self.clock.get_fps()