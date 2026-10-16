# Änderungsprotokoll – Doku VT

## 2.2.0 – 16.10.2026

Etappe 3: gemeinsame Zugliste und Einrichtung je Abteilung – mit der Arbeitsweise der Bühnentechnik.

- **Einrichte-Reihenfolge Bühne:** „Erst unten, dann oben – jeweils von vorne nach hinten.“ Jede Bühnen-Position hat eine **Ebene** (Unterbühne, Boden / Podium, Oben / Züge) und einen **Bereich** (Vorbühne, Portal, Hauptbühne, Seitenbühne, Hinterbühne). Liste, Checkliste und PDF folgen dieser Reihenfolge automatisch: Ebene, dann Bereich, dann Platz in der Zugliste, dann „Reihenfolge Umbau“. Die Bühnen-Liste ist nach Ebene gegliedert, die Regel steht darüber.
- **Gemeinsame Zugliste:** Beleuchterzüge (OLZ, BGZ …) und Bühnenzüge/Positionen (frei benennbar, z. B. „Zug 14“, „PZ 8“, „PR 11“) in einer Liste, von vorne nach hinten sortierbar, mit Ebene, Bereich, Höhe/Marke, Last und Bemerkung. Beide Abteilungen sehen und bearbeiten alle Züge; jeder Zug wird beim Abgleich einzeln zusammengeführt. Licht- und Bühnen-Angaben desselben Zugs überschreiben sich nicht gegenseitig.
- **Zug-Auswahl im Bühnen-Eintrag:** großes Auswahlfeld mit allen Zügen (Beleuchterzüge gekennzeichnet), „+ Neuer Zug …“ (wird sofort in die Zugliste aufgenommen und gewählt) und „Freie Position …“ mit Textfeld, Ebene und Bereich. Ohne Zug oder Position kein Speichern. Umbenannte Züge erscheinen überall mit neuem Namen; ein entfernter Zug behält den gespeicherten Namen und zeigt „Zug entfernt“.
- **Bühnen-Ablauf** in drei Abschnitten **Grundeinrichtung · Pausenumbau · Ende / Abbau**: Schritte anlegen, umsortieren, entfernen und mit einem Bühnen-Eintrag verknüpfen (Fotos per Antippen). Pinker Rahmen, sobald ein Ablauf eingetragen ist.
- **Einrichtung je Abteilung** über der Liste: Licht „Einrichtung & Züge“ (wie bisher, nur Beleuchterzüge), Ton „Einrichtung Ton“ (Freitext), Bühne „Ablauf & Positionen“. Bei „Alle“ untereinander.
- **PDF:** Einrichtungsseiten je Abteilung im jeweiligen Kapitel (Bühne mit Regel, Ablauf je Abschnitt inkl. Seitenverweis auf verknüpfte Einträge und Zug-/Positionsliste unten → oben). Inhaltsverzeichnis mit allen Einrichtungsseiten. Pfeile und ähnliche Zeichen aus dem Text erscheinen lesbar (z. B. „->“) statt als „?“.
- **Duplizieren** übernimmt Ton-Einrichtung und Bühnen-Ablauf (Verknüpfungen zeigen auf die kopierten Einträge).
- **Bühnen-Einträge aus 2.0/2.1** (Zug nur als Text) bleiben unverändert; beim Lesen gilt „Zug …“ als oben, alles andere als Boden. Über die Zug-Auswahl lassen sie sich einem Zug zuordnen.
- Smartphone: Im Editor-Kopf ist „Abbrechen“ ein ×, damit der Titel Platz hat.
- Demo „Der Haifisch“ mit Bühnen-Ablauf, Bühnenzug, Podium und Ton-Einrichtung.

## 2.1.0 – 16.10.2026

Etappe 2: Ton und Bühnentechnik vollständig im PDF, und die Tastatur verdeckt keine Eingabefelder mehr.

- **Tastatur verdeckt keine Felder mehr:** Das Feld, in das getippt wird, wird automatisch über die Tastatur geschoben – mit Beschriftung, damit man sieht und korrigieren kann, was man schreibt. Das gilt im Eintrag (auch für die Felder unter „Weitere Angaben“ ganz unten), in „Einrichtung & Züge“, beim Anlegen einer Veranstaltung und in Dialogen mit Eingabefeld.
  - iPad/iPhone: Das Blatt behält seine Größe (Lehre aus 1.8.0). Der Inhalt bekommt nur unten Platz in Tastaturhöhe und wird gezielt gescrollt; kleine Blätter und Dialoge werden angehoben. Nach dem Schließen der Tastatur ist alles wieder wie vorher.
  - Android (Pixel): Die Seite wird bei offener Tastatur kleiner (`interactive-widget=resizes-content`), dadurch scrollt das Blatt von selbst richtig.
  - **Bemerkung und andere mehrzeilige Felder wachsen mit dem Text mit**, bis etwa zur halben Bildschirmhöhe – der ganze Text bleibt zum Gegenlesen sichtbar.
- **PDF mit Kapiteln je Abteilung:** Bei mehreren Abteilungen beginnt jede mit einer Trennseite in Abteilungsfarbe (Name, Anzahl der Einträge und Seiten je Phase). Das Inhaltsverzeichnis ist nach Abteilung gegliedert, jede Abteilung mit eigener Kopfzeile und eigenen Spalten (Licht: Kreis, Phase, Gruppe, Filter · Ton: Kanal, Phase, Quelle, Mikrofon · Bühne: Zug, Phase, Element, Höhe) und der Seitenzahl ihrer Trennseite. Die Grenze von 100 Einträgen je Inhaltsseite und die zweispaltige Darstellung bleiben.
- **„Einrichtung & Züge“ im PDF** steht im Kapitel Beleuchtung und fehlt in einem PDF ohne Licht (z. B. „nur Ton“).
- Editor-Kopf auf dem Smartphone: kürzerer Titel, die Abteilung steht im Tag davor.

## 2.0.0 – 16.10.2026

Erste Etappe der Erweiterung um **Ton** und **Bühnentechnik**. Ein Gerät, das nur Licht dokumentiert, sieht fast aus wie 1.8.1 – nur in Rot.

- **Abteilungen:** Licht (Rot), Ton (Blau), Bühne (Grau). Alles, was eine Abteilung ausmacht – Felder, Beschriftungen, Phasen, Hauptfeld, Farben –, steht an einer Stelle im Code (`DEPT`). Phasen: Licht Aufbau/Einleuchten, Ton Aufbau/Soundcheck, Bühne nur Aufbau (Fotos) mit zwei Haken (Aufbau, Einrichten).
- **Neues Farbsystem:** Die Abteilung bestimmt den Farbton, die Phase die Darstellung: Aufbau dunkel und umrandet, 2. Phase hell und gefüllt. Jede Karte trägt ein Tag „LICHT · AUFBAU“ (schmal: „L · AUFBAU“). Das bisherige Blau/Gelb entfällt.
- **Ohne Foto:** gestrichelte Karte in der Abteilungsfarbe statt grau (Grau gehört jetzt der Bühne).
- **Warnfarbe:** Löschen und Fehler in Karminrosa, klar vom Licht-Rot abgesetzt. Der Rahmen um „Einrichtung & Züge“ ist pink und hat ein Hinweis-Symbol.
- **Rotlicht:** Alle Abteilungen in Rottönen; Aufbau schraffiert, 2. Phase gefüllt, dazu das Tag mit dem Abteilungsnamen.
- **Dieses Gerät dokumentiert:** neue Gruppe in den Einstellungen (Licht, Ton, Bühne; mindestens eine). Bestehende Installationen: nur Licht.
- **Abteilungen je Veranstaltung:** Beim Anlegen Titel und drei große Umschalter (vorausgewählt: die Abteilungen des Geräts). Änderbar unter „Titel & Details bearbeiten“; Abwählen blendet nur aus, mit Rückfrage. Sichtbar ist die Schnittmenge aus Veranstaltung und Gerät; ist sie leer, erscheint ein Hinweis mit Knopf zu den Einstellungen.
- **Werkzeugleiste:** Bei mehr als einer sichtbaren Abteilung zusätzlich die Leiste „Alle / Licht / Ton / Bühne“ mit Zählern. Die Phasen heißen je nach Abteilung, bei „Alle“ „Aufbau / Einrichtung“; bei Bühne entfällt der Phasen-Filter.
- **Hinzufügen:** Bei mehreren Abteilungen „+ Licht“, „+ Ton“, „+ Bühne“ in Abteilungsfarbe (auf dem Smartphone gestapelt). Die Kamera-Taste fragt bei „Alle“ kurz nach der Abteilung.
- **Liste:** Sortierung Abteilung → Phase → Hauptfeld; Abschnitte „Licht · Aufbau“, „Ton · Soundcheck“ … Rechte Spalte zeigt Kreis / Kanal / Zug. Bildansicht: „Nächster Eintrag“ statt „Nächster Kreis“.
- **Ton und Bühne – erster Stand:** Editor aus `DEPT` gebaut (Licht unverändert). Ton: Kanal wird wie Kreis zu „17+18“, gleiche Kanäle werden zusammengeführt (getrennt von Licht), Mikrofon-Schnelltasten (Einstellungen → Eingabe). Bühne: Zug/Position ist Pflichtfeld, gleiche Züge werden nicht zusammengeführt. Zug-Auswahl aus der Zugliste folgt in einer späteren Etappe.
- **Speichern-Knopf zusätzlich unten** im Eintrag (wie bei „Einrichtung & Züge“).
- **Abgleich, Paketformat 2:** Sync-Paket und Live-Abgleich übertragen Veranstaltungen (mit Einrichtung und Zügen) immer, Einträge und Fotos nur der Abteilungen dieses Geräts; beim Live-Abgleich die Schnittmenge beider Geräte. Neue Option „Komplett, alle Abteilungen“. Das Komplett-Backup enthält weiterhin alles. 1.8.1 lehnt Pakete im Format 2 mit „bitte zuerst aktualisieren“ ab.
- **PDF:** Farben und Plakette je Abteilung („TON · SOUNDCHECK“), Infoblock und Inhaltsverzeichnis mit den Feldern der Abteilung; im Dialog Auswahl der Abteilung. Dateiname bei einer einzelnen Abteilung z. B. `Der_Haifisch_Ton_2026-10-16.pdf`.
- **Daten bleiben unverändert:** fehlende Angaben (Abteilung, Abteilungen der Veranstaltung) gelten beim Lesen als Licht. Gespeichert wird nur, was sich ändert – leere neue Felder werden nicht angelegt, kein bestehender Eintrag gilt nach dem Update als „geändert“.
- **Behoben:** Der Kamera-Knopf (Schnell-Erfassung) rutschte wegen eines CSS-Namenskonflikts mit der Vollbild-Kamera nach oben links hinter die Kopfzeile. Er sitzt jetzt unten neben „+ Eintrag“.
- **Demo „Der Haifisch“** mit allen drei Abteilungen (ein Ton-Kanal, zwei Bühnen-Einträge).

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
