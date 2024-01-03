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

gam = road3.GameWindow()
WIDTH = 1024
HEIGHT = 768
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption('RaceGame')
fps = 60
timer = pygame.time.Clock()
font = pygame.font.SysFont('Georgia', 24, bold=False)
client_id = None

connectmenue = True
menueactive = False
connectEnter = False
settingsactive = False
offlinemode = False

username_input_box = menue.TextInputBox(WIDTH/2, (HEIGHT/2) - 70, 400, font)
input_group = pygame.sprite.Group(username_input_box)

sio = socketio.Client()
username = None
usernames = []
client_ids = {}
is_host = False

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
    print("I'm connected! ")

@sio.event
def getPlayerID(socket_id):
    global client_id
    client_id = socket_id

@sio.event
def getHostID(host_id):
    global is_host
    if host_id == client_id:
        is_host = True
    else:
        is_host = False

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
    global client_id
    global client_ids
    usernames = []

    for key in data:
        usernames.append(data[key])
    
    client_ids = data

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
                sio.connect('http://35.246.239.15:3000/', headers={'username': username})
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
                status = font.render('Connection failed ', True, 'red')
                screen.blit(status, (connect_button.button.midleft[0], connect_button.button.midleft[1] - 15))
                pygame.display.flip()
                #pygame.time.delay(3000)
                menueactive = True
                offlinemode = True
                is_host = True
                events = None
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
            if resolution_dropdown.getSelected() is not None:
                WIDTH = resolution_dropdown.getSelected()[0]
                HEIGHT = resolution_dropdown.getSelected()[1]
                screen = pygame.display.set_mode((WIDTH, HEIGHT))
            if fullscreen_toggle.getValue() and resolution_dropdown.getSelected()[0] != 480:
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)

#############################################################################################################################################
#############################################################################################################################################
            gam.run(sio, offlinemode, client_id, client_ids, is_host)
#############################################################################################################################################
#############################################################################################################################################
            
        elif settings_button.button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] and events is not None:
            settingsactive = True
            menueactive = False
        elif quit_button.button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
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
                road3.window_width = resolution_dropdown.getSelected()[0]
                road3.window_height = resolution_dropdown.getSelected()[1]
            menueactive = True
            settingsactive = False

    pygame.display.flip()

sio.disconnect()
pygame.quit()
sys.exit()

