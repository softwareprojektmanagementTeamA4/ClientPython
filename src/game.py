import pygame
import socketio
import menue
import json
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
connectEnter = False

sio = socketio.Client()
username = None

@sio.event
def connect():
    print("I'm connected! ")

@sio.event
def connect_error(data):
    print("The connection failed!")

@sio.event
def disconnect():
    print("I'm disconnected!")
    global menueactive
    global connectmenue
    menueactive = False
    connectmenue = True

@sio.event()
def playersConnected(data):
    playerinfo = json.load(data)
    online = font.render(playerinfo['usernames'] + ' Online', True, 'green')
    screen.blit(online, (screen.get_rect().x, screen.get_rect().y + 25))

username_input_box = menue.TextInputBox(WIDTH/2, (HEIGHT/2) - 70, 400, font)
input_group = pygame.sprite.Group(username_input_box)

run = True
while run:
    screen.fill('blue')
    timer.tick(fps)

    input_group.update(pygame.event.get())
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    if connectmenue:
        input_group.draw(screen)

        connect_button = menue.Button('Connect', WIDTH/2, HEIGHT/2, screen)
        connect_button.draw()

        if connect_button.button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] == True or username_input_box.enterpressed:
            connectmenue = False
            username = username_input_box.text
            try:
                sio.connect('http://3.71.101.250:3000/', headers={'username': username})
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
        online = font.render(username + ' Online', True, 'green')
        screen.blit(online, (screen.get_rect().x, screen.get_rect().y + 25))

        start_button = menue.Button('Start', WIDTH/2, (HEIGHT/2) - 65, screen)
        start_button.draw()
        settings_button = menue.Button('Settings', WIDTH / 2, HEIGHT / 2, screen)
        settings_button.draw()
        quit_button = menue.Button('Quit', WIDTH / 2, (HEIGHT/2) + 65, screen)
        quit_button.draw()

        if start_button.button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] == True:
            ## Starte das Spiel
            pass
        if settings_button.button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] == True:
            ## Zeige die Einstellungen
            pass
        if quit_button.button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] == True:
            run = False

    pygame.display.flip()

sio.disconnect()
pygame.quit()

