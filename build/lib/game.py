import sys
import pygame
import socketio
import menue
import road3
pygame.init()

gam = road3.GameWindow()
WIDTH = 1024
HEIGHT = 768
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption('RaceGame')
fps = 60
timer = pygame.time.Clock()
font = pygame.font.SysFont('Georgia', 24, bold=False)

connectmenue = True
menueactive = False
connectEnter = False
settingsactive = False
offlinemode = False

username_input_box = menue.TextInputBox(WIDTH/2, (HEIGHT/2) - 70, 400, font)
input_group = pygame.sprite.Group(username_input_box)

sio = socketio.Client()
username = None
usernames = None

"""
SockeIO Eventhandler

@sio.connect: Informiert über erfolgreiche Verbindung
@sio.connect_error: Informiert über fehlerhafte Verbindung
@sio.disconnect: Informiert über Trennung der Verbindung
@sio.playersConnected: Informiert über die Verbindung anderer Spieler und speichert diese ins Dictionary 'usernames'
"""
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
    print("PLAYER CONNECTED")
    global usernames
    usernames = data['usernames']
    print('Updated Users:', usernames)

# Gameloop für das Ausführen des Programms
run = True
while run:
    screen.fill('blue')
    timer.tick(fps)

    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            run = False


    # Der User muss sich mit dem Server Connecten und ist somit im Login Screen.
    if connectmenue:
        input_group.draw(screen)

        input_group.update(events)

        connect_button = menue.Button('Connect', WIDTH/2, HEIGHT/2, screen)
        connect_button.draw()
        # Prüft ob der User den Connect-Button gedrückt hat oder das Eingabefeld durch Enter bestätigt hat
        if connect_button.button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] or username_input_box.enterpressed:
            connectmenue = False
            username_input_box.enterpressed = False
            username = username_input_box.text
            try:
                sio.connect('http://3.71.101.250:3000/', headers={'username': username})
                pygame.time.delay(1000)
            except Exception as ex:
                print("Verbindungsfehler")
            # Wenn die Verbindung erfolgreich war, geht es ins Hauptmenü.
            # Andernfalls wird der User über die fehlerhafte Verbindung informiert und geht zurück in den Login Screen.
            if sio.connected:
                menueactive = True
                offlinemode = False
            else:
                screen.fill('light blue')
                print("1")
                status = font.render('Connection failed ', True, 'red')
                screen.blit(status, (connect_button.button.midleft[0], connect_button.button.midleft[1] - 15))
                pygame.display.flip()
                #pygame.time.delay(3000)
                menueactive = True
                offlinemode = True
    # Der User ist im Hauptmenü.
    if menueactive:
        # Zeichnet alle User die Online sind, oben links in die Ecke
        if not offlinemode:
            status = font.render('Connected to Server ', True, 'black')
            screen.blit(status, (0,0))
            i = 25
            for users in usernames:
                online = font.render(users + ' Online', True, 'green')
                screen.blit(online, (0, i))
                i += 25
        else:
            status = font.render('Offlinemode ', True, 'red')
            screen.blit(status, (0, 0))
            reconnect_button = menue.Button('Reconnect', WIDTH / 2, (HEIGHT / 2) + 130, screen)
            reconnect_button.draw()

            if reconnect_button.button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                menueactive = False
                offlinemode = False
                connectmenue = True
                username_input_box.enterpressed = True

        start_button = menue.Button('Start', WIDTH/2, (HEIGHT/2) - 65, screen)
        start_button.draw()
        settings_button = menue.Button('Settings', WIDTH / 2, HEIGHT / 2, screen)
        settings_button.draw()
        quit_button = menue.Button('Quit', WIDTH / 2, (HEIGHT/2) + 65, screen)
        quit_button.draw()

        # Prüft die Betätigung der Hauptmenü-Buttons.
        if start_button.button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            #with open("road3.py") as f:
                #exec(f.read())
            gam.run()

        if settings_button.button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            settingsactive = True
        if quit_button.button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            run = False

    if settingsactive:
        pass

    pygame.display.flip()

sio.disconnect()
pygame.quit()
sys.exit()

