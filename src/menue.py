import pygame

class Button():
    def __init__(self, txt, x, y, screen):
        self.font = pygame.font.SysFont('Georgia', 24, bold=False)
        self.text = txt
        self.x = x
        self.y = y
        self.screen = screen
        self.button = pygame.rect.Rect(x,y,150,60)
        self.button.midbottom = (x,y)

    def draw(self):
        btn = pygame.draw.rect(self.screen, 'light gray', self.button, 0, 5)
        btnrand = pygame.draw.rect(self.screen, 'black', self.button, 5, 5)
        surf = self.font.render(self.text, True, 'black')
        self.screen.blit(surf, (self.button.midleft[0] + 25, self.button.midleft[1] - 15))