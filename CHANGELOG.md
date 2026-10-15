# Änderungsprotokoll – Doku VT

## 1.8.1 – 15.10.2026

- **Einrichtung & Züge repariert:** Die Tastatur-Anpassung aus 1.8.0 hat das Blatt auf dem iPad zusammengeschoben, sodass sich keine Felder mehr antippen ließen. Sie ist wieder entfernt. Speichern geht bei offener Tastatur über den großen Knopf unten im Formular.
- **Rahmen, „+ Eintrag“ und Kreis-Kopfzeilen bleiben an ihrem Platz:** Nach dem Schließen der Tastatur richtet die App die Ansicht neu aus (iPadOS ließ feste Elemente sonst an der alten Stelle hängen). Die Seite lässt sich nicht mehr versehentlich mit zwei Fingern zoomen; Zoomen in der Bildansicht geht weiterhin.
- **Großbild-Ansicht:** Ecke oben links an jeder Karte sauber (kein Absatz mehr zwischen Rahmen und Kopfzeile). Kopfzeile jetzt wirklich halbtransparent mit Unschärfe dahinter, bleibt beim Scrollen oben stehen.

## 1.8.0 – 15.10.2026

- **PDF-Inhaltsverzeichnis:** zeigt jetzt Kreis, Kategorie, Gruppe und Filter je Zeile. Bis 100 Einträge steht die Liste auf einer Seite (bei vielen Einträgen zweispaltig mit kleinerer Schrift), erst ab 101 Einträgen geht es auf einer zweiten Seite weiter.
- **PDF-Dateiname:** nur noch Veranstaltung und Datum, z. B. `Der_Haifisch_2026-10-15.pdf`.
- **Foto-Beschriftung:** Die Zusätze „Nah“/„Nahaufnahme“ und „Totale“ sind überall entfernt (Liste, Detail, Eintrag, Kamera, PDF). Fotos sind nur noch durchnummeriert.
- **Einrichtung & Züge:** Bei offener Tastatur bleibt die Kopfzeile mit „Speichern“ sichtbar (das Blatt passt sich dem sichtbaren Bereich an). Zusätzlich gibt es unten im Formular einen großen Speichern-Knopf. Ein neu hinzugefügter Zug wird direkt ins Bild gescrollt.
- **Einrichtung & Züge rot umrandet,** sobald unter „Allgemeine Einrichtung“ etwas eingetragen ist.
- **Großbild-Ansicht:** Die blauen/gelben Kopfzeilen und Rahmen sind auf 50 % abgeschwächt und oben abgerundet; Kreis-Nummer in heller Schrift.
- **Bearbeitungsmodus:** farbiger Rahmen um den ganzen Bildschirm statt nur der Linie oben.
- **Bildansicht:** Die Pfeile stehen an fester Stelle und springen nicht mehr je nach Länge der Bemerkung. Beim Blättern gleitet das alte Bild hinaus und das neue – erst wenn es fertig geladen ist – sauber herein; die Nachbarbilder werden vorgeladen. Neuer, leicht transparenter Knopf **„Nächster Kreis“** unten rechts springt direkt zum ersten Foto des nächsten Kreises.

## 1.7.2 – 15.10.2026

- **Live-Abgleich: Diagnose bei Fehlschlag.** Klappt die Verbindung nicht, zeigt die App jetzt, woran es liegt: verschiedene Netze (mit den Adressen beider Geräte), Mobilfunk/VPN, fehlende Adressen, nur verschlüsselte Adressen (…local) oder „selbe Netz, aber blockiert“ (Fritzbox lässt WLAN-Geräte nicht untereinander sprechen). Unter „Technische Details“ steht ein vollständiger Bericht, den man teilen kann. Der erste Hinweis landet auch im Protokoll der Diagnose.
- **Live-Abgleich robuster:** Die Kamera läuft nach dem Scannen weiter, bis die Verbindung steht (Safari gibt die lokalen Netzadressen nur bei aktiver Kamera frei). Beim Anbieten wartet die App, bis die Kamera wirklich läuft, statt pauschal 0,4 s. Ein Abbruch der Verbindungsprüfung wird jetzt auch über den ICE-Status erkannt; Wartezeit 40 s.

## 1.7.1 – 15.10.2026

- **Großbild-Ansicht:** Fotos ragten rechts über den Rahmen hinaus – sie sitzen jetzt mit gleichem Abstand innerhalb der Karte. Die Kreis-Kopfzeile ist eckig und deckt beim Anpinnen die ganze Kartenbreite ab (keine durchscheinenden Ecken mehr).
- **Großbild-Ansicht auf dem Smartphone:** Es wurde nur das erste Foto eines Kreises gezeigt (eine Platzspar-Regel der Listenansicht griff auch hier). Jetzt erscheinen alle Fotos.

## 1.7.0 – 15.10.2026

- **Leiste immer zweizeilig:** Zeile 1 Alle/Aufbau/Einleuchten + Checkliste, Zeile 2 Darstellung + Schalter Ansicht/Bearbeiten – auf jeder Bildschirmbreite und auch bei vergrößerter Systemschrift (z. B. Pixel).
- **Eintrag neu angeordnet:** Kreis und Adresse nebeneinander · Gruppe und Filter nebeneinander, die Filter-Schnelltasten direkt darunter · Bemerkung · Fotos Aufbau/Einleuchten · „Weitere Angaben“ unter den Fotos. Lange Kreise werden im Feld automatisch kleiner geschrieben.
- **Großbild-Ansicht: Kreis immer sichtbar.** Jede Karte hat eine farbige Kopfzeile (Kategorie, Kreis, Anzahl Fotos), die beim Scrollen oben unter der Leiste stehen bleibt, bis der nächste Kreis sie ablöst. Antippen öffnet das Detail.
- **Klarere Trennung zwischen Kreisen** in der Großbild-Ansicht: farbiger Rahmen um jede Karte und deutlich größerer Abstand.

## 1.6.0 – 15.10.2026

- **Import aus der früheren Lichtdoku-App:** Über „Importieren“ lassen sich jetzt auch JSON-Dateien der alten Lichtdoku-App (bis 1.8.x) einlesen. Jede Datei wird zu einer eigenen Veranstaltung. Die Fotos werden verlustfrei übernommen (Original-JPEGs, keine neue Kompression), Bemerkungen und Zeitstempel vollständig, Aufbau-/Einleuchten-Zuordnung 1:1. Kreis-Bereiche wie „531-535“ bleiben unverändert; Filter wie „501 + R119“ werden zu „501+R119“. Ein erneuter Import derselben Datei legt nichts doppelt an. Auch die ältere Fassung (kategorie + bild1/bild2) wird erkannt.
- **Werkzeugleiste aufgeräumt:** Suchleiste und Sortierung nach Gruppe entfernt; sortiert wird immer nach Kreis aufsteigend (Aufbau vor Einleuchten). Zwei Zeilen: Alle/Aufbau/Einleuchten + Checkliste · Darstellung + Schalter Ansicht/Bearbeiten – auch auf dem Smartphone.
- **Bildansicht:** Pfeile sitzen jetzt im unteren Drittel des Fotos (Daumenhöhe).

## 1.5.0 – 14.10.2026

- **Pfeile in der Bildansicht:** Große Pfeile links und rechts zum Blättern, auch auf iPad und Smartphone (bisher nur am Computer). Am Anfang bzw. Ende ist der jeweilige Pfeil ausgegraut. Wischen funktioniert weiterhin.
- **Großbild-Ansicht:** Dritte Darstellung neben Liste und Kacheln. Alle Fotos einer Karte werden groß nebeneinander gezeigt (in voller Auflösung), Infos darunter, Kreis-Nummer rechts. Antippen eines Fotos öffnet die Bildansicht, Antippen der Infos das Detail.
- **Schalter Ansicht ⇄ Bearbeiten:** statt eines Knopfs ein Schiebeschalter; im Bearbeitungsmodus orange.
- **Neue Werkzeugleiste:** Zeile 1 Suche · Zeile 2 Alle / Aufbau / Einleuchten (farbig umrandet: grau, blau, gelb; gewählt = gefüllt) und daneben Checkliste · Zeile 3 Kreis/Gruppe, Darstellung und der Schalter Ansicht/Bearbeiten.

## 1.4.0 – 14.10.2026

- **Einrichtung & Züge** je Veranstaltung: ein Feld „Allgemeine Einrichtung“ und Basisinformationen für OLZ 1, OLZ 2, BGZ 1, BGZ 2 (Höhe/Marke, Bestückung, Bemerkung). Weitere Züge lassen sich hinzufügen und wieder entfernen. Der Bereich steht aufklappbar über der Kreisliste und bekommt im PDF eine eigene Seite (mit Eintrag im Inhaltsverzeichnis). Jeder Zug wird beim Abgleich einzeln zusammengeführt; Duplizieren übernimmt alles.
- **Bildansicht:** Kreis, Kategorie, Felder und Bemerkung sind immer eingeblendet, auch beim Durchwischen. Das Foto wird darüber eingepasst und nicht mehr verdeckt.
- **Kamera – echte Objektive:** Der reine Digitalzoom ist entfernt. Zoomstufen erscheinen nur noch, wenn das Gerät darüber wirklich auf das Weitwinkel-Objektiv umschaltet. Gibt ein Gerät seine Objektive nicht an den Browser frei (z. B. Pixel), zeigt die Kamera das an.
- **Geräte-Kamera:** Neuer Knopf „Geräte-Kamera · alle Objektive“ in der Kamera und in den Einstellungen die Wahl „Fotos aufnehmen mit: Doku-VT-Kamera / Geräte-Kamera“. Die Kamera-App des Geräts erreicht auf jedem Smartphone und Tablet alle Objektive; das Foto landet direkt in der gewählten Kategorie und wird quadratisch zugeschnitten.

## 1.3.1 – 14.10.2026

- **Kamera-Auswahl nur Rückseite:** Zur Wahl stehen die Objektive auf der Rückseite: „0,5× Weitwinkel“, „1× Normal“ und „Tele“. Die Selfie-Kamera ist ausgeblendet, ebenso die virtuellen Kombi-Kameras von iOS („Dual“/„Triple“), die selbst das Objektiv wechseln. Die Kamera startet auf „1× Normal“ oder dem zuletzt gewählten Objektiv. Die Wechseltaste schaltet reihum durch die Rückkameras.
- **Android (z. B. Pixel 8):** Meldet der Browser nur eine Rückkamera, erscheinen stattdessen Zoomstufen (z. B. 0,5× / 1× / 2× / 5×), soweit das Gerät sie anbietet. Darüber wechselt das Telefon selbst das Objektiv.

## 1.3.0 – 14.10.2026

- **PDF-Export repariert:** Die Bezeichnungen in Listen (PDF-Fenster, Einstellungen, Diagnose) hatten dieselbe CSS-Klasse wie die Vollbild-Fotoansicht. Jede Zeile wurde dadurch zu einer schwarzen, bildschirmfüllenden Fläche, und die Knöpfe ließen sich nicht mehr antippen. Die Fotoansicht hat jetzt eine eigene Klasse.
- **Teilen nach PDF, Backup und Sync-Paket:** Ist die Datei fertig, erscheint ein Dialog „Teilen“ / „Öffnen/Sichern“. Safari erlaubt das Teilen nur direkt nach einem Antippen; nach mehreren Sekunden Rechenzeit wurde es vorher blockiert.
- **Sync-Paket:** Die Anzeige „Bilder werden verpackt“ blieb über dem Fertig-Dialog liegen. Behoben. Meldungen (Toasts) verdecken keine Dialog-Knöpfe mehr.
- **PDF:** Lange Werte im Infoblock (z. B. Kreis „12+17+103+113+620“) werden verkleinert statt abgeschnitten.
- **Versionsnummer sichtbar:** in der Kopfzeile der Startseite, unten auf der Startseite, am Ende jeder Kartenliste und in den Einstellungen.
- **Filter-Schnelltasten** im Eintrag: Antippen setzt den Filter, erneutes Antippen entfernt ihn, mehrere werden mit „+“ verbunden. Dazu kommen die in dieser Veranstaltung schon benutzten Filter (gestrichelt). Die feste Liste ist in den Einstellungen unter „Eingabe“ änderbar.
- **Alle Kameras:** Die Kamera zeigt alle Kameras des Geräts zur Auswahl (z. B. Weitwinkel, Ultraweitwinkel, Tele, Vorne). Die Wechseltaste schaltet reihum. Die zuletzt benutzte Kamera wird gemerkt.
- **Farbiger Rand in der Kamera:** Sucher und Vorschaubilder haben einen blauen (Aufbau) oder gelben (Einleuchten) Rahmen. Auch im Eintrag tragen die Fotos den Rand ihrer Kategorie.
- **Kreis-Nummer rechts:** In der Liste steht die Kreis-Nummer in einer festen Spalte am rechten Rand, bei allen Karten auf derselben Höhe.
- **QR-Scanner (iPad/iPhone):** liest Verbindungscodes jetzt auch bei schräg gehaltener Kamera (bis etwa 40°, vorher etwa 15°) und auch sehr kurze Codes.

## 1.2.2 – 14.10.2026

- **Feste App-ID im Manifest** (`id`): Chrome erkennt die App eindeutig. Ein hängengebliebener, fehlerhafter Installationsversuch blockiert keine Neuinstallation mehr.

## 1.2.1 – 14.10.2026

- **Installation repariert:** Die App-Icons liegen jetzt direkt neben `index.html` statt im Ordner `icons/`. Beim Hochladen vom Handy ging der Ordner verloren. Die Folge waren ein graues Platzhalter-Icon und eine App, die sich nach der Installation nicht öffnen ließ.
- **Robuster Offline-Start:** Fehlt einmal ein Icon, richtet sich der Service Worker trotzdem ein.

## 1.2.0 – 14.10.2026

- **Neuer Name:** Aus „Lichtdoku“ wird **Doku VT**, in der Oberfläche, im PDF, in Dateinamen und im App-Icon.
- **Installierbare App (PWA):** Manifest, App-Icons und Service Worker sind dabei. Die App lässt sich auf iPad, iPhone und Android zum Home-Bildschirm hinzufügen und startet danach auch ohne Internet.
- **Update-Hinweis:** Beim Öffnen und beim Zurückkehren in die App wird `version.json` geprüft. Bei einer neueren Version erscheint „Aktualisieren“. Während ein Eintrag offen ist, wird nicht aktualisiert, damit nichts verloren geht.
- **Kompatibel:** Backups, Sync-Pakete und Verbindungscodes aus Lichtdoku 1.0.0 werden weiterhin gelesen. Auch der interne Speicher bleibt gleich. Das hilft aber nur, wenn die App unter derselben Adresse läuft, denn Browser trennen Daten nach Webadresse. Daten von einer anderen Adresse also per Backup übertragen.

## 1.0.0

- Kompletter Neuaufbau (damals „Lichtdoku“): Veranstaltungen und Kreis-Einträge, 1:1-Kamera, Fotos markieren, Lightbox, Suche, Sortierung, Checkliste, eigener PDF-Generator, JSON-Backup, Sync-Paket und Live-Abgleich im WLAN per QR-Code.
