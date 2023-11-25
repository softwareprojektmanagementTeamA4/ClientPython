import pygame

class Button():
    def __init__(self, txt, x, y, screen):
        self.font = pygame.font.SysFont('Georgia', 24, bold=False)
        self.text = txt
        self.x = x
        self.y = y
        self.screen = screen
        self.button = pygame.rect.Rect(x,y,120,40)

    def draw(self):
        btn = pygame.draw.rect(self.screen, 'light gray', self.button, 0, 5)
        btnrand = pygame.draw.rect(self.screen, 'black', self.button, 5, 5)
        surf = self.font.render(self.text, True, 'black')
        self.screen.blit(surf, (self.x + 10, self.y + 5))