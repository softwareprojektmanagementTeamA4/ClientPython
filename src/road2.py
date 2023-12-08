import math
import time
from typing import List
import pygame
import sys

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

roadW = 2000  # road width (left to right)
segL = 200  # segment length (top to bottom)
camD = 0.84  # camera depth
show_N_seg = 300  # number of segments to show on screen
tick_rate = 60  # frames per second

dark_grass = pygame.Color(0, 154, 0)
light_grass = pygame.Color(16, 200, 16)
white_rumble = pygame.Color(255, 255, 255)
black_rumble = pygame.Color(0, 0, 0)
dark_road = pygame.Color(105, 105, 105)
light_road = pygame.Color(150, 150, 150)


class Line:
    def __init__(self, i):
        self.i = i
        self.x = self.y = self.z = 0.0  # game position (3D space)
        self.X = self.Y = self.W = 0.0  # game position (2D projection)
        self.scale = 0.0  # scale from camera position
        self.curve = 0.0  # curve radius

        self.spriteX = 0.0  # sprite position X
        self.clip = 0.0
        self.sprite: pygame.Surface = None
        self.sprite_rect: pygame.Rect = None

        self.grass_color: pygame.Color = "black"
        self.rumble_color: pygame.Color = "black"
        self.road_color: pygame.Color = "black"

    def project(self, camX: int, camY: int, camZ: int):
        """
        Calculate how to project the line on the screen in relation to the camera.
        From 3D to 2D.
        """
        self.scale = camD / (self.z - camZ)
        self.X = (1 + self.scale * (self.x - camX)) * WINDOW_WIDTH / 2
        self.Y = (1 - self.scale * (self.y - camY)) * WINDOW_HEIGHT / 2
        self.W = self.scale * roadW * WINDOW_WIDTH / 2

    def drawSprite(self, draw_surface: pygame.Surface):
        """
        Draw the lines sprite(s) on the screen.
        """

        # If there is no sprite, return
        if self.sprite is None:
            return
        # Get the sprite width and height
        w = self.sprite.get_width()
        h = self.sprite.get_height()
        # Calculate the destination X and Y
        destX = self.X + self.scale * self.spriteX * WINDOW_WIDTH / 2
        destY = self.Y + 4
        destW = w * self.W / 266
        destH = h * self.W / 266

        destX += destW * self.spriteX
        destY += destH * -1

        # clip the sprite if below ground (clipH)
        # clipH is the height of the sprite below the ground
        clipH = destY + destH - self.clip
        if clipH < 0:
            clipH = 0
        if clipH >= destH:
            return

        # avoid scalling up images which causes lag
        if destW > w:
            return

        # mask the sprite if below ground (clipH)
        scaled_sprite = pygame.transform.scale(self.sprite, (destW, destH))
        crop_surface = scaled_sprite.subsurface(0, 0, destW, destH - clipH)

        draw_surface.blit(crop_surface, (destX, destY))

def drawQuad(
    surface: pygame.Surface,
    color: pygame.Color,
    x1: int,
    y1: int,
    w1: int,
    x2: int,
    y2: int,
    w2: int,
):
    """
    Draw a polygon with 2 points + widths and a color
    """
    pygame.draw.polygon(
        surface, color, [(x1 - w1, y1), (x2 - w2, y2), (x2 + w2, y2), (x1 + w1, y1)]
    )

class GameWindow:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pseudo 3D Road")
        self.window_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.last_time = time.time()
        self.dt = 0

        self.create_background()
        self.load_sprites()

    def create_background(self):
        """
        Create the background surface
        """

        # load background image and scale it to the window width
        self.background_image = pygame.image.load("src/media/backgroundRepeatable.png").convert_alpha()
        self.background_image = pygame.transform.scale(
            self.background_image, (WINDOW_WIDTH, self.background_image.get_height())
        )
        # create a surface 3 times the width of the background image
        self.background_surface = pygame.Surface(
            (self.background_image.get_width() * 3, self.background_image.get_height())
        )
        # blit the background image 3 times
        self.background_surface.blit(self.background_image, (0, 0))
        self.background_surface.blit(
            self.background_image, (self.background_image.get_width(), 0)
        )
        self.background_surface.blit(
            self.background_image, (self.background_image.get_width() * 2, 0)
        )
        # create a rect for the background surface
        self.background_rect = self.background_surface.get_rect(
            topleft=(-self.background_image.get_width(), 0)
        )
        self.window_surface.blit(self.background_surface, self.background_rect)

    def load_sprites(self):
        """
        Load sprites
        """
        # sprites
        # load sprites named 1.png - xy.png
        self.sprites: List[pygame.Surface] = []
        for i in range(1, 3):
            self.sprites.append(pygame.image.load(f"src/media/{i}.png").convert_alpha())

    def run(self):
        """
        Main game loop and street generation
        """

        # create road lines for each segment
        lines: List[Line] = []
        for i in range(1600):
            line = Line(i)
            line.z = (
                i * segL + 0.00001
            )  # adding a small value avoids Line.project() errors

            # change color at every other 3 lines (int floor division)
            grass_color = light_grass if (i // 3) % 2 else dark_grass
            rumble_color = white_rumble if (i // 3) % 2 else black_rumble
            road_color = light_road if (i // 3) % 2 else dark_road

            line.grass_color = grass_color
            line.rumble_color = rumble_color
            line.road_color = road_color

            # right curve
            if 300 < i < 700:
                line.curve = 0.5

            # uphill and downhill
            if i > 750:
                line.y = math.sin(i / 30.0) * 1500

            # left curve
            if i > 1100:
                line.curve = -0.7

            # Sprites segments
            if i < 300 and i % 20 == 0:
                line.spriteX = -2.5
                line.sprite = self.sprites[1]

            if i % 17 == 0:
                line.spriteX = 2.0
                line.sprite = self.sprites[1]

            if i > 300 and i % 20 == 0:
                line.spriteX = -0.7
                line.sprite = self.sprites[0]

            if i > 800 and i % 20 == 0:
                line.spriteX = -1.2
                line.sprite = self.sprites[0]

            if i == 400:
                line.spriteX = -1.2
                line.sprite = self.sprites[0]


            lines.append(line)

        NumberOfLines = len(lines)
        pos = 0
        playerX = 0  # player start at the center of the road
        playerY = 1500  # camera height offset

        while True:
            self.dt = time.time() - self.last_time
            self.last_time = time.time()
            self.window_surface.fill((135, 206, 235))   # background

            for event in pygame.event.get([pygame.QUIT]):
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            speed = 0
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                speed += segL  # has to be integer times the segment length
            if keys[pygame.K_DOWN]:
                speed -= segL  # has to be integer times the segment length
            if keys[pygame.K_RIGHT]:
                playerX += 200
            if keys[pygame.K_LEFT]:
                playerX -= 200
            if keys[pygame.K_w]: 
                playerY += 100  # up
            if keys[pygame.K_s]:
                playerY -= 100  # down
            # avoid camera going below ground
            if playerY < 500:
                playerY = 500
            # turbo speed
            if keys[pygame.K_TAB]:
                speed *= 2  # has to be integer times the segment length
            pos += speed

            # loop the circut from start to finish
            while pos >= NumberOfLines * segL:
                pos -= NumberOfLines * segL
            while pos < 0:
                pos += NumberOfLines * segL
            startPos = pos // segL

            x = dx = 0.0  # curve offset on x axis

            camH = lines[startPos].y + playerY
            maxy = WINDOW_HEIGHT

            # draw and move background
            if speed > 0:
                self.background_rect.x -= lines[startPos].curve * 2
            elif speed < 0:
                self.background_rect.x += lines[startPos].curve * 2

            # loop the background
            if self.background_rect.right < WINDOW_WIDTH:
                self.background_rect.x = -WINDOW_WIDTH
            elif self.background_rect.left > 0:
                self.background_rect.x = -WINDOW_WIDTH

            self.window_surface.blit(self.background_surface, self.background_rect)

            # draw road
            for n in range(startPos, startPos + show_N_seg):
                current = lines[n % NumberOfLines]
                # loop the circut from start to finish = pos - (NumberOfLines * segL if n >= NumberOfLines else 0)
                current.project(playerX - x, camH, pos - (NumberOfLines * segL if n >= NumberOfLines else 0))
                
                # update curve offset
                x += dx
                dx += current.curve

                current.clip = maxy

                # don't draw "above ground"
                if current.Y >= maxy:
                    continue
                maxy = current.Y

                prev = lines[(n - 1) % NumberOfLines]  # previous line

                drawQuad(
                    self.window_surface,
                    current.grass_color,
                    0,
                    prev.Y,
                    WINDOW_WIDTH,
                    0,
                    current.Y,
                    WINDOW_WIDTH,
                )
                drawQuad(
                    self.window_surface,
                    current.rumble_color,
                    prev.X,
                    prev.Y,
                    prev.W * 1.2,
                    current.X,
                    current.Y,
                    current.W * 1.2,
                )
                drawQuad(
                    self.window_surface,
                    current.road_color,
                    prev.X,
                    prev.Y,
                    prev.W,
                    current.X,
                    current.Y,
                    current.W,
                )
            
            # draw sprites
            for n in range(startPos + show_N_seg, startPos + 1, -1):
                lines[n % NumberOfLines].drawSprite(self.window_surface)

            pygame.display.update()
            self.clock.tick(tick_rate)


if __name__ == "__main__":
    game = GameWindow()
    game.run()
