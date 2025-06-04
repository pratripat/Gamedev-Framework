class Scene(): 
    def __init__(self, id: str):
        self.id = id

    def start(self):
        print(f"[SCENE] Starting scene: '{self.id}' (DEBUG)")
    
class SceneManager():
    def __init__(self):
        self.scenes = []
        self.current_scene = None

    def get_scene(self, id: str) -> Scene:
        for scene in self.scenes:
            if scene.id == id:
                return scene
        return None
    
    def set_current_scene(self, id: str):
        scene = self.get_scene(id)
        if scene:
            self.current_scene = scene
        else:
            raise ValueError(f"Scene with id {id} not found.")

    def add_scene(self, scene: Scene):
        self.scenes.append(scene)

    def play_scene(self):
        self.current_scene.start()
