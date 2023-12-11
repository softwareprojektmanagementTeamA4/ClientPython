import time
import random
from math import cos, pi, e
import pygame
import math
from sprites import sprite_list

SPRITE_SCALE = 0.3 * (1/sprite_list['PLAYER_STRAIGHT']['w'])

class Colors:
    sky = pygame.Color("#72D7EE")
    tree = pygame.Color("#005108")
    fog = pygame.Color("#005108")
    light = {'road': pygame.Color("#6B6B6B"), 'grass': pygame.Color("#10AA10"), 'rumble': pygame.Color("#555555"), 'lane': pygame.Color("#CCCCCC")}
    dark = {'road': pygame.Color("#6B6B6B"), 'grass': pygame.Color("#009A00"), 'rumble': pygame.Color("#BBBBBB")}
    start = {'road': pygame.Color("#FFFFFF"), 'grass': pygame.Color("#FFFFFF"), 'rumble': pygame.Color("#FFFFFF")}
    finish = {'road': pygame.Color("#000000"), 'grass': pygame.Color("#000000"), 'rumble': pygame.Color("#000000")}

class Background:
    hills = {'x': 0, 'y': 0, 'w': 1280, 'h': 480}
    sky = {'x': 0, 'y': 0, 'w': 1280, 'h': 480}
    trees = {'x': 0, 'y': 0, 'w': 1280, 'h': 480}

class Game:
    def load_images():
        """
        Load images
        """
        images = {}
        sprite_sheet = pygame.image.load("media/sprites.png")
        for name, sprite in sprite_list.items():
            images[name] = sprite_sheet.subsurface(pygame.Rect(sprite['x'], sprite['y'], sprite['w'], sprite['h']))

        return images

class Util:

    def to_int(number, default):
        """
        Convert number to int
        """
        try:
            return int(number)
        except ValueError:
            return default

    def timestamp():
        """
        Return current timestamp
        """
        return time.time()

    def accelerate(speed, accel, delta_time):
        """
        Accelerate speed by accel, with delta_time
        """
        return speed + (accel * delta_time)

    def limit(value, low, high):
        """
        Limit value to be between low and high
        """
        return max(low, min(value, high))

    def random_int(low, high):
        """
        Return random integer between low and high
        """
        return random.randint(low, high)
    
    def random_choice(options):
        """
        Return random choice from options
        """
        return options[random.randint(0, len(options) - 1)]

    def interpolate(a, b, percent):
        """
        Interpolate from a to b by percent
        """
        return a + (b - a) * percent

    def ease_in(a, b, percent):
        """
        Ease in from a to b by percent
        """
        return a + (b - a) * pow(percent, 2)

    def ease_out(a, b, percent):
        """
        Ease out from a to b by percent
        """
        return a + (b - a) * (1 - pow(1 - percent, 2))

    def ease_in_out(a, b, percent):
        """
        Ease in and out from a to b by percent
        """
        return a + (b - a) * ((-cos(percent * pi) / 2) + 0.5)

    def exponential_fog(distance, density):
        """
        Return exponential fog value for distance and density
        """
        return 1 / (pow(e, (distance * distance * density)))

    def percent_remaining(n, total):
        """
        Return percent remaining of n and total
        """
        return (n % total) / total

    def increase(start, increment, max):
        """
        Increase value by increment, but don't go over max
        Loop if we go over max
        """
        result = start + increment
        while result > max:
            result -= max
        while result < 0:
            result += max
        return result

    # def project(p, cameraX, cameraY, cameraZ, camera_depth, width, height, roadWidth):
    #     """
    #     Project p onto screen
    #     """
    #     p.camera.x = (p.world.x or 0) - cameraX
    #     p.camera.y = (p.world.y or 0) - cameraY
    #     p.camera.z = (p.world.z or 0) - cameraZ
    #     p.screen.scale = camera_depth / p.camera.z
    #     p.screen.x = round((width / 2) + (p.screen.scale * p.camera.x * width / 2))
    #     p.screen.y = round((height / 2) - (p.screen.scale * p.camera.y * height / 2))
    #     p.screen.w = round((p.screen.scale * roadWidth * width / 2))

    def project(p, cameraX, cameraY, cameraZ, camera_depth, width, height, roadWidth):
        """
        Project p onto screen
        """
        #TODO: bug in the screen scale = camera_depth / p.camera.z 

        p['camera']['x'] = (p['world']['x'] or 0) - cameraX
        p['camera']['y'] = (p['world']['y'] or 0) - cameraY
        p['camera']['z'] = (p['world']['z'] or 0) - cameraZ
        if (p['camera']['z'] > 0):
            p['screen']['scale'] = camera_depth / p['camera']['z']
        else:
            p['screen']['scale'] = 0
        p['screen']['x'] = round((width / 2)  + (p['screen']['scale'] * p['camera']['x'] * width / 2))
        p['screen']['y'] = round((height / 2) - (p['screen']['scale'] * p['camera']['y'] * height / 2))
        p['screen']['w'] = round(               (p['screen']['scale'] * roadWidth * width / 2))

    def overlap(x1, w1, x2, w2, percent):
        """
        Return percent overlap of x1, w1, x2, w2
        """
        half = (percent or 1) / 2
        min1 = x1 - (w1 * half)
        max1 = x1 + (w1 * half)
        min2 = x2 - (w2 * half)
        max2 = x2 + (w2 * half)
        return not ((max1 < min2) or (min1 > max2))
    
class Render:
    def rumble_width(projectedRoadWidth, lanes):
        """
        Return rumble width
        """
        return projectedRoadWidth / max(6,  2 * lanes)
    
    def lane_marker_width(projectedRoadWidth, lanes):
        """
        Return lane marker width
        """
        return projectedRoadWidth / max(32, 8 * lanes)


    def polygon(surface, x1, y1, x2, y2, x3, y3, x4, y4, color):
        """
        Draw polygon
        """
        pygame.draw.polygon(surface, color, [(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

    def segment(surface, width, lanes, x1, y1, w1, x2, y2, w2, fog, color):
        """
        Draw segment
        """
        r1 = Render.rumble_width(w1, lanes)
        r2 = Render.rumble_width(w2, lanes)
        l1 = Render.lane_marker_width(w1, lanes)
        l2 = Render.lane_marker_width(w2, lanes)

        fill_color = color['grass']
        rectangle = pygame.Rect(0, y2, width, y1 - y2)
        pygame.draw.rect(surface, fill_color, rectangle)

        Render.polygon(surface, x1 - w1 - r1, y1, x1 - w1, y1, x2 - w2, y2, x2 - w2 - r2, y2, color['rumble'])
        Render.polygon(surface, x1 + w1 + r1, y1, x1 + w1, y1, x2 + w2, y2, x2 + w2 + r2, y2, color['rumble'])
        Render.polygon(surface, x1 - w1, y1, x1 + w1, y1, x2 + w2, y2, x2 - w2, y2, color['road'])
        
        if ('lane' in color):
            lanew1 = w1 * 2 / lanes
            lanew2 = w2 * 2 / lanes
            lanex1 = x1 - w1 + lanew1
            lanex2 = x2 - w2 + lanew2
            for lane in range(1, lanes):
                Render.polygon(surface, lanex1 - l1 / 2, y1, lanex1 + l1 / 2, y1, lanex2 + l2 / 2, y2, lanex2 - l2 / 2, y2, color['lane'])
                lanex1 += lanew1
                lanex2 += lanew2
        
        Render.fog(surface, 0, y1, width, y2 - y1, fog)

        

    # def background(surface, background, width, height, layer, rotation, offset):
    #     """
    #     Draw background
    #     background has to be a pygame.Surface
    #     """
    #     rotation = rotation or 0
    #     offset = offset or 0

    #     imageW = layer.w/2
    #     imageH = layer.h

    #     sourceX = layer.x + math.floor(layer.w * rotation)
    #     sourceY = layer.y
    #     sourceW = min(imageW, layer.x + layer.w - sourceX)
    #     sourceH = imageH

    #     destX = 0
    #     destY = offset
    #     destW = math.floor(width * (sourceW / imageW))
    #     destH = height

    #     surface.blit(background, (destX, destY), (sourceX, sourceY, sourceW, sourceH))

    #     if (sourceW < imageW):
    #         surface.blit(background, (layer.x, sourceY), (imageW-sourceW, sourceH, destW-1, destH))

    def background(surface, background, width, height, layer, rotation):
        """
        Draw background
        background has to be a pygame.Surface
        """
        rotation = rotation or 0
        background_offset = 0

        imageW = layer['w']*10
        imageH = layer['h']

        sourceX = layer['x'] + math.floor(layer['w'] * rotation)
        sourceY = layer['y']
        sourceW = min(imageW, layer['x'] + layer['w'] - sourceX)
        sourceH = imageH

        destX = 0
        destY = background_offset
        destW = math.floor(width * (sourceW / imageW))
        destH = height

        # background = pygame.transform.scale(background, (imageW * 2, imageH))
        background = pygame.transform.scale(background, (width * 2, height))
        # background = pygame.transform.scale(background, (destW, destH))
        # surface.blit(background, background_pos)
        surface.blit(background, (destX, destY), (sourceX, sourceY, sourceW, sourceH))

        if (sourceW < imageW):
            surface.blit(background, (layer['x'], sourceY), (imageW-sourceW, sourceH, destW-1, destH))
            # surface.blit(background, (destW-1, destY), (layer['x'], sourceY, imageW-sourceW, sourceH))

    def player(surface, width, height, resolution, roadWidth, sprites, speed_percent, scale, destX, destY, steer, updown):
        """
        Draw player
        """
        bounce = (1.5 * random.random() * speed_percent * resolution) * Util.random_choice([-1, 1])
        if (steer < 0):
            sprite = sprites['PLAYER_UPHILL_LEFT'] if updown > 0 else sprites['PLAYER_LEFT']
        elif (steer > 0):
            sprite = sprites['PLAYER_UPHILL_RIGHT'] if updown > 0 else sprites['PLAYER_RIGHT']
        else:
            sprite = sprites['PLAYER_UPHILL_STRAIGHT'] if updown > 0 else sprites['PLAYER_STRAIGHT']

        Render.sprite(surface, width, height, resolution, roadWidth, sprite, scale, destX, destY + bounce, -0.5, -1, 0)

    def sprite(surface, width, height, resolution, roadWidth, sprite, scale, destX, destY, offsetX, offsetY, clipY):
        """
        Draw sprite
        """
        destW = (sprite.get_width() * scale * width / 2) * (SPRITE_SCALE * roadWidth)
        destH = (sprite.get_height() * scale * width / 2) * (SPRITE_SCALE * roadWidth)

        destX = destX + (destW * (offsetX or 0))
        destY = destY + (destH * (offsetY or 0))

        clipH = math.max(0, destY + destH - clipY) if (clipY) else 0
        if (clipH < destH):
            # rect = (destX, destY, destW, destH - clipH)
            # destW = 1000
            # destH = 1000
            sprite = pygame.transform.scale(sprite, (destW, destH))

            # surface.blit(sprite, (destX, destY))
            # surface.blit(sprite, (destX, destY), (0, 0, destW, destH - clipH))
            surface.blit(sprite, (destX, destY), (0, 0, destW, destH - clipH))


    def fog(surface, x, y, width, height, fog):
        """
        Draw fog
        """
        if (fog < 1):
            s = pygame.Surface((width, -height + 1))
            s.set_alpha(255 * (1-fog))
            s.fill(Colors.fog)
            surface.blit(s, (x, y+height))
            s.set_alpha(255)
