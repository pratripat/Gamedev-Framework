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
            raise ValueError(f"[SCENE MANAGER] Scene with id {id} not found. (DEBUG)")

    def add_scene(self, scene: Scene):
        if self.get_scene(scene.id):
            raise ValueError(f"[SCENE MANAGER] Scene with id {scene.id} already exists. (DEBUG)")
        self.scenes.append(scene)
    
    def render_scene(self, screen):
        if not self.current_scene:
            raise RuntimeError("[SCENE MANAGER] No current scene set. (DEBUG)")
        
        self.current_scene.render(screen)

    def update_scene(self, **kwargs):
        if not self.current_scene:
            raise RuntimeError("[SCENE MANAGER] No current scene set. (DEBUG)")
        
        self.current_scene.update(**kwargs)

    def remove_scene(self, id: str):
        scene = self.get_scene(id)
        if scene:
            self.scenes.remove(scene)
            if self.current_scene == scene:
                self.current_scene = None
        else:
            raise ValueError(f"[SCENE MANAGER] Scene with id {id} not found. (DEBUG)")

    def play_scene(self, data: dict):
        if not self.current_scene:
            raise RuntimeError("[SCENE MANAGER] No current scene set. (DEBUG)")
        self.current_scene.start(*(data.values()))
