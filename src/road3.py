import math
import time
from typing import List
import pygame
import sys
import os
from util import *

src_path = os.path.dirname(__file__)


fps = 60                           # how many updates per second
step = 1/fps                       # how long is each frame
window_width = 1024                # logical window width
window_height = 768                # logical window height
centrifugal_force = 0.3            # centrifugal force multiplier when going around curves
offRoadDecel = 0.99                # speed multiplier when off road (e.g. you lose 2% speed each update frame)
sky_speed = 0.001                  # background sky layer scroll speed when going around curve (or up hill)
hill_speed = 0.002                 # background hill layer scroll speed when going around curve (or up hill)
tree_speed = 0.003                 # background tree layer scroll speed when going around curve (or up hill)
sky_offset = 0                     # current sky scroll offset
hill_offset = 0                    # current hill scroll offset
tree_offset = 0                    # current tree scroll offset
segments = []                      # array of road segments
cars = []                          # array of cars on the road
# background = None                  # our background image (loaded below)
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
total_cars = 200                   # total number of cars on the road
current_lap_time = 0               # current lap time
last_lap_time = None               # last lap time
path_background_sky = "background/sky.png"
path_background_hills = "background/hills.png"
path_background_trees = "background/trees.png"


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
        self.clock = pygame.time.Clock()

        self.background_sky = pygame.image.load(path_background_sky).convert_alpha()
        self.background_hills = pygame.image.load(path_background_hills).convert_alpha()
        self.background_trees = pygame.image.load(path_background_trees).convert_alpha()

        self.background = pygame.Surface((window_width, window_height))


    def run(self):
        """
        Main game loop
        """

        def update(delta_time):
            """
            Update current game state
            """
            global position, speed, playerX, playerZ, sky_offset, hill_offset, tree_offset
            player_segment = find_segment(position + playerZ)
            speed_percent = speed/max_speed
            dx = delta_time * 2 * speed_percent # at top speed, should be able to cross from left to right (-1 to 1) in 1 second
            
            position = Util.increase(position, delta_time * speed, track_length)
            
            sky_offset  = Util.increase(sky_offset,  (sky_speed  * player_segment['curve'] * speed_percent), 1)
            hill_offset = Util.increase(hill_offset, (hill_speed * player_segment['curve'] * speed_percent), 1)
            tree_offset = Util.increase(tree_offset, (tree_speed * player_segment['curve'] * speed_percent), 1)

            # input handling
            keys = pygame.key.get_pressed()
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

            if keys[pygame.K_SPACE]:    # For testing purposes
                pass

            if ((playerX < -1) or (playerX > 1)) and (speed > off_road_limit):
                speed = Util.accelerate(speed, off_road_decel, delta_time) # driving off road slows you down
            
            playerX = Util.limit(playerX, -2, 2) # dont ever let player go too far out of bounds
            speed = Util.limit(speed, 0, max_speed) # or exceed maxSpeed


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

            self.surface.fill('#FFFFFF') # clear screen
            
            Render.background(self.surface, self.background_sky,   window_width, window_height, Background.sky,   sky_offset)  # Render background sky
            Render.background(self.surface, self.background_hills, window_width, window_height, Background.hills, hill_offset)
            Render.background(self.surface, self.background_trees, window_width, window_height, Background.trees, tree_offset)

            # render road
            for n in range(draw_distance):

                segment           = segments[(base_segment['index'] + n) % len(segments)]
                segment['looped'] = segment['index'] < base_segment['index']
                segment['fog']    = Util.exponential_fog(n/draw_distance, fog_density)
                
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

            # render player
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
                          player_segment['p2']['world']['y'] - player_segment['p1']['world']['y'])

            
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
                'color': Colors.dark if math.floor(n/rumble_length) % 2 else Colors.light
            })

        def last_y():
            """
            Get last segment y
            """
            if (len(segments) == 0): return 0
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


        def reset_road():
            global playerZ
            global track_length
            add_straight(road['length']['short'])
            add_hill(road['length']['medium'], road['hill']['low'])
            add_low_rolling_hills(None, None)
            add_curve(road['length']['medium'], road['curve']['medium'], road['hill']['low'])
            add_low_rolling_hills(None, None)
            add_curve(road['length']['long'], road['curve']['medium'], road['hill']['medium'])
            add_straight(None)
            add_curve(road['length']['long'], -road['curve']['medium'], road['hill']['medium'])
            add_hill(road['length']['long'], road['hill']['high'])
            add_curve(road['length']['long'],-road['curve']['medium'], road['hill']['low'])
            add_hill(road['length']['long'], -road['hill']['medium'])
            add_straight(None)
            add_downhill_to_end(None)

            segments[find_segment(playerZ)['index'] + 2]['color'] = Colors.start
            segments[find_segment(playerZ)['index'] + 3]['color'] = Colors.start

            for n in range(rumble_length):
                segments[len(segments) - 1 - n]['color'] = Colors.finish

            track_length = len(segments) * segment_length


        # reset_road version straight
        # def reset_road():
        #     """
        #     Reset and setup road
        #     """
        #     global track_length
        #     for n in range(1, road_length):
        #         segments.append({
        #             'index': n,
        #             'p1': {'world': {'x':0, 'y':0, 'z': n * segment_length},
        #                    'camera': {'x': 0, 'y': 0, 'z': 0},
        #                    'screen': {'x': 0, 'y': 0, 'w': 0, 'scale': 0}},
        #             'p2': {'world': {'x':0, 'y':0, 'z': (n + 1) * segment_length}, 
        #                    'camera': {'x': 0, 'y': 0, 'z': 0}, 
        #                    'screen': {'x': 0, 'y': 0, 'w': 0, 'scale': 0}},
        #             'color': Colors.dark if math.floor(n/rumble_length) % 2 else Colors.light
        #         })
            
        #     track_length = len(segments) * segment_length

        def reset():

            global camera_depth
            global player_z
            global playerZ
            global resolution
            camera_depth = 1 / math.tan((field_of_view/2) * math.pi/180)
            player_z = (camera_height * camera_depth)
            playerZ = (camera_height * camera_depth)
            resolution = window_height / 480
          
            if (len(segments) == 0):
                reset_road()


        def find_segment(z):
            """
            Find segment by z
            """
            return segments[math.floor(z/segment_length) % len(segments)]


        # Start of the game
        
        # Game.
        sprites = Game.load_images()
        reset()
        # main game loop
        while True:
            self.clock.tick(fps)
            frame()
            pygame.display.update()

            # handle quit event
            for event in pygame.event.get([pygame.QUIT]):
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()





game = GameWindow()
game.run()