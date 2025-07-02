import pygame, json, bisect
from ...utils import load_image, load_images_from_spritesheet, DEFAULT_COLORKEY, ANIMATION_FOLDER, GameSceneEvents, normalize_scale

class AnimationHandler:
    def __init__(self):
        self.animations = {}
        self.animations_config = json.load(open(f"{ANIMATION_FOLDER}/config.json", "r"))
    
    def load_animation(self, entity):
        """
        Load an animation from a file and store it in the animations dictionary.
        
        :param filepath: Path to the animation file.
        """
        spritesheet_file_path = f"{ANIMATION_FOLDER}/{entity}.png"
        config = self.animations_config.get(entity, {})
        if not config:
            print(f"[ANIMATION] No configuration found for entity '{entity}' (DEBUG)")
            return
    
        try:
            spritesheet_index = 0
            for animation_id in config:
                self.animations[f"{entity}_{animation_id}"] = AnimationData(f"{ANIMATION_FOLDER}/{entity}", config[animation_id], spritesheet_index)
                spritesheet_index += len(config[animation_id]['frames'])

        except FileNotFoundError:
            print(f"[ANIMATION] Animation file '{spritesheet_file_path}' not found (DEBUG)")
            return        
    
    def get_animation(self, animation_id):
        """
        Get the animation data for a given entity.
        
        :param entity: The entity for which to get the animation data.
        :return: AnimationData object if found, None otherwise.
        """
        if animation_id not in self.animations:
            entity = '_'.join(animation_id.split('_')[:-1]) # Extract entity name from animation ID
            self.load_animation(entity)  # Load the animation for the entity if not already loaded
            # print(f"[ANIMATION] Animation '{animation_id}' not found, loading from entity '{entity}' (DEBUG)")
        
        animation_data = self.animations[animation_id]
        return Animation(animation_data, animation_id)

class AnimationData:
    def __init__(self, path, config, spritesheet_index=0):
        """
        Initializes the AnimationData with the path to the spritesheet and its configuration.
        
        :param path: Path to the spritesheet.
        :param config: Configuration for the animation.
        :param spritesheet_index: Index of the spritesheet in case of multiple sheets.
        """
        self.animation_path = path
        self.load_data(path, config, spritesheet_index)
    
    def load_data(self, path, config, spritesheet_index=0):
        """
        Load the animation data from the given path and configuration.
        
        :param path: Path to the spritesheet.
        :param config: Configuration for the animation.
        :param spritesheet_index: Index of the spritesheet in case of multiple sheets.
        """
        images = load_images_from_spritesheet(path+'.png')[spritesheet_index:spritesheet_index + len(config['frames'])]
        if images == []: self.original_images = self.images = load_image(path) # handles if its a single image n not a spritesheet
        else: self.original_images = self.images = images

        self.config = config

        # flips the images horizontally if specified in the config
        if self.config.get("flip", False):
            self.images = [pygame.transform.flip(image, True, False) for image in self.images]
        
        # offset
        self.config["offset"] = pygame.Vector2(self.config["offset"])

        # self.resize_images(self.config.get("scale", 1))
        self.config["scale"] = normalize_scale(self.config.get("scale", 1))
        self.resize_images(self.config["scale"])
        self.config["offset"][0] *= self.config["scale"][0]
        self.config["offset"][1] *= self.config["scale"][1]

    def resize_images(self, scale):
        """
        Resize the images based on the scale factor.
        
        :param scale: Scale factor to resize the images.
        """
        if scale[0] == 1 and scale[1] == 1:
            return

        new_size = (
            (self.original_images[0].get_width() * scale[0]),
            (self.original_images[0].get_height() * scale[1])
        )

        self.images = [pygame.transform.scale(image, new_size) for image in self.original_images]


    #Returns total number of frames of the animation
    def get_frames(self):
        return self.config['frames']

    #Returns all the frames in the form of images
    def get_images(self):
        return self.images

    #Returns the scale of the animation
    def get_scale(self):
        return self.config['scale']

    #Returns the time taken(in frames) to finish the animation
    def duration(self):
        return sum(self.config['frames'])

class Animation:
    def __init__(self, animation_data, animation_id):
        self.animation_data = animation_data
        self.animation_id = animation_id
        self.frame = 0
        self.image = None
        self._frame_lookup = self._generate_frame_lookup()
        self.update_image()

    def _generate_frame_lookup(self):
        frames = self.animation_data.get_frames()
        lookup = []
        total = 0
        for f in frames:
            total += f
            lookup.append(total)
        return lookup

    def update_image(self):
        frame_index = bisect.bisect_right(self._frame_lookup, self.frame)
        frame_index = min(frame_index, len(self.animation_data.get_images()) - 1)
        self.image = self.animation_data.get_images()[frame_index]

    def render(self, surface, pos, flipped=(False, False), angle=0, scale=(1, 1), alpha=None, center=True, offset=None, tint=None):
        img = self.image
        img.set_colorkey(DEFAULT_COLORKEY)
        off = self.animation_data.config.get("offset", pygame.Vector2(0, 0)).copy()

        if flipped != (False, False):
            img = pygame.transform.flip(img, *flipped)

        if angle != 0:
            img = pygame.transform.rotate(img, angle)

        if alpha is not None:
            img = img.copy()
            img.set_alpha(alpha)
        
        if tint is not None:
            # mask = pygame.mask.from_surface(image)
            # image = mask.to_surface()

            # image = image.convert_alpha()

            # Generate a white overlay with transparency in background
            white_overlay = pygame.mask.from_surface(img).to_surface(
                setcolor=(255, 255, 255, 255),
                unsetcolor=(0, 0, 0, 0)
            )

            # Create a copy of the sprite and clear existing color
            silhouette = img.copy()
            silhouette.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # Add white overlay onto cleared base
            silhouette.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

            img = silhouette

        if scale != (1, 1):
            img = pygame.transform.scale(img, (
                int(img.get_width() * scale[0]),
                int(img.get_height() * scale[1])
            ))

        if offset:
            off = offset

        if self.animation_data.config.get("centered", center):
            off.x -= img.get_width() / 2
            off.y -= img.get_height() / 2

        render_pos = (pos[0] + off.x, pos[1] + off.y)
        surface.blit(img, render_pos)

    def run(self, event_manager, entity_id, fps, dt):
        self.frame += self.animation_data.config['speed'] * dt * fps

        if self.frame >= self.animation_data.duration():
            try:
                event_manager.emit(GameSceneEvents.ANIMATION_FINISHED, entity_id=entity_id, animation_id=self.animation_id)
            except:
                pass

            loop = self.animation_data.config['loop']
            if loop is True:
                self.frame = 0
            elif isinstance(loop, list):
                loop_start, loop_end = loop
                self.frame = sum(self.animation_data.get_frames()[:loop_start+1])
            else:
                self.frame = self.animation_data.duration()

        self.update_image()

    def change_scale(self, scale):
        scale = normalize_scale(scale)
        self.animation_data.resize_images(scale)
        self._frame_lookup = self._generate_frame_lookup()

    def set_center(self, flag: bool):
        self.animation_data.config['centered'] = flag

    @property
    def current_image(self):
        return self.image

    @property
    def over(self):
        return self.frame >= self.animation_data.duration()
