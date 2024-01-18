# Client-Python

## Softwarestruktur:

Im Python Client gibt es 5 Dateien, die das Spiel ausmachen:
-   game.py
-   menue.py
-   road3.py
-   sprites.py
-   util.py


### game.py
Bildet das Front-End des Spiels, welches mit Pygame realisiert wurde. Hier werden diverse Menüs realisiert, darunter der Home-Bildschirm zum connecten mit dem Server, die Settings um Einstellungen zu treffen und das eigentliche Spielfenster. Ebenfalls befindet sich dort auch die Game-Loop, die auf 60 FPS begrenzt ist. In der Game-Loop wird die Funktion run() aufgerufen, die das Programm startet, unter anderem werden auch sämtliche User-Inputs überprüft und darauf entsprechende Funktionen ausgeführt. Außerdem werden verschiedene Socket-IO Events realisiert. Damit bildet die game.py den zentralen Einstiegspunkt für das Spiel.

### menue.py
Ist eine Hilfsklasse für Widgets. Dort wird eine Button Klasse realisiert, die entsprechende Buttons umsetzt und eine Sprite-Klasse TextInputBox. Die update()-Funktion selbst, wird in der Game-Loop 60-mal die Sekunde (FPS) aufgerufen, um die User-Eingaben zu erfassen.

### sprites.py
Sprites.py enthält die verschiedenen Sprites die im Spiel angezeigt werden, diese befinden sich alle auf einem Spritesheet. Sprites des gleichen Typs (Bäume, Auto, Billboards) wurden jeweils in eigene Dictionaries gruppiert. Die Dictionaries enthalten jeweils die x,y Koordinaten des Sprites und beschreiben damit, an welcher Position sich die Sprites auf dem Spritesheet befinden. Die Breite (w) und Höhe (h) geben die Größe des Sprites an, um es entsprechend ausschneiden zu können.

### util.py
Ist eine weitere Hilfsklasse die folgende Klassen definiert:
- Colors: Definiert Farben und Farbtöne für verschiedene Elemente des Spiels (Himmel, Bäume, Straße, Gras,...)
- Background: Definiert die Koordinaten und die Größe des Hintergrunds (Himmel, Hügel, Bäume)
- Game: Ist dafür zuständig, die Sprites aus dem Spritesheet zu schneiden, welche mittels einem Rectangle und ihren definierten Koordinaten, aus dem Sheet extrahiert werden.
- Util: Ist eine Hilfsklasse mit diversen statischen Methoden für allgemeine Zwecke, z.B Typumwandlungen, random Funktionen für z.B Zahlengeneration, eine Beschleunigungsfunktion für das Auto, Maximum, Minimum, Interpolationsfunktion
- Render: Enthält Methoden zum Rendern von Sprites auf dem Bildschirm oder die Darstellung von Straßensegmenten als Polygone. Dabei gibt es auch Funktionen, die jeweils die Sprites noch entsprechend skalieren.