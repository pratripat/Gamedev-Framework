from .resource_manager import ResourceManager
from ..scene.scene_manager import SceneManager
from ..input.input_system import Input
from .event_manager import EventManager
from ..animation.animation_handler import AnimationHandler
from ..audio.audio_manager import AudioManager

class GameContext:
    def __init__(self):
        self.resource_manager = None
        self.scene_manager = None
        self.input_system = None
        self.event_manager = None
        self.animation_handler = None
        self.audio_manager = None

    def init(self):
        self.resource_manager = ResourceManager()
        self.scene_manager = SceneManager()
        self.input_system = Input()
        self.event_manager = EventManager()
        self.animation_handler = AnimationHandler(self.resource_manager)
        self.audio_manager = AudioManager()