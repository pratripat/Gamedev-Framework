import pygame, json
from ..utils import load_image, load_images_from_spritesheet, DEFAULT_COLORKEY, ANIMATION_FOLDER

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
        
        animation_data = self.animations.get(animation_id, None)
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

        self.resize_images(self.config.get("scale", 1))

    def resize_images(self, scale):
        """
        Resize the images based on the scale factor.
        
        :param scale: Scale factor to resize the images.
        """
        if scale == 1: return  # no need to resize if scale is 1

        self.images = [pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale))) for image in self.original_images]

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
        self.load_image()
    
    def load_image(self):
        """
        Load the images for the animation from the animation data according to the current frame.
        """
        images = self.animation_data.get_images()
        frames = self.animation_data.get_frames()
        self_frame = self.frame

        for i, frame in enumerate(frames):
            if self_frame > frame:
                self_frame -= frame
                continue

            self.image = images[i]
            break
    
    def render(self, surface, position, flipped=[False, False], colorkey=DEFAULT_COLORKEY, angle=0, center_rotation=True, alpha=None, animation_offset=None):
        """
        Render the current frame of the animation onto the given surface at the specified position.
        :param surface: The surface to render the animation onto.
        :param position: The position (x, y) where the animation should be rendered.
        :param flipped: A list indicating whether to flip the image horizontally or vertically.
        :param colorkey: The color key for transparency.
        :param angle: The angle to rotate the image.
        :param center_rotation: Whether to center the rotation around the image's center.
        :param alpha: The alpha value for transparency.
        :param animation_offset: An optional offset to apply to the animation position.
        """
    
        offset = [0, 0]
        image = self.image

        if any(flipped):
            image = pygame.transform.flip(self.image, *flipped)
    
        if colorkey != DEFAULT_COLORKEY:
            image.set_colorkey(colorkey)

        if angle != 0:
            image_copy = image.copy()
            image = pygame.transform.rotate(image, angle)

            if center_rotation:
                offset[0] = image_copy.get_width()/2-image.get_width()/2
                offset[1] = image_copy.get_height()/2-image.get_height()/2

        if self.animation_data.config['centered']:
            offset[0] -= image.get_width()//2
            offset[1] -= image.get_height()//2

        if alpha != None:
            alpha_surface = pygame.Surface(image.get_size())
            alpha_surface.convert_alpha()
            alpha_surface.set_colorkey(DEFAULT_COLORKEY)
            alpha_surface.set_alpha(alpha)
            alpha_surface.blit(image, (0, 0))
            image = alpha_surface

        if animation_offset != None:
            offset = animation_offset.copy()

            scale = self.animation_data.config['scale']
            offset[0] *= scale
            offset[1] *= scale

        surface.blit(image, (position[0]+offset[0], position[1]+offset[1]))

    def run(self, event_manager, entity_id, dt):
        """
        Update the animation frame based on the elapsed time.
        :param dt: The elapsed time since the last update.
        """

        if self.frame > self.animation_data.duration():
            event_manager.emit("animation_finished", entity_id=entity_id, animation_id=self.animation_id)

            if self.animation_data.config['loop'] == True:
                self.frame = 0
            elif self.animation_data.config['loop'] == False:
                self.frame = self.animation_data.duration()

        self.frame += self.animation_data.config['speed'] * dt

        if type(self.animation_data.config['loop']) == type([]):
            loop_indexes = self.animation_data.config['loop']

            if self.frame > sum(self.animation_data.config['frames'][:loop_indexes[1]+1]):
                self.frame = sum(self.animation_data.config['frames'][:loop_indexes[0]+1])

        self.load_image()

    def change_scale(self, scale):
        self.animation_data.resize_images(scale)
        self.animation_data.config['scale'] = scale
    
    #The current image
    @property
    def current_image(self):
        return self.image

    @property
    def over(self):
        return self.frame >= self.animation_data.duration()
