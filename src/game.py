import pygame
import socketio
import menue
pygame.init()

WIDTH = 1280
HEIGHT = 960
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption('RaceGame')
fps = 60
timer = pygame.time.Clock()
font = pygame.font.SysFont('Georgia', 24, bold=False)

connectmenue = True
menueactive = False

sio = socketio.Client()

sio.connect('http://3.71.101.250:3000/')
@sio.event
def connect():
    print("I'm connected!")
@sio.event
def connect_error(data):
    print("The connection failed!")

@sio.event
def disconnect():
    print("I'm disconnected!")

run = True
while run:
    screen.fill('light blue')
    timer.tick(fps)
    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    if connectmenue:
        connect_button = menue.Button('Connect', WIDTH/2, HEIGHT/2, screen)
        connect_button.draw()

        if connect_button.button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] == True:
            connectmenue = False
            menueactive = True
    if menueactive:
        status = font.render('Connected to Server ', True, 'black')
        screen.blit(status, (0,0))


    pygame.display.flip()

sio.disconnect()
pygame.quit()

