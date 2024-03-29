import sys
import pygame
import socketio
import menue
import road3
import pygame_widgets
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from pygame_widgets.dropdown import Dropdown
from pygame_widgets.toggle import Toggle
pygame.init()

# Setup
gam = road3.GameWindow()
WIDTH = 1024
HEIGHT = 768
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption('RaceGame')
fps = 60
timer = pygame.time.Clock()
font = pygame.font.SysFont('Georgia', 24 , bold=False)
client_id = None
background = pygame.image.load("media/homescreen.jpg").convert_alpha()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))
gametitle = pygame.image.load("media/gametitle.png").convert_alpha()
gametitle = pygame.transform.scale(gametitle, (WIDTH, HEIGHT / 3))

connectmenue = True
menueactive = False
connectEnter = False
settingsactive = False
offlinemode = False
canstart = False
playerready = False
game_start = False


username_input_box = menue.TextInputBox(WIDTH/2, (HEIGHT/2) - 70, 400, font)
input_group = pygame.sprite.Group(username_input_box)

sio = socketio.Client()
username = None
usernames = []
client_ids = {}
is_host = False
hostID = 0

# Settings
road_width_slider = Slider(screen, WIDTH//2 - 150, (HEIGHT//2) - 75, 300, 20, min = 500, max = 3000, step=1, initial=2000)
road_width_label = font.render('Road Width ', True, 'white')
road_width_output = TextBox(screen, road_width_slider.getX() + road_width_label.get_width(), road_width_slider.getY() - 40, 45, 30, fontSize=15)

camera_height_slider = Slider(screen, WIDTH//2 - 150, (HEIGHT//2), 300, 20, min = 500, max = 5000, step=1 , initial=1000)
camera_height_label = font.render('CameraHeight  ', True, 'white')
camera_height_output = TextBox(screen, road_width_slider.getX() + road_width_label.get_width(), camera_height_slider.getY() - 40, 45, 30, fontSize=15)

draw_distance_slider = Slider(screen, WIDTH//2 - 150, (HEIGHT//2) + 75, 300, 20, min = 100, max = 500, step=1, initial=300)
draw_distance_label = font.render('Draw Distance ', True, 'white')
draw_distance_output = TextBox(screen, road_width_slider.getX() + road_width_label.get_width(), draw_distance_slider.getY() - 40, 45, 30, fontSize=15)

fov_slider = Slider(screen, WIDTH//2 - 150, (HEIGHT//2) + 150, 300, 20, min = 80, max = 140, step=1, initial=100)
fov_label = font.render('Field of View ', True, 'white')
fov_output = TextBox(screen, road_width_slider.getX() + road_width_label.get_width(), fov_slider.getY() - 40, 45, 30, fontSize=15)

fog_density_slider = Slider(screen, WIDTH//2 - 150, (HEIGHT//2) + 225, 300, 20, min = 0, max = 50, step=1, initial=5)
fog_density_label = font.render('Fog Density ', True, 'white')
fog_density_output = TextBox(screen, road_width_slider.getX() + road_width_label.get_width(), fog_density_slider.getY() - 40, 45, 30, fontSize=15)

lanes_dropdown = Dropdown(
    screen, 5, road_width_slider.getY()-65, 100, 50, name='Lanes',
    choices=[
        '1 Lane',
        '2 Lanes',
        '3 Lanes',
        '4 Lanes',
    ],
    borderRadius=3, colour=pygame.Color('white'), values=[1, 2, 3, 4], direction='down', textHAlign='left'
)

resolution_dropdown = Dropdown(
    screen, 5, lanes_dropdown.getY()-65, 120, 50, name='Resolution',
    choices=[
        'Low 480x360',
        'Medium 640x480',
        'High 1024x768',
        'Fine 1280x960',
    ],
    borderRadius=3, colour=pygame.Color('white'), values=[[480,360], [640,480], [1024,768], [1280,960]], direction='down', textHAlign='left'
)

fullscreen_label = font.render('Fullscreen ', True, 'white')
fullscreen_toggle = Toggle(screen, resolution_dropdown.getWidth() + 15, resolution_dropdown.getY() - 60, 50, 20)

"""
SockeIO Eventhandler

@sio.connect: Informiert über erfolgreiche Verbindung
@sio.connect_error: Informiert über fehlerhafte Verbindung
@sio.disconnect: Informiert über Trennung der Verbindung
@sio.playersConnected: Informiert über die Verbindung anderer Spieler und speichert diese ins Dictionary 'usernames'
"""
@sio.event
def connect():
    """
    This method is called by the server to inform the client about a successful connection
    """
    print("I'm connected! ")

@sio.event
def getPlayerID(socket_id):
    """
    This event is called by the server to send the current client id to the client
    """
    global client_id
    client_id = socket_id

@sio.event
def getHostID(host_id):
    """
    This event is called by the server to send the current host id to the client
    """
    global is_host, hostID
    hostID = host_id
    if host_id == client_id:
        is_host = True
    else:
        is_host = False

@sio.event
def connect_error(data):
    """
    This event is called when a connection error occurs.
    """
    print("The connection failed!")

@sio.event
def disconnect():
    """
    This event is called when the server disconnects the client
    """
    print("I'm disconnected!")
    global menueactive
    global connectmenue
    menueactive = True
    connectmenue = False

@sio.event()
def playersConnected(data):
    """
    This event is called when a new player connects to the server. \n
    The client saves usernames and clientids
    """
    print("PLAYER CONNECTED")
    global usernames
    global client_id
    global client_ids
    usernames = []

    for key in data:
        usernames.append(data[key])
    
    client_ids = data

    print('Updated Users:', usernames)

@sio.event
def all_players_ready(data):
    """
    Server sends this event when all players are ready
    """
    global canstart
    canstart = data

@sio.event
def start():
    """
    Start the game when the server sends start event
    """
    global game_start
    game_start = True



# Gameloop für das Ausführen des Programms
run = True
while run:

    screen.blit(background,(0,0))
    screen.blit(gametitle, (80, 0))
    timer.tick(fps)

    # Eventlistener
    events = pygame.event.get()
    mouseclick = False
    for event in events:
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouseclick = True


    # Der User muss sich mit dem Server Connecten und ist somit im Login Screen.
    if connectmenue:
        input_group.draw(screen)
        input_group.update(events)

        connect_button = menue.Button('Connect', WIDTH/2, HEIGHT/2, screen)
        connect_button.draw()
        # Prüft ob der User den Connect-Button gedrückt hat oder das Eingabefeld durch Enter bestätigt hat
        if connect_button.button.collidepoint(pygame.mouse.get_pos()) and mouseclick or username_input_box.enterpressed:
            connectmenue = False
            username_input_box.enterpressed = False
            username = username_input_box.text
            try:
                sio.connect('http://35.246.239.15:3000/', headers={'username': username})
                pygame.time.delay(1000)
            except Exception as ex:
                print("Verbindungsfehler")
            # Wenn die Verbindung erfolgreich war, geht es ins Hauptmenü.
            # Andernfalls wird der User über die fehlerhafte Verbindung informiert und geht zurück in den Login Screen.
            if sio.connected:
                menueactive = True
                offlinemode = False
                mouseclick = False
            else:
                screen.fill('light blue')
                status = font.render('Connection failed ', True, 'red')
                screen.blit(status, (connect_button.button.midleft[0], connect_button.button.midleft[1] - 15))
                pygame.display.flip()
                pygame.time.delay(1000)
                menueactive = True
                offlinemode = True
                is_host = True
                mouseclick = False
                events = None
    # Der User ist im Hauptmenü.
    if menueactive:
        # Zeichnet alle User die Online sind, oben links in die Ecke
        if not offlinemode:
            status = font.render('Connected to Server ', True, 'black')
            screen.blit(status, (0,0))
            i = 25
            for userID, uservalue in client_ids.items():
                if userID == hostID:
                    online = font.render(uservalue + ' Online ' + 'Host', True, 'green')
                else:
                    online = font.render(uservalue + ' Online', True, 'green')
                screen.blit(online, (0, i))
                i += 25
        else:
            status = font.render('Offlinemode ', True, 'red')
            screen.blit(status, (0, 0))
            reconnect_button = menue.Button('Reconnect', WIDTH / 2, (HEIGHT / 2) + 130, screen)
            reconnect_button.draw()

            if reconnect_button.button.collidepoint(pygame.mouse.get_pos()) and mouseclick:
                menueactive = False
                offlinemode = False
                connectmenue = True
                mouseclick = False
                username_input_box.enterpressed = True

        if offlinemode or len(client_ids) <=1 or is_host and canstart:
            start_button = menue.Button('Start', WIDTH/2, (HEIGHT/2) - 65, screen, 'green')
        elif offlinemode or is_host:
            start_button = menue.Button('Start', WIDTH / 2, (HEIGHT / 2) - 65, screen, 'red')
        elif not playerready:
            start_button = menue.Button('Not Ready', WIDTH/2, (HEIGHT/2) - 65, screen, 'red')
        else:
            start_button = menue.Button('Ready', WIDTH / 2, (HEIGHT / 2) - 65, screen, 'green')
        start_button.draw()
        settings_button = menue.Button('Settings', WIDTH / 2, HEIGHT / 2, screen)
        settings_button.draw()
        quit_button = menue.Button('Quit', WIDTH / 2, (HEIGHT/2) + 65, screen)
        quit_button.draw()

        # Prüft die Betätigung der Hauptmenü-Buttons.
        if start_button.button.collidepoint(pygame.mouse.get_pos()) and mouseclick or game_start:
            if canstart or len(client_ids) <= 1 or game_start:
                if resolution_dropdown.getSelected() is not None:
                    WIDTH = resolution_dropdown.getSelected()[0]
                    HEIGHT = resolution_dropdown.getSelected()[1]
                    screen = pygame.display.set_mode((WIDTH, HEIGHT))
                if fullscreen_toggle.getValue() and resolution_dropdown.getSelected()[0] != 480:
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)

                gam.run(sio, offlinemode, client_id, client_ids, is_host, username)
                game_start = False
                playerready = False
                canstart = False
                mouseclick = False
                sio.emit('player_ready', playerready)
                sio.emit('updateUserList')

            elif not is_host:
                sio.emit('player_ready', not playerready)
                playerready = not playerready

        elif settings_button.button.collidepoint(pygame.mouse.get_pos()) and mouseclick and not connectmenue:
            settingsactive = True
            menueactive = False
            mouseclick = False
        elif quit_button.button.collidepoint(pygame.mouse.get_pos()) and mouseclick:
            run = False

    if settingsactive:
        screen.blit(fullscreen_label, (5, fullscreen_toggle.getY()))

        screen.blit(road_width_label, (5, road_width_slider.getY()))
        road_width_output.disable()
        road_width_output.setText(road_width_slider.getValue())

        screen.blit(camera_height_label, (5, camera_height_slider.getY()))
        camera_height_output.disable()
        camera_height_output.setText(camera_height_slider.getValue())

        screen.blit(draw_distance_label, (5, draw_distance_slider.getY()))
        draw_distance_output.disable()
        draw_distance_output.setText(draw_distance_slider.getValue())

        screen.blit(fov_label, (5, fov_slider.getY()))
        fov_output.disable()
        fov_output.setText(fov_slider.getValue())

        screen.blit(fog_density_label, (5, fog_density_slider.getY()))
        fog_density_output.disable()
        fog_density_output.setText(fog_density_slider.getValue())
        pygame_widgets.update(events)

        save_button = menue.Button('Save', WIDTH / 2, fog_density_slider.getY() + 100, screen)
        save_button.draw()
        if save_button.button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            road3.road_width = road_width_slider.getValue()
            road3.camera_height = camera_height_slider.getValue()
            road3.draw_distance = draw_distance_slider.getValue()
            road3.field_of_view = fov_slider.getValue()
            road3.fog_density = fog_density_slider.getValue()
            if lanes_dropdown.getSelected() is not None: road3.lanes = lanes_dropdown.getSelected()
            if resolution_dropdown.getSelected() is not None:
                road3.hud_scale = resolution_dropdown.getSelected()[0] / road3.window_width
                print(road3.hud_scale)
                gam.font = pygame.font.SysFont('Georgia', (int) (24 * road3.hud_scale), bold=False)
                road3.window_width = resolution_dropdown.getSelected()[0]
                road3.window_height = resolution_dropdown.getSelected()[1]
                gam.hud = pygame.Surface((road3.window_width, road3.window_height), pygame.SRCALPHA)
            menueactive = True
            settingsactive = False

    pygame.display.flip()

sio.disconnect()
pygame.quit()
sys.exit()

