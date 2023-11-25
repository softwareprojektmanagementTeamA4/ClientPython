import socket
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

sio = socketio.Client(logger=True, engineio_logger=True)

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
            try:
                sio.connect('http://3.71.101.250:3000/')
            except Exception as ex:
                print("Verbindungsfehler")

            if sio.connected:
                menueactive = True
            else:
                screen.fill('light blue')
                status = font.render('Connection failed ', True, 'red')
                screen.blit(status, (connect_button.button.midleft[0], connect_button.button.midleft[1] - 15))
                pygame.display.flip()
                pygame.time.delay(3000)
                connectmenue = True
    if menueactive:
        status = font.render('Connected to Server ', True, 'black')
        screen.blit(status, (0,0))


    pygame.display.flip()

sio.disconnect()
pygame.quit()

