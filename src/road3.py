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
position = 200                      # current camera Z position (add playerZ to get player's absolute Z position)
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
            global position, speed, playerX, playerZ
            position = Util.increase(position, delta_time * speed, track_length)
            dx = delta_time * 2 * (speed/max_speed) # at top speed, should be able to cross from left to right (-1 to 1) in 1 second
            
            # input handling
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:     # drive left
                playerX -= dx
            if keys[pygame.K_RIGHT]:    # drive right
                playerX += dx

            if keys[pygame.K_UP]:       # go faster
                speed = Util.accelerate(speed, accel, delta_time)
            elif keys[pygame.K_DOWN]:   # slow down
                speed = Util.accelerate(speed, breaking, delta_time)
            else:                       # slow down if not pressing forward or backward
                speed = Util.accelerate(speed, decel, delta_time)

            if ((playerX < -1) or (playerX > 1)) and (speed > off_road_limit):
                speed = Util.accelerate(speed, off_road_decel, delta_time) # driving off road slows you down
            
            playerX = Util.limit(playerX, -2, 2) # dont ever let player go too far out of bounds
            speed = Util.limit(speed, 0, max_speed) # or exceed maxSpeed

        def render():
            """
            Render current game state
            """
            self.surface.fill('#FFFFFF') # clear screen
            # render background
            Render.background(self.surface, self.background_sky, window_width, window_height, Background.sky)
            Render.background(self.surface, self.background_hills, window_width, window_height, Background.hills)
            Render.background(self.surface, self.background_trees, window_width, window_height, Background.trees)

            # render road
            base_segment = find_segment(position)
            maxy = window_height
            for n in range(draw_distance):
                segment = segments[(base_segment['index'] + n) % len(segments)]
                segment['looped'] = segment['index'] < base_segment['index']
                segment['fog'] = Util.exponential_fog(n/draw_distance, fog_density)
                
                Util.project(segment['p1'], playerX * road_width, camera_height, position - (track_length if segment['looped'] else 0), camera_depth, window_width, window_height, road_width)
                Util.project(segment['p2'], playerX * road_width, camera_height, position - (track_length if segment['looped'] else 0), camera_depth, window_width, window_height, road_width)            

                if (segment['p1']['camera']['z'] <= camera_depth) or (segment['p2']['screen']['y'] >= maxy):
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

        def reset_road():
            """
            Reset and setup road
            """
            global track_length
            for n in range(1, road_length):
                segments.append({
                    'index': n,
                    'p1': {'world': {'x':0, 'y':0, 'z': n * segment_length},
                           'camera': {'x': 0, 'y': 0, 'z': 0},
                           'screen': {'x': 0, 'y': 0, 'w': 0, 'scale': 0}},
                    'p2': {'world': {'x':0, 'y':0, 'z': (n + 1) * segment_length}, 
                           'camera': {'x': 0, 'y': 0, 'z': 0}, 
                           'screen': {'x': 0, 'y': 0, 'w': 0, 'scale': 0}},
                    'color': Colors.dark if math.floor(n/rumble_length) % 2 else Colors.light
                })
            
            track_length = len(segments) * segment_length

        def reset():
            if (len(segments) == 0):
                reset_road()

            global camera_depth
            global player_z
            camera_depth = 1 / math.tan((field_of_view/2) * math.pi/180)
            player_z = (camera_height * camera_depth)


        def find_segment(z):
            """
            Find segment by z
            """
            # print (z, segment_length, len(segments))
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