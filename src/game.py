import pygame
import socketio
import menue
pygame.init()

WIDTH = 1500
HEIGHT = 1000
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption('RaceGame')
fps = 60
timer = pygame.time.Clock()



run = True
while run:
    screen.fill('Light blue')
    timer.tick(fps)
    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    connect_button = menue.Button('Connect', 100, 200, screen)
    connect_button.draw()

    pygame.display.flip()

pygame.quit()