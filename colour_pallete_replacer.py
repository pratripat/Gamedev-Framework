import os, pygame

# CHESS PIECES
# white to black
to_be_replaced = {
    '(234, 212, 170, 255)': (38, 43, 68),
    '(228, 166, 114, 255)': (24, 20, 37),
    '(184, 111, 80, 255)': (24, 20, 37),
    '(184, 110, 80, 255)': (24, 20, 37)
}

# white to black (boss)
# to_be_replaced = {
#     '(234, 212, 170, 255)': (38, 43, 68),
#     '(228, 166, 114, 255)': (24, 20, 37),
#     '(184, 111, 80, 255)': (0, 0, 1),
#     '(184, 110, 80, 255)': (24, 20, 37)
# }

# black to white
# to_be_replaced = {
#     '(38, 43, 68, 255)': (234, 212, 170),
#     '(24, 20, 37, 255)': (228, 166, 114)
# }

# EYES
# to_be_replaced = {
#     '(44, 232, 245, 255)': (254, 230, 97),
#     '(18, 78, 137, 255)': (162, 38, 51)
# }

# PROJECTILES
# to_be_replaced = {
#     '(18, 78, 137, 255)': (162, 38, 51),
#     '(44, 232, 245, 255)': (247, 119, 34)
# }

def ask_filename():
    input_filename = input('Input filename of images: ')
    output_filename = input('Output filename of images: ')
    return input_filename, output_filename

def check_filename(filename):
    return os.path.exists('data/graphics/animations/'+filename)

def make_folder(filename):
    if not check_filename(filename):
        os.makedirs('data/graphics/animations/'+filename)

def change_colors(input_filename, output_filename):
    image = pygame.image.load(f'data/graphics/animations/{input_filename}')

    for x in range(image.get_width()):
        for y in range(image.get_height()):
            pixel_color = image.get_at((x, y))
            color = f'({pixel_color.r}, {pixel_color.g}, {pixel_color.b}, {pixel_color.a})'
            if f'{color}' in to_be_replaced.keys():
                image.set_at((x, y), to_be_replaced[f'{color}'])

    pygame.image.save(image, f'data/graphics/animations/{output_filename}')

def run():
    input_filename, output_filename = ask_filename()
    if not check_filename(input_filename):
        print('\n\n')
        print(f'{input_filename} filename does not exist...')
        run()

    # make_folder(output_filename)

    change_colors(input_filename, output_filename)

    print('done')

run()
