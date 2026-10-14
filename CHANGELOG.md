# Änderungsprotokoll – Doku VT

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
