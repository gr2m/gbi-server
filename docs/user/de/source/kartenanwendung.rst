
Kartenansicht
=============

Hier werden Ihnen alle zur Verfügung stehenden Karten- und Hintergrundkarten dargestellt. Über die Auswahl können Sie die Karten ein- bzw. ausblenden. Änderungen an den Daten können hier nicht vorgenommen werden.

Flächeneditor
=============

Mit Hilfe des Flächeneditors können Sie Ihre Daten bearbeiten. Für die Bearbeitung liegen die Daten in verschiedenen Ebenen, so genannten Layern, vor. Sie können neue Layer anlegen, Layer löschen und Geometrien aus anderen Layern, z.B. die Ihnen vom FLOrlp zur Verfügung gestellt werden, kopieren.

.. attention :: Das Löschen eines Layers kann nicht rückgängig gemacht werden!

Das Programm bietet Ihnen die Möglichkeit einen Layer über den internen Flächeneditor oder über einen externen Flächeneditor zu bearbeiten.

Interner Flächeneditor
----------------------

Auf der linken Seite befindet sich die Karte. Über die Layerauswahl können Sie Layer ein- und ausblenden. Oben Links in der Karte befinden sich zwei Schaltflächen, die für das Editieren in der Karte verantwortlich sind. Nach dem Aktivieren des Handsymbols (aktiv wenn gelb hinterlegt) können Sie durch Anklicken von Geometrien diese auswählen.

Durch das Aktivieren des Polygonwerkzeugs ist die Zeichenfunktion aktiviert und Sie können über Klicken in der Karte neue Geometrien in Ihren Layer zeichnen. Um eine Geometrie zu schließen bzw. das Bearbeiten zu beenden muss ein Doppelklick auf dem letzen Punkt der Geometrie ausgeführt werden.

Die rechte Seite des Flächenenditors unterteilt sich in:
  - Suche
  - Fläche bearbeiten
  - Änderungen dauerhaft speichern
  - Eigenschaften

Suche
"""""

Durch Eingabe einer Flurstückskennzeichens in der Form **Gemarkungsnummer-Flurnummer-Zähler/Nenner** und betätigen des `Suchen` Knopfes wird die Karte auf das entsprechenden Flurstück zentriert. Das Flurstückskennzeichens muss mindestens **Gemarkungsnummer-Flurnummer** enthalten.

Fläche bearbeiten
"""""""""""""""""

Die Schaltflächen dieses Bereiches stehen Ihnen nach Auswahl einer Geometrie zur Verfügung. Diese können Sie, wie eben beschrieben, mit Hilfes des Werkzeugs oben links in der Karte auswählen. Welche Geometrie aktiv ist, sehen Sie an der blauen Umrandung einer Geometrie.

Kopieren
  Die ausgewählte Geometrie wird in Ihren Layer kopiert.
  Es können nur Geometrien kopiert werden, die nicht zu Ihrem Layer gehören.

Bearbeiten
  Die derzeit aktive Geometrie kann bearbeitet werden. Sie können diese über den Mittelpunkt verschieben oder die jeweiligen Stützpunkte durch Klicken und Ziehen verschieben.
  Es können nur Geometrien aus Ihrem Layer bearbeitet werden.

Löschen
  Ausgewählte Geometrie löschen. Ein Löschen kann nicht rückgängig gemacht werden.
  Es können nur Geometrien Ihres Layers gelöscht werden.

Änderungen dauerhaft speichern
""""""""""""""""""""""""""""""

Mit diesem Kopf speichern Sie Änderungen Ihres Layer dauerhaft. Dieser Kopf wird aktiv, sobald eine oder mehrere Geometrien Ihres Layers bearbeitet oder hinzugefügt wurden. Wurden Eigenschaften einer oder mehrerer Geometrien bearbeitet, wird der Knopf ebenfalls aktiv.

.. attention:: Alle nicht dauerhaft gespeicherten Veränderungen gehen beim Verlassen oder beim Neuaufruf des Flächeneditors verloren!

Eigenschaften
"""""""""""""

Hier werden die Eigenschaften einer ausgewählten Geometrie angezeigt. Befindet sich die ausgewählte Geometrie in Ihrem Layer, können Sie die Eigenschaften bearbeiten. Um Änderungen zu speichern müssen Sie dies über den Knopf `Eigenschaften speichern` bestätigen.

Externer Flächeneditor
----------------------

Über das Aktivieren des `Externen Flächeneditor über WFS` wird eine WFS-URL generiert über die Sie Zugriff auf Ihren aktuellen Layer mit einem GIS-Programm haben. Unterstützt wird hierbei der WFS-Standard in der Version 1.1.0. DAs Einrichten des WFS in IHrem GIS-Programm entnehmen Sie bitte der dortigen Dokumentation.

Um Änderungen, die in einem externen Editor vorgenommen wurden zu übernehmen, klicken Sie auf `Editieren beenden und Änderungen speichern`. Wollen Sie alle Änderungen verwerfen, klicken Sie auf `Editieren beenden und Änderungen verwerfen`.

Die Seite kann während des Editieren geschlossen werden. Sie können diese Seite wieder aufrufen, indem Sie unter `Flächeneditor wählen` den Layer erneut auswählen und den `Externer Flächeneditor über WFS`-Knopf betätigen.

.. attention:: Während der Nutzung eines Layers in einem externen Editor können Sie den internen Editor nicht verwenden.