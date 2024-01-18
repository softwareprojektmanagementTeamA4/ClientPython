import sys
import os
from util import *
from sprites import *
from threading import Lock

src_path = os.path.dirname(__file__)


fps = 60                           # how many updates per second
step = 1/fps                       # how long is each frame
window_width = 1024                # logical window width
window_height = 768                # logical window height
centrifugal_force = 0.3            # centrifugal force multiplier when going around curves
offRoadDecel = 0.99                # speed multiplier when off road (e.g. you lose 2% speed each update frame)
sky_speed  = 0.001                  # background sky layer scroll speed when going around curve (or up hill)
hill_speed = 0.002                 # background hill layer scroll speed when going around curve (or up hill)
tree_speed = 0.003                 # background tree layer scroll speed when going around curve (or up hill)
sky_offset = 0                     # current sky scroll offset
hill_offset = 0                    # current hill scroll offset
tree_offset = 0                    # current tree scroll offset
segments = []                      # array of road segments
cars = []                          # array of cars on the road
npc_car_lock = Lock()              # lock for adding cars to segments
client_ids = {}                    # dict of other players
player_start_positions = []        # array of player cars
player_car_lock = Lock()           # lock for adding cars to segments
player_cars = {}                   # array of player cars
player_num = 1                     # player number
# background = None                # our background image (loaded below)
sprites = None                     # our spritesheet (loaded below)
resolution = None                  # scaling factor for multi-resolution support
road_width = 2000                  # actually half the roads width, easier math if the road spans from -roadWidth to +roadWidth
segment_length = 200               # length of a single segment
rumble_length = 3                  # number of segments per red/white rumble strip
track_length = None                # z length of entire track (computed)
lanes = 3                          # number of lanes
field_of_view = 100                # angle (degrees) for field of view
camera_height = 1000               # z height of camera
camera_depth = None                # z distance camera is from screen (computed)
draw_distance = 300                # number of segments to draw
playerX = 0                       # player x offset from center of road (-1 to 1 to stay independent of roadWidth)
playerZ = None                    # player relative z distance from camera (computed)
fog_density = 5                    # exponential fog density
position = 1                     # current camera Z position (add playerZ to get player's absolute Z position)
speed = 0                          # current speed
max_speed = segment_length/step    # top speed (ensure we can't move more than 1 segment in a single frame to make collision detection easier)
accel =  max_speed/5               # acceleration rate - tuned until it 'felt' right
breaking = -max_speed              # deceleration rate when braking
decel = -max_speed/5               # 'natural' deceleration rate when neither accelerating, nor braking
off_road_decel = -max_speed/2      # off road deceleration is somewhere in between
off_road_limit = max_speed/4       # limit when off road deceleration no longer applies (e.g. you can always go at least this speed even when off road)
total_cars = 100                   # total number of cars on the road
current_lap_time = 0               # current lap time
last_lap_time = 0               # last lap time
current_lap = 0
maxlap = 0
path_background_sky = "background/sky.png"
path_background_hills = "background/hills.png"
path_background_trees = "background/trees.png"
path_nitro_bottle = "media/nitro.png"
path_nitro_empty_bottle = "media/nitro_empty.png"
max_nitro = 100
nitro = 100
nitro_recharging = False
nitro_is_on = False
place = 1
finished_players = []
game_finished = False
hud_scale = 1


#########################################################
road_length = 500                 # length of our road
#########################################################

# TODO: implement hud

# class Segment:
#     """
#     Segment of road
#     """
#     def __init__(self, index, p1, p2, color):
#         self.index = index
#         self.p1 = p1
#         self.p2 = p2
#         self.color = color
    
class GameWindow:
    def __init__(self):
        self.global_delta_time = 0
        self.delta_time = 0
        self.time_now = None
        self.last_time = Util.timestamp()
        pygame.init()
        pygame.display.set_caption('Road3')
        self.surface = pygame.display.set_mode((window_width, window_height))
        self.font = pygame.font.SysFont('Georgia', 24, bold=False)
        self.hud = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        self.clock = pygame.time.Clock()
        self.username = 'unknown'

        self.background_sky = pygame.image.load(path_background_sky).convert_alpha()
        self.background_hills = pygame.image.load(path_background_hills).convert_alpha()
        self.background_trees = pygame.image.load(path_background_trees).convert_alpha()

        self.background = pygame.Surface((window_width, window_height))

    def run(self, sio, offlinemode, id, client_ids_server, is_host, username):
        """
        Main game loop
        """
        global client_ids
        client_ids = client_ids_server
        self.sio = sio
        self.offlinemode = offlinemode
        self.id = id
        self.is_host = is_host
        self.game_is_loaded = False
        self.username = username

        def update(delta_time):
            """
            Update current game state
            """
            global position, speed, playerX, playerZ, sky_offset, hill_offset, tree_offset, max_nitro, nitro, nitro_recharging, nitro_is_on
            global client_ids

            player_segment = find_segment(position + playerZ)
            playerW = sprite_list['1_PLAYER_STRAIGHT']['w'] * SPRITE_SCALE
            speed_percent = speed/max_speed
            dx = delta_time * 2 * speed_percent
            start_position = position

            if is_host:
                update_cars(delta_time, player_segment, playerW)

            position = Util.increase(position, delta_time * speed, track_length)
            
            sky_offset  = Util.increase(sky_offset, sky_speed * player_segment['curve'] * (position - start_position)/segment_length, 1)
            hill_offset = Util.increase(hill_offset, hill_speed * player_segment['curve'] * (position - start_position)/segment_length, 1)
            tree_offset = Util.increase(tree_offset, tree_speed * player_segment['curve'] * (position - start_position)/segment_length, 1)

            # input handling
            keys = pygame.key.get_pressed()
            global game_finished
            if not game_finished:
                if keys[pygame.K_LEFT]:     # drive left
                    playerX -= dx
                if keys[pygame.K_RIGHT]:    # drive right
                    playerX += dx

                playerX = playerX - (dx * speed_percent * player_segment['curve'] * centrifugal_force) # steering is harder when going around curves

                if keys[pygame.K_UP]:       # go faster
                    speed = Util.accelerate(speed, accel, delta_time)
                elif keys[pygame.K_DOWN]:   # slow down
                    speed = Util.accelerate(speed, breaking, delta_time)
                else:                       # slow down if not pressing forward or backward
                    speed = Util.accelerate(speed, decel, delta_time)

                if keys[pygame.K_SPACE]:
                    if nitro <= 0:
                        nitro_recharging = True
                    elif not nitro_recharging and speed > 0:
                        nitro_is_on = True
                        speed = Util.accelerate(speed, accel * 2.5, delta_time)  # 2,5x so schnell Beschleunigen
                        nitro -= 1
                else:
                    nitro_is_on = False
                if nitro_recharging:
                    nitro_is_on = False
                    nitro += 0.0625 
                    nitro = min(nitro, max_nitro) 
                    nitro_recharging = nitro < max_nitro
            else:
                if keys[pygame.K_q]:
                    if (len(finished_players) == len(player_start_positions)):
                        self.game_is_loaded = False


            # Esc key to quit
            if keys[pygame.K_ESCAPE]:
                pygame.quit()
                sys.exit()

            if (playerX < -1) or (playerX > 1):
                if speed > off_road_limit:
                    speed = Util.accelerate(speed, off_road_decel, delta_time) # driving off road slows you down

                for n in range(len(player_segment['sprites'])):
                    sprite = player_segment['sprites'][n]
                    spriteW = sprite['source'][1]['w'] * SPRITE_SCALE
                    x2 = sprite['offset'] + spriteW/2 * (1 if (sprite['offset'] > 0) else -1)
                    if Util.overlap(playerX, playerW, x2, spriteW, None):
                        speed = max_speed/5
                        position = Util.increase(player_segment['p1']['world']['z'], -playerZ, track_length) # stop in front of sprite (at front of segment)
                        break

            for n in range(len(player_segment['cars'])):
                car = player_segment['cars'][n]
                carW = car['sprite'][1]['w'] * SPRITE_SCALE
                if speed > car['speed']:
                    if Util.overlap(playerX, playerW, car['offset'], carW, 0.8):
                        speed = car['speed'] * (car['speed']/speed)
                        position = Util.increase(car['z'], -playerZ, track_length)
                        break

            # Collide with other players     
            for n in player_cars:
                if n == id:
                    continue
                car_segment = find_segment(player_cars[n]['position'] + playerZ)
                if car_segment != player_segment:
                    continue
                carW = sprite_list['1_PLAYER_STRAIGHT']['w'] * SPRITE_SCALE
                if speed > player_cars[n]['speed']:
                    if Util.overlap(playerX, playerW, player_cars[n]['playerX'], carW, 0.8):
                        speed = player_cars[n]['speed'] * (player_cars[n]['speed']/speed)
                        position = Util.increase(player_cars[n]['position'], -playerZ, track_length)
                        break

            playerX = Util.limit(playerX, -2, 2) # dont ever let player go too far out of bounds
            speed = Util.limit(speed, 0, max_speed) # or exceed maxSpeed
            if not offlinemode:
                send_data()

            if position > playerZ:
                global current_lap_time, last_lap_time, current_lap
                if current_lap_time != 0 and (start_position < playerZ):
                    last_lap_time = current_lap_time
                    current_lap_time = 0
                    current_lap += 1
                else:
                    current_lap_time += delta_time

        """
        SockeIO Eventhandler

        @sio.receive_data: receive data from server
        """
        @sio.event()
        def receive_data(data):
            """
            Receive data from server
            """
            global player_cars
            while True:
                player_car_lock.acquire()
                player_cars.update(data)
                player_car_lock.release()
                break

        @sio.event()
        def receive_order(order):
            """
            Receive order from server
            """
            order = order[::-1]
            global place
            for i in order:
                if i['id'] == id:
                    place = order.index(i) + 1

        @sio.event()
        def playersConnected(data):
            """
            Receive data from server
            """
            global client_ids
            client_ids = data
            print(client_ids)

        @sio.event()
        def receive_npc_car_data(data):
            """
            Receive data from server
            """
            if is_host or not self.game_is_loaded: return
            global cars
            cars = data
            put_cars_into_segments()


        def send_data():
            """
            Send data to server
            """
            sio.emit('player_data', {'id': id, 'username': username,'playerX': playerX, 'position': position, 'player_num': player_num, 'speed': speed, 'nitro': nitro_is_on, 'current_lap': current_lap})
            if is_host:
                sio.emit('npc_car_data', cars)


        def update_cars(delta_time, player_segment, player_w):
            for n in range(len(cars)):
                car = cars[n]
                old_segment = find_segment(car['z'])
                car['offset'] = car['offset'] + update_car_offset(car, old_segment, player_segment, player_w)
                car['z'] = Util.increase(car['z'], delta_time * car['speed'], track_length)
                car['percent'] = Util.percent_remaining(car['z'], segment_length)  # useful for interpolation during rendering phase
                new_segment = find_segment(car['z'])
                if old_segment != new_segment:
                    index = Util.index_of(old_segment['cars'], car)
                    old_segment['cars'].pop(index)
                    new_segment['cars'].append(car)

        def update_car_offset(car, car_segment, player_segment, player_w):
            lookahead = 20
            carW = car['sprite'][1]['w'] * SPRITE_SCALE
            dir = 0

            if (car_segment['index'] - player_segment['index']) > draw_distance:
                return 0

            for i in range(1, lookahead):
                segment = segments[(car_segment['index'] + i) % len(segments)]

                if ((segment == player_segment) and
                    (car['speed'] > speed) and
                    (Util.overlap(playerX, player_w, car['offset'], carW, 1.2))):
                    if playerX > 0.5:
                        dir = -1
                    elif playerX < -0.5:
                        dir = 1
                    else:
                        dir = 1 if car['offset'] > playerX else -1
                    
                    return dir * 1/i * (car['speed'] - speed)/max_speed # the closer the cars (smaller i) and the greated the speed ratio, the larger the offset

                for j in range(len(segment['cars'])):
                    otherCar = segment['cars'][j]
                    otherCarW = otherCar['sprite'][1]['w'] * SPRITE_SCALE

                    if ((car['speed'] > otherCar['speed']) and
                        (Util.overlap(car['offset'], carW, otherCar['offset'], otherCarW, 1.2))):
                        if otherCar['offset'] > 0.5:
                            dir = -1
                        elif otherCar['offset'] < -0.5:
                            dir = 1
                        else:
                            dir = 1 if car['offset'] > otherCar['offset'] else -1
                        
                        return dir * 1/i * (car['speed'] - otherCar['speed'])/max_speed

            # if no cars ahead, but I have somehow ended up off road, then steer back on
            if car['offset'] < -0.9:
                return 0.1
            elif car['offset'] > 0.9:
                return -0.1
            else:
                return 0        
                

        ############################################################################################################
        # Render the game world
        ############################################################################################################

        def render():
            """
            Render current game state
            """
            base_segment    = find_segment(position)
            base_percent    = Util.percent_remaining(position, segment_length)
            player_segment  = find_segment(position + playerZ)
            player_percent  = Util.percent_remaining(position + playerZ, segment_length)
            playerY         = Util.interpolate(player_segment['p1']['world']['y'], player_segment['p2']['world']['y'], player_percent)
            maxy            = window_height

            x = 0
            dx = - (base_segment['curve'] * base_percent)

            self.surface.fill('#72D7EE') # clear screen
            
            Render.background(self.surface, self.background_sky,   Background.sky,   sky_offset,  resolution * sky_speed * playerY)  # Render background sky
            Render.background(self.surface, self.background_hills, Background.hills, hill_offset, resolution * hill_speed * playerY)
            Render.background(self.surface, self.background_trees, Background.trees, tree_offset, resolution * tree_speed * playerY)

            # render road
            for n in range(draw_distance):

                segment           = segments[(base_segment['index'] + n) % len(segments)]
                segment['looped'] = segment['index'] < base_segment['index']
                segment['fog']    = Util.exponential_fog(n/draw_distance, fog_density)
                segment['clip']   = maxy
                
                Util.project(segment['p1'], (playerX * road_width) - x,      playerY + camera_height, position - (track_length if segment['looped'] else 0), camera_depth, window_width, window_height, road_width)
                Util.project(segment['p2'], (playerX * road_width) - x - dx, playerY + camera_height, position - (track_length if segment['looped'] else 0), camera_depth, window_width, window_height, road_width)            

                x += dx
                dx += segment['curve']

                if ((segment['p1']['camera']['z'] <= camera_depth) or
                    (segment['p2']['screen']['y'] >= maxy) or
                    (segment['p2']['screen']['y'] >= segment['p1']['screen']['y'])):
                    continue

                Render.segment(self.surface, window_width, lanes,
                               segment['p1']['screen']['x'],
                               segment['p1']['screen']['y'],
                               segment['p1']['screen']['w'],
                               segment['p2']['screen']['x'],
                               segment['p2']['screen']['y'],
                               segment['p2']['screen']['w'],
                               segment['fog'],
                               segment['color'])
                
                maxy = segment['p2']['screen']['y']

            # render sprites
            for n in range((draw_distance-1), 2, -1):
                segment = segments[(base_segment['index'] + n) % len(segments)]

                while True:
                    npc_car_lock.acquire()
                    for i in range(len(segment['cars'])):
                        car          = segment['cars'][i]
                        sprite       = sprites[car['sprite'][0]]
                        sprite_scale = Util.interpolate(segment['p1']['screen']['scale'], segment['p2']['screen']['scale'], car['percent'])
                        spriteX      = Util.interpolate(segment['p1']['screen']['x'],     segment['p2']['screen']['x'],     car['percent']) + (sprite_scale * car['offset'] * road_width * window_width/2)
                        spriteY      = Util.interpolate(segment['p1']['screen']['y'],     segment['p2']['screen']['y'],     car['percent'])
                        Render.sprite(self.surface, window_width, window_height, resolution, road_width, sprite, sprite_scale, spriteX, spriteY, -0.5, -1, segment['clip'])
                    npc_car_lock.release()
                    break
                for i in range(len(segment['sprites'])):
                    sprite       = sprites[(segment['sprites'][i]['source'][0])]
                    sprite_scale = segment['p1']['screen']['scale']
                    spriteX      = segment['p1']['screen']['x'] + (sprite_scale * segment['sprites'][i]['offset'] * road_width * window_width/2)
                    spriteY      = segment['p1']['screen']['y']
                    offsetX      = -1 if (segment['sprites'][i]['offset'] < 0) else 0
                    Render.sprite(self.surface, window_width, window_height, resolution, road_width, sprite, sprite_scale, spriteX, spriteY, offsetX, -1, segment['clip'])

                # Render other players (if multiplayer)
                if not offlinemode:
                    global place
                    while True:
                        player_car_lock.acquire()
                        for player in player_cars:
                            if player == id: continue
                            other_player_segment = find_segment(player_cars[player]['position'] + playerZ)
                            if player_cars[player]['current_lap'] > maxlap:
                                if not player_cars[player]['username'] in finished_players:
                                    finished_players.append(player_cars[player]['username'])
                            if segment == other_player_segment:
                                other_player_num = player_cars[player]['player_num']
                                car_percent = Util.percent_remaining(player_cars[player]['position'] + playerZ, segment_length)
                                # place = 1
                                # if player_cars[player]['position'] > position and player_cars[player]['current_lap'] >= current_lap:
                                #     place += 1
                                if player_cars[player]['nitro']:
                                    sprite = sprites[f'{other_player_num}_PLAYER_STRAIGHT_NITRO']
                                else:
                                    sprite = sprites[f'{other_player_num}_PLAYER_STRAIGHT']
                                sprite_scale = Util.interpolate(segment['p1']['screen']['scale'], segment['p2']['screen']['scale'], car_percent)
                                spriteX = Util.interpolate(segment['p1']['screen']['x'], segment['p2']['screen']['x'], car_percent) + (sprite_scale * player_cars[player]['playerX'] * road_width * window_width/2)
                                spriteY = Util.interpolate(segment['p1']['screen']['y'], segment['p2']['screen']['y'], car_percent)
                                Render.sprite(self.surface, window_width, window_height, resolution, road_width, sprite, sprite_scale, spriteX, spriteY, -0.5, -1, segment['clip'])
                        player_car_lock.release()
                        break

                # render player
                if segment == player_segment:
                    # calc steering
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_LEFT]:
                        steer = speed * -1
                    elif keys[pygame.K_RIGHT]:
                        steer = speed
                    else:
                        steer = 0

                    Render.player(self.surface, window_width, window_height, resolution, road_width, sprites, speed/max_speed,
                                camera_depth/playerZ,
                                window_width/2,
                                (window_height/2) - (camera_depth/playerZ * Util.interpolate(player_segment['p1']['camera']['y'], player_segment['p2']['camera']['y'], player_percent) * window_height/2),
                                steer,
                                player_segment['p2']['world']['y'] - player_segment['p1']['world']['y'], nitro_is_on, player_num)

        def frame():
            """
            Main game frame
            """
            self.time_now = Util.timestamp()
            self.delta_time = min(1, (self.time_now - self.last_time) / 1000)
            self.global_delta_time += self.delta_time

            # while (self.global_delta_time > step):
            #     self.global_delta_time -= step
            #     update(step)
            update(step)

            render()
            self.last_time = self.time_now
            hudupdate()

        def hudupdate():
            pygame.draw.rect(self.hud, pygame.Color(255, 0, 0, 75), [0, 0, window_width, window_height/8])
            self.surface.blit(self.hud, (0,0))

            speed_hud_text = self.font.render(str(int(speed/100)) + " Km/h", True, 'black')
            self.surface.blit(speed_hud_text, (0,0))

            last_lap_hud_text = self.font.render("Last Lap: " + str(round(last_lap_time, 2)) + " Sekunden", True, 'black')
            self.surface.blit(last_lap_hud_text, (0,25 * hud_scale))

            lapcount_hud_text = self.font.render(str(current_lap) + "/4 Laps", True, 'black')
            self.surface.blit(lapcount_hud_text, (0,50 * hud_scale))

            nitro_hud = nitro / 100
            pygame.draw.rect(self.surface, pygame.Color(0, 0, 0), [295 * hud_scale, 20 * hud_scale, 510 * hud_scale, 50 * hud_scale], border_radius=5)
            if nitro_recharging:
                pygame.draw.rect(self.surface, pygame.Color(255, 0, 0), [300 * hud_scale, 25 * hud_scale, (500*nitro_hud) * hud_scale , 40 * hud_scale], border_radius=5)

                nitro_bottle = pygame.image.load(path_nitro_empty_bottle).convert_alpha()
                nitro_bottle = pygame.transform.scale(nitro_bottle, (40 * 2.5 * hud_scale, 13 * 2.5 * hud_scale))
                nitro_bottle_rect = nitro_bottle.get_rect()
                nitro_bottle_rect.bottomleft = (((295 + 550) * hud_scale, 60 * hud_scale))
            else:
                pygame.draw.rect(self.surface, pygame.Color(77, 187, 230), [300 * hud_scale, 25 * hud_scale, 500*nitro_hud * hud_scale, 40 * hud_scale], border_radius=5)

                nitro_bottle = pygame.image.load(path_nitro_bottle).convert_alpha()
                nitro_bottle = pygame.transform.scale(nitro_bottle, (40 * 2.5 * hud_scale, 13 * 2.5 * hud_scale))
                nitro_bottle_rect = nitro_bottle.get_rect()
                nitro_bottle_rect.bottomleft = (((295 + 550) * hud_scale, 60 * hud_scale))
            if not offlinemode:
                global place
                player_place_font = pygame.font.SysFont("freesansbold.ttf", (int) (72 * hud_scale))
                player_place_text = player_place_font.render(str(place) + ".", True, 'red')
                self.surface.blit(player_place_text, (0, 100 * hud_scale))

            self.surface.blit(nitro_bottle, nitro_bottle_rect)

        def endscreen():
            if current_lap > maxlap:
                if not username in finished_players:
                    finished_players.append(username)

                race_finished_font = pygame.font.SysFont("freesansbold.ttf", (int) (72 * hud_scale))
                race_finished_player_font = pygame.font.SysFont("freesansbold.ttf", (int) (36 * hud_scale))
                race_finished_text = race_finished_font.render("RACE FINISHED", True, 'red')
                self.surface.blit(race_finished_text, (window_width/3,window_height/4))
                press_q_text = race_finished_player_font.render("Q Drücken um ins Hauptmenü zurückzukehren", True, 'red')
                self.surface.blit(press_q_text, (window_width / 4, window_height / 5))

                for i, player in enumerate(finished_players):
                    race_finished_player_text = race_finished_player_font.render(str(i + 1) + "# " + player, True, 'white')
                    self.surface.blit(race_finished_player_text, (window_width / 3, window_height / 3 + i * 30))
                global game_finished
                game_finished = True


############################################################################################################
        # Road build functions
############################################################################################################

        road = {
            'length': {'none': 0, 'short':  25, 'medium':  50, 'long':  100},
            'curve' : {'none': 0, 'easy':    2, 'medium':   4, 'hard':    6},
            'hill'  : {'none': 0, 'low':    20, 'medium':  40, 'high':   60},
        }

        def add_road(enter, hold, leave, curve, y):
            """
            Add road to track
            """
            startY = last_y()
            endY = startY + (Util.to_int(y, 0) * segment_length)
            total = enter + hold + leave

            for n in range(enter):
                add_segment((Util.ease_in(0, curve, n/enter)), (Util.ease_in_out(startY, endY, n/total)))
            for n in range(hold):
                add_segment(curve, Util.ease_in_out(startY, endY, (enter + n)/total))
            for n in range(leave):
                add_segment(Util.ease_in_out(curve, 0, n/leave), Util.ease_in_out(startY, endY, (enter + hold + n)/total))

        def add_segment(curve, y):
            """
            Add segment to road
            """
            n = len(segments)
            segments.append({
                'index': n,
                'p1': {'world': {'x':0, 'y':last_y(), 'z': n * segment_length},
                       'camera': {'x': 0, 'y': 0, 'z': 0},
                       'screen': {'x': 0, 'y': 0, 'w': 0, 'scale': 0}},
                'p2': {'world': {'x':0, 'y': y, 'z': (n + 1) * segment_length}, 
                       'camera': {'x': 0, 'y': 0, 'z': 0}, 
                       'screen': {'x': 0, 'y': 0, 'w': 0, 'scale': 0}},
                'curve': curve,
                'sprites': [],
                'cars': [],
                'color': Colors.dark if math.floor(n/rumble_length) % 2 else Colors.light
            })

        def add_sprite(n, sprite, offset):
            """
            Add sprite to road
            """
            segments[n]['sprites'].append({
                'source': sprite,
                'offset': offset
            })

        def last_y():
            """
            Get last segment y
            """
            if len(segments) == 0: return 0
            return segments[len(segments) - 1]['p2']['world']['y']
        
        def add_straight(num):
            num = num or road['length']['medium']
            add_road(num, num, num, 0, 0)

        def add_curve(num, curve, height):
            num = num or road['length']['medium']
            curve = curve or road['curve']['medium']
            height = height or road['hill']['none']
            add_road(num, num, num, curve, height)

        def add_hill(num, height):
            num = num or road['length']['medium']
            height = height or road['hill']['medium']
            add_road(num, num, num, 0, height)

        def add_downhill_to_end(num):
            num = num or 200
            add_road(num, num, num, -road['curve']['easy'], -last_y()/segment_length)

        def add_s_curves():
            """
            Add curves to road
            """
            add_road(road['length']['medium'], road['length']['medium'], road['length']['medium'],  -road['curve']['easy'],    road['hill']['none'])
            add_road(road['length']['medium'], road['length']['medium'], road['length']['medium'],   road['curve']['medium'],  road['hill']['medium'])
            add_road(road['length']['medium'], road['length']['medium'], road['length']['medium'],   road['curve']['easy'],   -road['hill']['low'])
            add_road(road['length']['medium'], road['length']['medium'], road['length']['medium'],  -road['curve']['easy'],    road['hill']['medium'])
            add_road(road['length']['medium'], road['length']['medium'], road['length']['medium'],  -road['curve']['medium'], -road['hill']['medium'])

        def add_low_rolling_hills(num, height):
            num = num or road['length']['short']
            height = height or road['hill']['low']

            add_road(num, num, num, 0, height/2)
            add_road(num, num, num, 0, -height)
            add_road(num, num, num, 0, height)
            add_road(num, num, num, 0, 0)
            add_road(num, num, num, 0, height/2)
            add_road(num, num, num, 0, 0)

        def add_bumps():
            add_road(10, 10, 10,  0,   5)
            add_road(10, 10, 10,  0,  -2)
            add_road(10, 10, 10,  0,  -5)
            add_road(10, 10, 10,  0,   8)
            add_road(10, 10, 10,  0,   5)
            add_road(10, 10, 10,  0,  -7)
            add_road(10, 10, 10,  0,   5)
            add_road(10, 10, 10,  0,  -2)

        def reset_road():
            global playerZ
            global track_length
            # segments = []
            add_straight(road['length']['short'])
            add_hill(road['length']['medium'], road['hill']['low'])
            add_low_rolling_hills(None, None)
            add_bumps()
            add_curve(road['length']['medium'], road['curve']['medium'], road['hill']['low'])
            # add_low_rolling_hills(None, None)
            add_curve(road['length']['long'], road['curve']['medium'], road['hill']['medium'])
            # add_straight(None)
            add_curve(road['length']['long'], -road['curve']['medium'], road['hill']['medium'])
            # add_hill(road['length']['long'], road['hill']['high'])
            add_curve(road['length']['long'],-road['curve']['medium'], road['hill']['low'])
            # add_hill(road['length']['long'], -road['hill']['medium'])
            add_straight(None)
            add_downhill_to_end(None)


            segments[find_segment(playerZ)['index'] + 2]['color'] = Colors.start
            segments[find_segment(playerZ)['index'] + 3]['color'] = Colors.start

            for n in range(rumble_length):
                segments[len(segments) - 1 - n]['color'] = Colors.finish

            track_length = len(segments) * segment_length

        def reset_sprites():
            """
            Reset and setup sprites
            """
            add_sprite(20, ('BILLBOARD07', sprite_list['BILLBOARD07']) , -1)
            add_sprite(40, ('BILLBOARD06', sprite_list['BILLBOARD06']) , -1)
            add_sprite(60, ('BILLBOARD08', sprite_list['BILLBOARD08']) , -1)
            add_sprite(80, ('BILLBOARD09', sprite_list['BILLBOARD09']) , -1)
            add_sprite(100, ('BILLBOARD01', sprite_list['BILLBOARD01']), -1)
            add_sprite(120, ('BILLBOARD02', sprite_list['BILLBOARD02']), -1)
            add_sprite(140, ('BILLBOARD03', sprite_list['BILLBOARD03']), -1)
            add_sprite(160, ('BILLBOARD04', sprite_list['BILLBOARD04']), -1)
            add_sprite(180, ('BILLBOARD05', sprite_list['BILLBOARD05']), -1)

            add_sprite(240, ('BILLBOARD07', sprite_list['BILLBOARD07']), -1.2)
            add_sprite(240, ('BILLBOARD06', sprite_list['BILLBOARD06']),  1.2)
            add_sprite(len(segments) - 25, ('BILLBOARD07', sprite_list['BILLBOARD07']), -1.2)
            add_sprite(len(segments) - 25, ('BILLBOARD06', sprite_list['BILLBOARD06']),  1.2)

            #for n in range(250, 1000, 50):
            #    add_sprite(n, ('COLUMN', sprite_list['COLUMN']), 1.1)
            #    add_sprite(n + Util.random_int(0,5), ('TREE1', sprite_list['TREE1']), -1 - (random.random() * 2))
            #   add_sprite(n + Util.random_int(0,5), ('TREE2', sprite_list['TREE2']), -1 - (random.random() * 2))

            for n in range(250, 1000, 50):
                offset = n // 50
                value1 = n + (offset % 6)
                value2 = -1 - ((offset % 11) / 5)

                add_sprite(n, ('COLUMN', sprite_list['COLUMN']), 1.1)
                add_sprite(n + value1, ('TREE1', sprite_list['TREE1']), value2)
                add_sprite(n, ('TREE2', sprite_list['TREE2']), -1 if n % 2 == 0 else 1)


            #for n in range(200, len(segments), 30):
            #   random_key = Util.random_key(sprite_list_plants)
            #    add_sprite(n, (random_key, sprite_list[random_key]), Util.random_choice([-1,1]) * (2 + random.random() * 5))

            for n in range(200, len(segments), 30):
                key_index = n % len(sprite_list_plants)
                key = list(sprite_list_plants.keys())[key_index]
                offset1 = (((n // 30) % 2) * 2) - 1  # Intervall von [-1, 1]
                offset2 = 2 + (n // 30) % 5  # Intervall von [2, 7]
                add_sprite(n, (key, sprite_list[key]), offset1 * offset2)


            #for n in range(1000, len(segments)-50, 500):
            #    side = Util.random_choice([1, -1])
            #    random_key = Util.random_key(sprite_list_billboards)
            #    add_sprite(n + Util.random_int(0, 50), (random_key, sprite_list[random_key]), -side * (1.5 + random.random()))
            #    for i in range(20):
            #        random_key = Util.random_key(sprite_list_plants)
            #        sprite = (random_key, sprite_list[random_key])
            #        offset = side * (1.5 + random.random())
            #        add_sprite(n + Util.random_int(0, 50), sprite, offset)

            for n in range(1000, len(segments)-50, 500):
                side = (((n // 500) % 2) * 2) - 1 # [-1, 1]
                key_index = n % len(sprite_list_billboards)
                key = list(sprite_list_billboards.keys())[key_index]

                add_sprite(n + (n // 50) % 50, (key, sprite_list[key]), -side * (1.5 + ((n // 50) % 100) / 100))
                for i in range(20):
                    key_index = (n // 50 + i) % len(sprite_list_plants)
                    key = list(sprite_list_plants.keys())[key_index]
                    sprite = (key, sprite_list[key])
                    offset = side * (1.5 + ((n // 50 + i) % 100) / 100)
                    add_sprite(n + (n // 50) % 50, sprite, offset)

        # rest start position
        def reset_player_start_positions():
            global player_start_positions
            player_start_positions = []
            offset = -0.6
            player_num = 1

            for player in client_ids:
                player_start_positions.append({'id': player, 'offset': offset, 'z': 0, 'player_num': player_num, 'speed': 0})
                offset += 0.66
                player_num += 1

            sio.emit('player_start_positions_data', player_start_positions)
            print(player_start_positions)
            return player_start_positions
        
        @sio.event()
        def receive_start_position(data):
            """
            Receive starposition
            """
            global player_start_positions
            global playerX
            global position
            global player_num
            for player in data:
                if player['id'] == id:
                    playerX = player['offset']
                    position = player['z']
                    player_num = player['player_num']
                    break
            player_start_positions = data
        
        def reset_cars():
            global cars
            cars = []
            for n in range(total_cars):
                offset = random.random() * Util.random_choice([-0.8, 0.8])
                z = math.floor(random.random() * len(segments)) * segment_length
                sprite = Util.random_choice_dict(sprite_list_cars)
                speed = max_speed/4 + random.random() * max_speed/(4 if sprite == sprite_list_cars['SEMI'] else 2)
                car = {'offset': offset, 'z': z, 'sprite': sprite, 'speed': speed}
                cars.append(car)
                
            put_cars_into_segments()

        def put_cars_into_segments():
            while True:
                npc_car_lock.acquire()
                for n in range(len(segments)):
                    segments[n]['cars'] = []

                for n in range(len(cars)):
                    car = cars[n]
                    segment = find_segment(car['z'])
                    segment['cars'].append(car)
                npc_car_lock.release()
                break

        def reset():

            global camera_depth
            global player_z
            global playerZ
            global resolution
            global fps                      # how many updates per second
            global step                       # how long is each frame
            global window_width                 # logical window width
            global window_height                 # logical window height
            global centrifugal_force            # centrifugal force multiplier when going around curves
            global offRoadDecel                 # speed multiplier when off road (e.g. you lose 2% speed each update frame)
            global sky_speed                    # background sky layer scroll speed when going around curve (or up hill)
            global hill_speed                  # background hill layer scroll speed when going around curve (or up hill)
            global tree_speed                 # background tree layer scroll speed when going around curve (or up hill)
            global sky_offset                     # current sky scroll offset
            global hill_offset                   # current hill scroll offset
            global tree_offset                   # current tree scroll offset
            global segments                     # array of road segments
            global cars                          # array of cars on the road
            global npc_car_lock               # lock for adding cars to segments

            global player_start_positions         # array of player cars
            global player_car_lock            # lock for adding cars to segments
            global player_cars                    # array of player cars
            global player_num                     # player number
            # background = None                # our background image (loaded below)
            global  sprites                      # our spritesheet (loaded below)
            global  resolution                   # scaling factor for multi-resolution support
            global road_width                  # actually half the roads width, easier math if the road spans from -roadWidth to +roadWidth
            global segment_length               # length of a single segment
            global rumble_length                  # number of segments per red/white rumble strip
            global track_length                 # z length of entire track (computed)
            global lanes                          # number of lanes
            global field_of_view                # angle (degrees) for field of view
            global camera_height               # z height of camera
            global camera_depth                 # z distance camera is from screen (computed)
            global draw_distance                 # number of segments to draw
            global playerX                       # player x offset from center of road (-1 to 1 to stay independent of roadWidth)
            global playerZ                    # player relative z distance from camera (computed)
            global fog_density                    # exponential fog density
            global position                     # current camera Z position (add playerZ to get player's absolute Z position)
            global speed                          # current speed
            global max_speed    # top speed (ensure we can't move more than 1 segment in a single frame to make collision detection easier)
            global accel               # acceleration rate - tuned until it 'felt' right
            global breaking               # deceleration rate when braking
            global decel                # 'natural' deceleration rate when neither accelerating, nor braking
            global off_road_decel      # off road deceleration is somewhere in between
            global off_road_limit       # limit when off road deceleration no longer applies (e.g. you can always go at least this speed even when off road)
            global total_cars                    # total number of cars on the road
            global current_lap_time               # current lap time
            global  last_lap_time               # last lap time
            global current_lap 
            global maxlap 
            global path_background_sky 
            global path_background_hills 
            global path_background_trees
            global path_nitro_bottle 
            global path_nitro_empty_bottle 
            global max_nitro 
            global nitro 
            global nitro_recharging 
            global nitro_is_on 
            global place 
            global finished_players 
            global game_finished

            segments = []
            cars = []
            npc_car_lock = Lock()
            player_start_positions = []
            player_car_lock = Lock()
            player_cars = {}
            sprites = None
            track_length = None
            playerX = 0
            position = 1
            speed = 0
            max_speed = segment_length / step
            accel = max_speed / 5
            breaking = -max_speed
            decel = -max_speed / 5
            off_road_decel = -max_speed / 2
            off_road_limit = max_speed / 4
            current_lap_time = 0
            last_lap_time = 0
            current_lap = 0
            max_nitro = 100
            nitro = 100
            nitro_recharging = False
            nitro_is_on = False
            place = 1
            finished_players = []
            game_finished = False
    
            camera_depth = 1 / math.tan((field_of_view/2) * math.pi/180)
            player_z = (camera_height * camera_depth)
            playerZ = (camera_height * camera_depth)
            resolution = window_height / 480
          
            if len(segments) == 0:
                reset_road()
                reset_sprites()

                if is_host:
                    reset_cars()
                    if not offlinemode:
                        reset_player_start_positions()
                        sio.emit('npc_car_data', cars)
                else:
                    if not offlinemode:
                        sio.emit('request_start_position')

        def find_segment(z):
            """
            Find segment by z
            """
            return segments[math.floor(z/segment_length) % len(segments)]


        # Start of the game
        # Game.
        sprites = Game.load_images()
        reset()
        if not offlinemode: sio.emit('game_start')
        global player_num
        print("PLAYER NUMBER", player_num)
        self.game_is_loaded = True
        # main game loop
        while self.game_is_loaded:
            self.clock.tick(fps)

            frame()
            endscreen()
            # pygame.display.update()
            pygame.display.flip()
            # handle quit event
            for event in pygame.event.get([pygame.QUIT]):
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
