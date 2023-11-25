import pygame
import socketio
pygame.init()

WIDTH = 500
HEIGHT = 500
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption('RaceGame')
fps = 60
timer = pygame.time.Clock()

font = pygame.font.Font('freesansbold.ttf', 24)

run = True
while run:
    screen.fill('Light blue')
    timer.tick(fps)
    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.flip()
pygame.quit()