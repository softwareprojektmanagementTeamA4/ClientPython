import pygame
import math
import sys

HEIGHT = 510
WIDTH = 720

pygame.init()

FPS = 60
light_green = (50, 200, 50)
dark_green = (50, 100, 50)
white = (255, 255, 255)
red = (255, 50, 0)
grey = (128, 128, 128)
start_pos = 0.0
distance = 0.0
clock = pygame.time.Clock()
sky_image = pygame.transform.scale(pygame.image.load("media/sky.PNG"), (WIDTH, HEIGHT/2))
sky_image2 = pygame.transform.flip(sky_image, True, False)
sky_rect = sky_image.get_rect(bottomleft=(0, HEIGHT/2))
sky_rect2 = sky_image2.get_rect(bottomright=(0, HEIGHT/2))
move = math.ceil(WIDTH*0.02)


def oncreation(surface, time=3.5):
    global distance
    surface.blit(sky_image2, sky_rect2)
    surface.blit(sky_image, sky_rect)

    if pygame.key.get_pressed()[pygame.K_w]:
        sky_rect.x += move
        sky_rect2.x += move
        distance += 100.00 * time
    for y in range(int(HEIGHT / 2)):
        for x in range(WIDTH):

            perspective = y / (HEIGHT / 2)
            middle_point = 0.5
            road_width = 0.15 + (perspective * 0.8)
            strip_width = road_width * 0.15
            road_width *= 0.5

            left_grass = (middle_point - road_width - strip_width) * WIDTH
            left_strip = (middle_point - road_width) * WIDTH
            right_strip = (middle_point + road_width) * WIDTH
            right_grass = (middle_point + road_width + strip_width) * WIDTH

            row = int((HEIGHT / 2)) + y   # Von der Hälfte Zeichnen (0, (h/2) + y)
            grass_color = light_green if math.sin(20.0 * ((1.0 - perspective)**3) + distance * 0.1) > 0.0 else \
                dark_green  # -1 < x < 1
            strip_color = red if math.sin(80.0 * ((1.0 - perspective)**2) + distance) > 0.0 else white

            if 0 <= x < left_grass:  # (0 <= x < 88)
                surface.set_at((x, row), grass_color)
            if left_grass <= x < left_strip:  # (88 <= x < 160)
                surface.set_at((x, row), strip_color)
            if left_strip <= x < right_strip:  # (160 <= x < 640)
                surface.set_at((x, row), grey)
            if right_strip <= x < right_grass:  # (640 <= x < 712)
                surface.set_at((x, row), strip_color)
            if right_grass <= x < WIDTH:  # (712 <= x < 800)
                surface.set_at((x, row), grass_color)

            if sky_rect.x >= WIDTH:
                sky_rect.right = 0

            if sky_rect2.x >= WIDTH:
                sky_rect2.right = 0

    car_pos = (WIDTH / 2) + ((WIDTH * start_pos) / 2.0)
    pygame.draw.circle(surface, 'black', (car_pos, HEIGHT - 70), 10)


screen = pygame.display.set_mode((WIDTH, HEIGHT))
while True:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    oncreation(screen)
    pygame.display.flip()