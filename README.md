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

### Road3.py
In der Road.py befindet sich die Logik für das Rennen. Dazu gehört die Hauptschleife in dem das Rennen stattfindet. Sie besteht aus mehreren Abschnitten. Am Anfang werden wichtige imports und Variablen bestimmt. In der Klasse GameWindow läuft das Spiel ab. Die Road3 nutzt Pygame für das darstellen und die Inputs des Spiels.
Wichtige Methoden sind:

Über die Runmethode wird das Spiel gestartet. Die Game.py gibt ihr wichtige Parameter, wie die Socketverbindung und den online- bzw. offlinemodus mit.
Im laufe der Methode wird das Setup des Spiels über verschiedene Resetmethoden abgeschlossen und anschließend wird die Hauptschleife gestartet. Zu den Resetmethoden gehören zum einen das erstellen des Spielstandes und zum anderen das Laden der verschiedenen Bilder. Je nachdem ob der Client der Hostclient ist, oder nicht erstellt und sendet er die Daten der NPC-Autos, sowie die Startpositionen der einzelnen Spieler an die anderen Clients.

In der Hauptschleife wird die Framemethode ausgeführt. In der Framemethode wird die aktuelle Zeit gespeichert und die Update- sowie Render- Methoden werden durchgeführt.

In der Updatemethode wird der Spielstand aktualisiert. Inputs werden eingelesen, Geschwindigkeiten und Positionen von Spielern und NPCAutos werden je nach Spielstand aktualisiert und wichtige daten werden an den Server gesendet. Die NPCAutos werden nur von dem Hostclient aktualisiert und anschließend an den Server geschickt. Der Server ist hier nur ein Kommunikationstunnel zwischen den Clients. Die Logik des Spiels wird auf den Clients selbst durchgeführt.

In der render Methode wird der aktuelle Spielstand über Pygame angezeigt. Diese nutzt die Renderklasse der Util.py. Gerendert werden Spieler, Hintergründe, die Strecke, Streckensprites und NPCAutos.

Ein Abschnitt der Road3.py sind die Serverevents. Es gibt Funktionen um bestimmte Daten wie die Spielerposition und NPC Daten an den Server zu schicken und es gibt Funktionen, die vom Server aufgerufen werden um Daten an die Clients zu schicken. Die Clients werten die Daten aus und speichern wichtige Daten ab. Da die Events vom Server asynchron zu dem Hauptspiel ausgeführt werden, werden Mutexlocks verwendet um zu verhindern, dass auf bestimmte Daten parallel zugegriffen wird.

Um die Strecke zu speichern nutzen wir ein Array von Dictionarys. In jedem Dictionary werden Werte für bestimmte Koordinaten gespeichert. Geneu so werden auch die Daten über andere Spieler gespeichert.
