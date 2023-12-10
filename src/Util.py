from random import random


def increase(start, increment,max):
    result = start + increment
    while (result >= max):
        result -= max
    while (result < 0):
        result += max
    return result

def acceelerate(v, accel, dt):
    return v + (accel * dt)

def project(p, camera_x, camera_y, camera_z, camera_depth, width, height, road_width):
    p['camera']['x'] = p['world'].get('x', 0) - camera_x
    p['camera']['y'] = p['world'].get('y', 0) - camera_y
    p['camera']['z'] = p['world'].get('z', 0) - camera_z

    p['screen']['scale'] = camera_depth / p['camera']['z']
    p['screen']['x'] = round((width / 2) + (p['screen']['scale'] * p['camera']['x'] * width / 2))
    p['screen']['y'] = round((height / 2) - (p['screen']['scale'] * p['camera']['y'] * height / 2))
    p['screen']['w'] = round(p['screen']['scale'] * road_width * width / 2)

def rumbleWidth(projectedRoadWidth, lanes):
    return projectedRoadWidth/max(6, 2*lanes)

def laneMarkerWidth(projectedRoadWidth, lanes):
    return projectedRoadWidth/max(32, 8*lanes)

def interpolate(a,b,percent):
    return a+(b-a)*percent

def randomInt(min, max):
    return round(interpolate(min, max, random()))

def randomChoice(options):
    return options[randomInt(0, len(options)-1)]