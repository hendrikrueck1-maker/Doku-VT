# Änderungsprotokoll – Doku VT

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
