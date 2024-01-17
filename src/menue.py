import pygame

"""
Class Button

Erstellt bei Initialisierung  ein Rechteck, was als Button dient.
@:param
txt: Text der auf dem Button stehen soll
x: x Koordinate
y: y Koordinate
screen: Container/Leinwand auf dem der Button gezeichnet werden soll
"""
class Button():
    def __init__(self, txt, x, y, screen, color='light gray'):
        self.font = pygame.font.SysFont('Georgia', 24, bold=False)
        self.text = txt
        self.x = x
        self.y = y
        self.screen = screen
        self.button = pygame.rect.Rect(x,y,150,60)
        self.button.midbottom = (x,y)
        self.color = color

    """
    def draw
    
    Bei Aufruf wird der Button gezeichnet.
    """
    def draw(self):
        btn = pygame.draw.rect(self.screen, self.color, self.button, 0, 5)
        btnrand = pygame.draw.rect(self.screen, 'black', self.button, 5, 5)
        surf = self.font.render(self.text, True, 'black')
        self.screen.blit(surf, (self.button.midleft[0] + 25, self.button.midleft[1] - 15))

"""
Class TextInputBox

Eine Sprite-Klasse, die ein Eingabefeld für den User erstellt.
@:param
x: x Koordinate
y: y Koordinate
w: Breite des Eingabefeldes
font: Die Schriftart, in der die Eingabe dargestellt wird
"""
class TextInputBox(pygame.sprite.Sprite):
    def __init__(self, x, y, w, font):
        super().__init__()
        self.color = (255, 255, 255)
        self.backcolor = None
        self.pos = (x, y)
        self.width = w
        self.font = font
        self.active = False
        self.text = ""
        self.render_text()
        self.enterpressed = False

    """
    def render_text

    Zeichnet den aktuellen Stand der Eingabe.
    """
    def render_text(self):
        t_surf = self.font.render(self.text, True, self.color, self.backcolor)
        self.image = pygame.Surface((max(self.width, t_surf.get_width()+10), t_surf.get_height()+10), pygame.SRCALPHA)
        if self.backcolor:
            self.image.fill(self.backcolor)
        self.image.blit(t_surf, (5, 5))
        pygame.draw.rect(self.image, self.color, self.image.get_rect().inflate(-2, -2), 2)
        self.rect = self.image.get_rect(midbottom = self.pos)

    """
    def update

    Wird in der Gameloop 60-mal die Sekunde aufgerufen, um die Usereingabe zu erfassen und ruft render_text zum Updaten auf.
    @:param
    event_list: Die Eventliste von Pygame, die die benötigten Tastatureingaben speichert
    """
    def update(self, event_list):
        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN and not self.active:
                self.active = self.rect.collidepoint(event.pos)
            if event.type == pygame.KEYDOWN and self.active:
                if event.key == pygame.K_RETURN:
                    self.active = False
                    self.enterpressed = True
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.render_text()