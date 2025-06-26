import pygame, json
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
    
    def render(self, surface, position, flipped=[False, False], colorkey=DEFAULT_COLORKEY, angle=0, center_rotation=True, alpha=None, animation_offset=None, scale=None, tint=None):
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
    
        offset = self.animation_data.config["offset"].copy()
        image = self.image

        # 1. Flip
        if any(flipped):
            image = pygame.transform.flip(image, *flipped)

        # 2. Colorkey (before alpha so alpha surface inherits it)
        if colorkey != DEFAULT_COLORKEY:
            image.set_colorkey(colorkey)

        # 3. Rotation (must come before scale, or it affects result shape)
        if angle != 0:
            image_copy = image.copy()
            image = pygame.transform.rotate(image, angle)
            
            if center_rotation:
                offset.x = image_copy.get_width() / 2 - image.get_width() / 2
                offset.y = image_copy.get_height() / 2 - image.get_height() / 2

        # 4. Apply alpha transparency
        if alpha is not None:
            alpha_surface = pygame.Surface(image.get_size(), pygame.SRCALPHA)
            alpha_surface.set_colorkey(DEFAULT_COLORKEY)
            alpha_surface.set_alpha(alpha)
            alpha_surface.blit(image, (0, 0))
            image = alpha_surface
        
        if tint is not None:
            # mask = pygame.mask.from_surface(image)
            # image = mask.to_surface()

            image = image.convert_alpha()

            # Create a white surface with the same size
            white_overlay = pygame.mask.from_surface(image).to_surface()

            # Create a copy of the sprite, clear its color data
            silhouette = image.copy()
            silhouette.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MULT)

            silhouette.set_colorkey(DEFAULT_COLORKEY)

            # Add white to the transparent base, generating the silhouette
            silhouette.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

            image = silhouette

        # 5. Determine scale
        scale = normalize_scale(scale) if scale is not None else normalize_scale(1)

        # 6. Apply scale (after rotation/alpha to preserve proportions)
        if scale != [1, 1]:
            image = pygame.transform.scale(image, (
                int(image.get_width() * scale[0]),
                int(image.get_height() * scale[1])
            ))

        # 7. Override offset (if manually supplied)
        if animation_offset is not None:
            offset = animation_offset.copy()
    

        # 8. Apply final scale to offset
        offset.x *= scale[0]
        offset.y *= scale[1]

        # 9. Center alignment
        if self.animation_data.config.get("centered", False):
            offset.x -= image.get_width() // 2
            offset.y -= image.get_height() // 2

        # 10. Final render
        surface.blit(image, (position[0] + offset.x, position[1] + offset.y))

    def run(self, event_manager, entity_id, dt):
        """
        Update the animation frame based on the elapsed time.
        :param dt: The elapsed time since the last update.
        """

        if self.frame > self.animation_data.duration():
            try:
                event_manager.emit(GameSceneEvents.ANIMATION_FINISHED, entity_id=entity_id, animation_id=self.animation_id)
            except Exception as e:
                # print("[ANIMATION] Error emitting ANIMATION_FINISHED event:", e, "(DEBUG)")
                pass

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
        scale = normalize_scale(scale)
        self.animation_data.resize_images(scale)
        self.animation_data.config['scale'] = scale
    
    def set_center(self, bool):
        self.animation_data.config['centered'] = bool

    #The current image
    @property
    def current_image(self):
        return self.image

    @property
    def over(self):
        return self.frame >= self.animation_data.duration()
