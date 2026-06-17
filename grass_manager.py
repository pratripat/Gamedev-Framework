import pygame, sys, random, math

FILENAME = 'grass_spritesheet.png'
COLORS = [(25,60,62), (38,92,66), (62,137,72), (100,199,77)]

def load_images_from_spritesheet(filename):
    #Tries to load the file
    try:
        spritesheet = pygame.image.load(filename)
    except:
        print('file not found...')
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
                start_position = [x+1, row+1]
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
                image.set_colorkey((0,0,0))
                image.blit(spritesheet, (-start_position[0], -start_position[1]))

                images.append(image)

    return images

def edit_image(image, scale, color, flip):
    image.set_colorkey((255,255,255))
    image = pygame.transform.flip(image, *flip)
    surface = pygame.Surface(image.get_size())
    surface.fill(color)
    surface.blit(image, (0,0))
    surface.set_colorkey((0,0,0))

    return pygame.transform.scale(surface, (int(surface.get_width()*scale), int(surface.get_height()*scale)))

GRASS_IMAGES = load_images_from_spritesheet(FILENAME)
calculated_distances = {}

class Grass_Manager:
    def __init__(self, scale=2):
        self.grass_blades = []
        self.grass_blades_group = pygame.sprite.Group()
        self.scale = scale
        self.wind = 0
        self.wind_timer = 0

    def spawn_blades(self, positions):
        for position in positions:
            grass_blade = Grass_Blade(position, self.scale)
            self.grass_blades.append(grass_blade)
            self.grass_blades_group.add(grass_blade)

    def render(self, screen, scroll=[0,0]):
        for blade in self.grass_blades:
            blade.render(screen, scroll)

    def update(self, dt, game_timer):
        # for blade in self.grass_blades:
        #     blade.update(dt, self.wind, game_timer)
        self.grass_blades_group.update(dt, self.wind, game_timer)

        if self.wind_timer == 0 and self.wind == 0 and random.random() > 0.999:
            self.wind = random.randrange(5, 12) * random.choice([-1, 1])
            self.wind_timer = random.randrange(1, 6)

        if self.wind_timer > 0:
            self.wind_timer -= dt
            if self.wind_timer <= 0:
                self.wind_timer = 0

        if self.wind != 0 and random.random() > 0.99:
            self.wind -= self.wind * random.uniform(0.05, 0.4) * 80 * dt
            if abs(self.wind) < 0.1:
                self.wind = 0

    def collide(self, rect):
        for blade in self.grass_blades:
            blade.collide(rect)

    def clear_cache(self):
        for blade in self.grass_blades:
            blade.calculated_distances.clear()

class Grass_Blade(pygame.sprite.Sprite):
    def __init__(self, position, scale):
        super().__init__()
        self.position = position
        self.scale = scale*random.uniform(0.7,1)
        self.image = random.choice(GRASS_IMAGES).convert()
        self.color = random.choice(COLORS)
        self.target_angle = self.angle = -math.pi/2
        self.angle_offset = random.randrange(-10, 10)

        self.image = edit_image(self.image, self.scale, self.color, [random.choice([0,1]), False])
        self.position[1] -= self.image.get_height()/2
        self.rect = pygame.Rect(*self.position, *self.image.get_size())

    def render(self, screen, scroll=[0,0]):
        rotated_image = pygame.transform.rotate(self.image, self.angle+self.angle_offset)

        screen.blit(rotated_image, (self.position[0]+self.image.get_width()/2-rotated_image.get_width()/2-scroll[0], self.position[1]+self.image.get_height()/2-rotated_image.get_height()/2-scroll[1]))

    def update(self, dt, wind, game_timer):
        self.angle += (self.target_angle - self.angle) / 3 * 80 * dt
        self.target_angle += (-math.pi/2 - self.target_angle) / 3 * 80 * dt

        if wind != 0:
            self.target_angle += wind * 80 * dt
            self.angle += math.sin(game_timer/(wind*random.randrange(5,7))) * random.randrange(2,4) * 80 * dt

        self.angle = min(self.angle, 80)
        self.angle = max(self.angle, -80)

    def collide(self, rect):
        if abs(rect.bottom-self.position[1]) < self.image.get_height():
            rect_position = [rect.center[0], rect.bottom]
            distance = (rect_position[0]-self.center[0])**2+(rect_position[1]-self.center[1])**2
            direction = rect_position[0]-self.center[0]

            if distance < (rect[2]**2+rect[3]**2)/2:
                if distance in calculated_distances.keys():
                    self.target_angle = calculated_distances[distance]
                else:
                    if direction <= 0:
                        target = -70 - direction * 0.3
                    else:
                        target = 70 - direction * 0.3

                    self.target_angle = min(self.target_angle+target, 80)
                    self.target_angle = max(self.target_angle, -80)

                    calculated_distances[distance] = self.target_angle

    @property
    def center(self):
        return [self.position[0] + self.image.get_width()/2, self.position[1]]

if __name__ == '__main__':
    screen = pygame.display.set_mode((1000, 700))

    clock = pygame.time.Clock()

    print(clock.get_fps())

    grass_manager = Grass_Manager(3)
    grass_manager.spawn_blades([[300+x+x*3, 400] for x in range(100)])

    game_timer = 0
    rect = pygame.Rect(0,350,50,50)

    pygame.mouse.set_visible(False)

    while True:
        game_timer += 1

        clock.tick()

        print(clock.get_fps())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEMOTION:
                calculated_distances.clear()
                rect[0] = event.pos[0]

        screen.fill((0,0,0))

        grass_manager.collide(rect)
        grass_manager.update(1/(clock.get_fps()+0.000001), game_timer)

        pygame.draw.rect(screen, (255,255,255), rect, 1)

        grass_manager.render(screen)

        pygame.display.update()
