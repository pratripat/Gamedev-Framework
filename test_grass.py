import pygame
from scripts.systems.rendering.grass_system import GrassSystem

pygame.init()
screen = pygame.display.set_mode((100, 100))
gs = GrassSystem()
gs.generate_grass({"grass": {(0, 0): {(320, 320): {}}}})

if gs.blades:
    bg = pygame.Surface((100,100)).convert()
    bg.fill((255,0,0)) # Red background
    img = gs.blades[0].image
    bg.blit(img, (10,10))
    pygame.image.save(bg, "test_bg_output.png")
    print("Blitted onto red background.")
