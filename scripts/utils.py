import pygame, json, os

DEFAULT_COLORKEY = (0, 0, 0)
INTIAL_WINDOW_SIZE = (800, 600)
ANIMATION_FOLDER = "data/graphics/animations"
SCALE = 3

# loads an image from a file and applies a colorkey for transparency
def load_image(path, colorkey=DEFAULT_COLORKEY, scale=1):
    """
    Load an image from a file and apply a colorkey for transparency.
    
    :param path: Path to the image file.
    :param colorkey: Color to be treated as transparent.
    :param scale: Scale factor for the image.
    :return: Scaled image with colorkey applied.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"[UTILS] Image file '{path}' does not exist. (DEBUG)")
    
    image = pygame.image.load(path).convert()
    image.set_colorkey(colorkey)
    
    if scale != 1:
        width, height = image.get_size()
        image = pygame.transform.scale(image, (width * scale, height * scale))
    
    return image

def load_images_from_spritesheet(file_path, colorkey=DEFAULT_COLORKEY, scale=1):
    """
    Load images from a spritesheet file, extracting individual images based on color markers.
    The spritesheet is expected to have specific color markers to define the start and end of images.
    :param file_path: Path to the spritesheet file.
    :param colorkey: Color to be treated as transparent for the images.
    :param scale: Scale factor for the images.
    :return: List of images extracted from the spritesheet.
    """
    # Tries to load the file
    try:
        spritesheet = load_image(file_path, colorkey, scale)
    except Exception as e:
        print(f"[UTILS] Error loading spritesheet '{file_path}': {e} (DEBUG)")
        return []

    rows = []
    images = []

    for y in range(spritesheet.get_height()):
        pixil = spritesheet.get_at((0, y))
        if pixil[2] == 255:
            rows.append(y)

    for row in rows:
        for x in range(spritesheet.get_width()):
            start_position = []
            pixil = spritesheet.get_at((x, row))
            if pixil[0] == 255 and pixil[1] == 255 and pixil[2] == 0:
                start_position = [x+1, row]
                width = height = 0

                for rel_x in range(start_position[0], spritesheet.get_width()):
                    pixil = spritesheet.get_at((rel_x, start_position[1]))
                    if pixil[0] == 255 and pixil[1] == 0 and pixil[2] == 255:
                        width = rel_x - start_position[0]
                        break

                for rel_y in range(start_position[1], spritesheet.get_height()):
                    pixil = spritesheet.get_at((start_position[0], rel_y))
                    if pixil[0] == 255 and pixil[1] == 0 and pixil[2] == 255:
                        height = rel_y - start_position[1]
                        break

                image = pygame.Surface((width, height))
                image.set_colorkey(colorkey)
                image.blit(spritesheet, (-start_position[0], -start_position[1]))
                image.convert()

                if scale != 1:
                    image = pygame.transform.scale(image, (image.get_width()*scale, image.get_height()*scale))

                images.append(image)

    return images
