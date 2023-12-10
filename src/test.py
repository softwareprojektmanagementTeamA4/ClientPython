import math
from random import random

import pygame
import Util

# Initialisierung von Pygame
pygame.init()
clock = pygame.time.Clock()
class Game:
    def __init__(self):
        # Game variables
        self.fps = 60
        self.step = 1/self.fps
        self.screen_width = 1024
        self.screen_height = 768
        self.segments = []
        self.canvas = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.background = None
        self.sprites = None
        self.resolution = None
        self.roadWidth = 2000
        self.segmentLength = 200
        self.rumbleLength = 3
        self.trackLength = None
        self.lanes = 3
        self.fieldOfView = 100
        self.cameraHeight = 1000
        self.cameraDepth = None
        self.drawDistance = 300
        self.playerX = 0
        self.playerZ = None
        self.fogDensity = 5
        self.position = 0
        self.speed = 0
        self.maxSpeed = self.segmentLength/self.step
        self.accel = self.maxSpeed/5
        self.breaking = -self.maxSpeed
        self.decel = -self.maxSpeed/5
        self.offRoadDecel = -self.maxSpeed/2
        self.offRoadLimit = self.maxSpeed/4

        self.colors = {
            "SKY": pygame.Color(114, 215, 238),
            "TREE": pygame.Color(0, 81, 8),
            "FOG": pygame.Color(0, 81, 8),
            "LIGHT": {'road': pygame.Color(107, 107, 107), 'grass': pygame.Color(16, 170, 16), 'rumble': pygame.Color(85, 85, 85), 'lane': pygame.Color(204, 204, 204)},
            "DARK": {'road': pygame.Color(105, 105, 105), 'grass': pygame.Color(0, 154, 0), 'rumble': pygame.Color(187, 187, 187)},
            "START": {'road': pygame.Color(255, 255, 255), 'grass': pygame.Color(255, 255, 255), 'rumble': pygame.Color(255, 255, 255)},
            "FINISH": {'road': pygame.Color(0, 0, 0), 'grass': pygame.Color(0, 0, 0), 'rumble': pygame.Color(0, 0, 0)}
        }

        self.keyLeft = False
        self.keyRight = False
        self.keyFaster = False
        self.keySlower = False

    def update(self, dt):
        self.position = Util.increase(self.position, dt * self.speed, self.trackLength)

        dx = dt * 2 * (self.speed/self.maxSpeed) #  at top speed, should be able to cross from left to right (-1 to 1) in 1 second

        keys = pygame.key.get_pressed()
        if (self.keyFaster):
            self.speed = Util.acceelerate(self.speed, self.accel, dt)
        elif (self.keySlower):
            self.speed = Util.acceelerate(self.speed, self.breaking, dt)
        else:
            self.speed = Util.acceelerate(self.speed, self.decel, dt)

        if (((self.playerX < -1) or (self.playerX > 1)) and (self.speed > self.offRoadLimit)):
            self.speed = Util.acceelerate(self.speed, self.offRoadLimit, dt)

    def polygon(self, surface, x1, y1, x2, y2, x3, y3, x4, y4, color):
        pygame.draw.polygon(surface, color, [(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

    def draw_background(self):
        """
        rotation = rotation if rotation is not None else 0
        offset = offset if offset is not None else 0

        imageW = layer.w/2
        imageH = layer.h

        sourceX = layer.x + math.floor(layer.w * rotation)
        sourceY = layer.y
        sourceW = min(imageW, layer.x+layer.w-sourceX)
        sourceH = imageH

        destX = 0
        destY = offset
        destW = math.floor(width * (sourceW/imageW))
        destH = height
        """
        sky_image = pygame.transform.scale(pygame.image.load("media/backgroundRepeatable.png"), (self.screen_width, self.screen_height / 2))
        sky_rect = sky_image.get_rect(bottomleft=(0, self.screen_height / 2))
        self.canvas.blit(sky_image, sky_rect)

    def draw_segment(self, width, lanes, x1, y1, w1, x2, y2, w2, color):
        r1 = Util.rumbleWidth(w1, lanes)
        r2 = Util.rumbleWidth(w2, lanes)
        l1 = Util.laneMarkerWidth(w1, lanes)
        l2 = Util.laneMarkerWidth(w2, lanes)

        rect = pygame.Rect(0, y2, width, y1 - y2)
        pygame.draw.rect(self.canvas, color['grass'], rect)

        self.polygon(self.canvas, x1-w1-r1, y1, x1-w1, y1, x2-w2, y2, x2-w2-r2, y2, color['rumble'])
        self.polygon(self.canvas, x1+w1+r1, y1, x1+w1, y1, x2+w2, y2, x2+w2+r2, y2, color['rumble'])
        self.polygon(self.canvas, x1-w1,    y1, x1+w1, y1, x2+w2, y2, x2-w2,    y2, color['rumble'])

        if (color['lane']):
            lanew1 = w1*2/lanes
            lanew2 = w2*2/lanes
            lanex1 = x1 - w1 + lanew1
            lanex2 = x2 - w2 + lanew2

            lane = 1

            while lane < lanes:
                self.polygon(self.canvas, lanex1 - l1/2, y1, lanex1 + l1/2, y1, lanex2 + l2/2, y2, lanex2 - l2/2, y2, color['lane'])

                lanex1 += lanew1
                lanex2 += lanew2
                lane += 1

    def draw_player(self, width, height, resolution, roadWidth, sprites, speedPercent, scale, destX, destY, steer, updown):
        bounce = (1.5 * random() * speedPercent * resolution) * Util.randomChoice([-1,1])

        if (steer < 0):
            pass
    def findSegment(self,z):
        return self.segments[math.floor(z/self.segmentLength) % self.segmentLength]

    def resetRoad(self):
        self.segments = []
        for n in range(500):
            color = self.colors['DARK'] if n // self.rumbleLength % 2 else self.colors['LIGHT']
            self.segments.append({'index' : n,
            'p1': { 'world': { 'z': n *self.segmentLength}, 'camera': {}, 'screen': {} },
            'p2': { 'world': { 'z': (n+1) *self.segmentLength}, 'camera': {}, 'screen': {} },
            'color': color

            })
        self.segments[self.findSegment(self.playerZ)['index'] + 2]['color'] = self.colors['START']
        self.segments[self.findSegment(self.playerZ)['index'] + 3]['color'] = self.colors['START']

        for n in range(self.rumbleLength):
            self.segments[len(self.segments)-1-n]['color'] = self.colors['FINISH']

        self.trackLength = len(self.segments) * self.segmentLength

    def render(self):

        baseSegment = self.findSegment(self.position)
        maxY = self.screen_height

        # Füllt das Surface mit Schwarz (oder einer anderen Farbe)
        self.canvas.fill(0, 0, 0)
        game.draw_background()

        segment = self.segments[(baseSegment)]

        for n in range(self.drawDistance):

            segment = self.segments[(baseSegment['index'] + n) % len(self.segments)]

            Util.project(segment['p1'], (self.playerX * self.roadWidth), self.cameraHeight, self.position, self.cameraDepth, self.screen_width, self.screen_height, self.roadWidth)
            Util.project(segment['p2'], (self.playerX * self.roadWidth), self.cameraHeight, self.position, self.cameraDepth, self.screen_width, self.screen_height, self.roadWidth)

            if ((self.segment['p1']['camera']['z'] <= self.cameraDepth) or (segment['p2']['screen']['y'] >= maxY)):
                continue

            self.draw_segment(self.screen_width, self.lanes,
                              segment['p1']['screen']['x'],
                              segment['p1']['screen']['y'],
                              segment['p1']['screen']['w'],
                              segment['p2']['screen']['x'],
                              segment['p2']['screen']['y'],
                              segment['p2']['screen']['w'],
                              segment['color'])

            maxY = segment['p2']['screen']['y']




# Spiel-Titel festlegen
pygame.display.set_caption("Pseudo-3D Racer")

game = Game()
# Spiel-Schleife
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    # Bildschirm aktualisieren
    clock.tick(60)
    pygame.display.flip()

# Pygame beenden, wenn die Schleife beendet ist
pygame.quit()
