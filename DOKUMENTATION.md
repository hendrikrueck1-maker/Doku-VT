# Doku VT 1.5.0 – Dokumentation

Die App ist eine Datei (`index.html`, ca. 245 KB), keine Abhängigkeiten, kein CDN, keine Webfonts. Läuft per Doppelklick oder über GitHub Pages. Für Kamera und Live-Abgleich ist **https** nötig (also GitHub Pages), denn Browser geben die Kamera nur in sicheren Kontexten frei.

---

## 1. Architektur

| Modul | Aufgabe |
|---|---|
| `Utils`, `Clock`, `ICONS` | Helfer, monotone Uhr für Zeitstempel, Inline-SVG-Icons |
| `Store` | IndexedDB, Stores: `shows`, `entries`, `photos` (nur Metadaten), `fulls`/`thumbs` (Bilddaten als ArrayBuffer), `meta`. Alle Schreibvorgänge laufen in **einer atomaren Transaktion**; ist der Speicher voll, gibt es eine klare Meldung „Es wurde NICHTS gespeichert“. |
| `Rec` | Datensatzformat mit **Zeitstempel je Feld** (`f` = Werte, `t` = Zeiten). Beim Merge gewinnt pro Feld der jüngere Wert. Löschen setzt das Feld `del` (Tombstone). |
| `Repo` | Datenzugriff mit RAM-Cache aller Metadaten, Index Eintrag → Fotos, `saveDraft` (inkl. automatischem Zusammenführen gleicher Kreise), `applyRemote` (Import/Sync), Aufräumen |
| `Settings` | Geräte-Einstellungen (werden nicht synchronisiert): Theme, Dimmer, Fotoauflösung … |
| `Photo`, `Thumbs` | 1:1-Zuschnitt, JPEG-Kompression (Standard 1600 px / 0,82), Vorschau 360 px; LRU-Cache für Object-URLs (max. 500, alte werden freigegeben), Lazy Loading per IntersectionObserver |
| `Camera` | Live-Vorschau 1:1, Auswahl der Rückkamera-Objektive 0,5×/1×/Tele ohne Selfie- und Kombi-Kameras, bei nur einer Rückkamera Zoomstufen (gemerkt in `Settings.cameraId`), Serienaufnahme, Umschalter Aufbau/Einleuchten mit farbigem Sucherrand, Taschenlampe, Fallback auf Mediathek/System-Kamera |
| `Annotator` | Pfeil, Kreis oder Freihand auf ein Foto zeichnen. Das Ergebnis wird als **neues** Foto gespeichert (Bilddaten bleiben unveränderlich und damit sync-sicher). |
| `Lightbox` | Vollbild: Pinch-Zoom, Doppeltipp, Wischen links/rechts (blättert über alle sichtbaren Karten), hoch/runter schließt, große Info-Einblendung |
| `QR`, `QrScan` | Eigener QR-**Generator** (Version 1–40, L/M) und eigener **Decoder** (Finder-Suche, perspektivische Entzerrung, Reed-Solomon-Korrektur). Der Scanner nutzt `BarcodeDetector`, wo vorhanden, sonst den eigenen Decoder. Auf iPad/iPhone gibt es keinen BarcodeDetector, dort ist der eigene Decoder also nötig. |
| `Pdf` | Eigener PDF-1.4-Generator: Helvetica mit WinAnsiEncoding (Umlaute), JPEG per DCTDecode, Deckblatt mit Inhaltsverzeichnis und Seitenzahlen |
| `Sync` + Adapter | Kern: Pakete bauen und einspielen, Status, Protokoll. Adapter mit gleichem Interface (`id, name, available(), push(), pull()`): `FileAdapter`, `PeerAdapter`/`PeerSession` (WebRTC), `ServerAdapter` (vorbereitet für eine spätere Version) |
| `Ui` | Ebenen mit History-Eintrag (Android-Zurück, Wischgeste und Esc schließen die oberste Ebene), eigene Dialoge, Toasts, Busy-Anzeige |
| `SetupView` | „Einrichtung & Züge“: Anzeige über der Liste, Bearbeitungsblatt. Daten im Show-Datensatz: `einrichtung` und je Zug ein Feld `z:<id>` (OLZ 1/2, BGZ 1/2 fest, weitere frei) → feldweiser Merge je Zug |
| `Views`, `Editor`, `SyncView`, `PeerView`, `DiagView`, `SettingsView`, `App` | Oberfläche, Routing per Hash (`#/show/<id>`), Ereignis-Delegation |

**Datenfluss:** UI → `Repo.saveDraft/patch…` → eine IDB-Transaktion → Cache → `Repo.emit(change)` → (a) UI zeichnet die Liste debounced neu, **nie während ein Eingabefeld fokussiert ist**; (b) eine offene Live-Verbindung schickt die Änderung sofort als `delta` an das andere Gerät.

**Sync-Konzept:** Jedes Feld trägt seinen eigenen Zeitstempel, Löschungen sind Tombstones, Bilddaten sind unveränderlich (Blob-ID). Ein Merge ist dadurch kommutativ und idempotent: Egal in welcher Reihenfolge und wie oft Pakete eingespielt werden, das Ergebnis ist gleich, und es geht keine neuere Änderung verloren. Getestet ist das so: Ein zweiter Import desselben Backups ergibt „0 neu, 18 unverändert“.

**Ehrliche Einschätzung, was der Browser kann:**
- Direkter Zugriff auf SMB/FTP/USB-Speicher der Fritzbox ist aus dem Browser **nicht möglich**.
- WebRTC ohne Server klappt im selben WLAN mit lokalen Host-Kandidaten. Die Signalisierung läuft per QR-Code (je Gerät einmal scannen). **Grenzen:** Gast-WLANs mit Client-Isolation blockieren das. Safari gibt lokale Adressen erst frei, wenn die Kamera aktiv ist, deshalb startet die App die Kamera vor dem Angebot. Die Live-Verbindung hält nur, solange die App auf beiden Geräten im Vordergrund läuft (iOS pausiert Hintergrund-Tabs).
- Das **Sync-Paket** ist der robusteste Weg: AirDrop (iPad ↔ iPhone), Quick Share (Android), oder für iPad ↔ Android über die Dateien-App auf den **USB-Speicher der Fritzbox (SMB)**. Das funktioniert ohne Internet, aber das Ablegen und Öffnen machst du von Hand.

---

## 2. Testcheckliste (iPad = Hauptgerät, iPhone, Pixel 8)

Vorbereitung: Datei auf GitHub Pages legen (https) und jeweils in Safari bzw. Chrome öffnen. Optional „Zum Home-Bildschirm“.

**Start & Speichern**
- [ ] Erster Start: Die Demo-Veranstaltung „Der Haifisch“ erscheint.
- [ ] Neue Veranstaltung anlegen: Der Titel-Dialog lässt sich überspringen.
- [ ] Eintrag mit allen Feldern speichern, App schließen, neu öffnen: Alles ist noch da.
- [ ] Kreis „123 124“ eintippen → wird beim Verlassen zu „123+124“. Die „+“-Taste funktioniert, die Zahlentastatur erscheint.
- [ ] Doppelten Kreis anlegen: Hinweis „gab es schon – zusammengeführt“, Fotos ergänzt, Bemerkung verbunden.
- [ ] Mit ungespeicherten Änderungen „Abbrechen“ oder Zurück-Geste: Rückfrage erscheint.
- [ ] Während des Tippens erscheinen Änderungen (z. B. Live-Sync): Die Tastatur bleibt offen, nichts flackert.

**Kamera & Fotos**
- [ ] Kamera öffnet die Rückkamera mit quadratischer Vorschau. Raster und Hinweis „Nahaufnahme/Totale“ sind sichtbar.
- [ ] Serienaufnahme: mehrere Fotos, dann „Fertig“. Speichern ist gesperrt, bis „Fotos werden verarbeitet“ verschwindet.
- [ ] Kamera verweigern → Hinweis plus System-Kamera/Mediathek funktioniert.
- [ ] Taschenlampe (falls angeboten), Umschalter Aufbau/Einleuchten: Sucherrand wechselt Blau/Gelb.
- [ ] Kameraleiste zeigt nur die Rückseite (iPhone: 0,5× Weitwinkel / 1× Normal / Tele, keine Selfie-Kamera); Pixel: Zoomstufen. Auswahl bleibt beim nächsten Öffnen erhalten.
- [ ] Filter-Schnelltasten: setzen, entfernen, kombinieren (L201+nc).
- [ ] Foto: markieren (Pfeil/Kreis), ersetzen, nach vorn/hinten, in andere Kategorie verschieben, entfernen.

**Ansicht**
- [ ] Ansichtsmodus: Antippen öffnet das Detail, nichts lässt sich versehentlich ändern.
- [ ] iPad quer: Liste links, Detail rechts. iPad hoch und iPhone: Detail als eigene Seite, Zurück-Geste schließt sie.
- [ ] Lightbox: Pinch-Zoom, Doppeltipp, Wischen zum nächsten Kreis, nach unten wischen schließt.
- [ ] Großbild-Ansicht: Fotos groß und scharf, Detail öffnet als eigene Seite.
- [ ] Bildansicht: Pfeile links/rechts blättern, auch über Kreise hinweg.
- [ ] Filter Alle/Aufbau/Einleuchten bleibt beim Scrollen sichtbar. Sortierung Kreis/Gruppe. Suche über alle Felder.
- [ ] Checkliste: abhaken, Fortschritt erscheint, Zurücksetzen funktioniert.
- [ ] Rotlicht, Hell, Dimmer im dunklen Saal ausprobieren.

**PDF & Teilen**
- [ ] PDF teilen: Das Teilen-Menü erscheint mit der Datei (AirDrop, Mail, Dateien).
- [ ] PDF herunterladen: Umlaute stimmen, eine Seite pro Kreis und Kategorie, Inhaltsverzeichnis mit korrekten Seitenzahlen.
- [ ] Kompakt-PDF ist deutlich kleiner.

**Backup & Sync**
- [ ] Komplett-Backup erstellen, auf einem zweiten Gerät einspielen, dann ein zweites Mal einspielen: Es entsteht nichts doppelt.
- [ ] Sync-Paket iPad → iPhone per AirDrop: Änderungen kommen an, der Status wird „Synchron“.
- [ ] Sync-Paket iPad ↔ Pixel über den Fritzbox-Speicher (Dateien-App bzw. Dateimanager).
- [ ] Live: beide Geräte im Theater-WLAN, „Verbindung anbieten“ und „Code scannen“. Der Abgleich läuft durch, danach erscheint eine Änderung auf A sofort auf B.
- [ ] Live iPad ↔ iPad (beide ohne BarcodeDetector): Der eigene QR-Decoder erkennt den Code.
- [ ] Gleichzeitig auf zwei Geräten denselben Eintrag ändern, unterschiedliche Felder: Beide Änderungen bleiben erhalten.
- [ ] Auf A löschen, abgleichen: Der Eintrag ist auch auf B weg und taucht nicht wieder auf.

**Offline & Robustheit**
- [ ] App zum Home-Bildschirm hinzufügen, einmal öffnen, dann Flugmodus: Die App startet und alles funktioniert.
- [ ] Neue Version hochladen (`APP_VERSION`, `sw.js`, `version.json` erhöhen): Der Hinweis „Aktualisieren“ erscheint, danach ist die neue Version aktiv.
- [ ] Diagnose: Speicher, dauerhafter Speicher, offene Änderungen, Protokoll.

---

## 3. Bewusste Designentscheidungen und Abweichungen

0. **Automatischer Test (ab 1.3.0, erweitert in 1.4.0):** 108 Prüfungen in Chromium mit simulierter Kamera – Start, Liste, Filter, Suche, Sortierung, Lightbox, Checkliste, Editor mit Kamera und Schnelltasten, Zusammenführen, Markieren, PDF (qpdf-Prüfung, Umlaute, Seitenzahl), Backup-Import auf zweitem Gerät, Sync-Paket, QR (auch gedreht), WebRTC-Live-Abgleich zwischen zwei Geräten, Einstellungen, iPad hoch und iPhone. Echte Geräte ersetzt das nicht: Safari-Teilen, mehrere Kameras und Taschenlampe bitte auf iPad/iPhone/Pixel prüfen.
12. **Farbiger Rand nur in der Anzeige**, nicht ins Foto eingebrannt. So bleibt ein Foto korrekt, wenn es später in die andere Kategorie verschoben wird, und das PDF zeigt saubere Bilder.

1. **Feld-Zeitstempel statt Eintrags-Zeitstempel.** Wenn zwei Leute denselben Eintrag ändern (einer die Bemerkung, einer den Filter), bleiben beide Änderungen erhalten. Das geht über die Vorgabe „Merge pro Eintrag“ hinaus.
2. **Fotos als eigene Datensätze** statt als Listen im Eintrag. Reihenfolge, Kategorie und Löschung sind einzeln zusammenführbar. Bilddaten sind unveränderlich, deshalb erzeugen Markieren und Ersetzen ein neues Foto. Beim Duplizieren einer Veranstaltung teilen sich die Fotos die Bilddaten und belegen keinen doppelten Speicher.
3. **Einträge ohne Fotos** erscheinen als graue Karte „Ohne Foto“ (die Vorgabe sah nur Karten je Kategorie mit Fotos vor). Sonst wären reine Text-Einträge unsichtbar.
4. **Rotlicht-Modus**: Kategorien sind dort zusätzlich durch Text-Tags und ein Streifenmuster unterscheidbar, weil Blau und Gelb im Rotlicht nicht mehr erkennbar sind. Fotos werden standardmäßig rot getönt (abschaltbar).
5. **Bearbeitungsmodus** ist durch einen orangen Rand unter der Kopfleiste deutlich erkennbar. Im Ansichtsmodus sind Anlegen-Knöpfe ausgeblendet, das Abhaken in der Checkliste ist aber erlaubt.
6. **Schnell-Erfassung**: Kamera-Knopf → Fotos (Kategorie direkt in der Kamera wählbar) → Kreis eintippen → Speichern.
7. **Zusammenführen gleicher Kreise** gilt für „123+124“ und „124+123“ gleichermaßen. Bei abweichenden Feldern gewinnt der neue Wert, alte Werte werden im Hinweis genannt, Bemerkungen werden verbunden. Doppelte Kreise, die erst beim Abgleich entstehen, werden markiert und lassen sich über „⋯ → zusammenführen“ bereinigen.
8. **PDF**: 1–2 Fotos groß untereinander, 3–4 Fotos im 2×2-Raster, mehr als 4 auf Fortsetzungsseiten. Fotos sind mit „Nah/Totale“ beschriftet.
9. **PWA** (seit 1.2.0 aktiv): Manifest und Apple-Touch-Icon sind fest eingebunden. Der Service Worker liefert die App aus dem Cache und lädt neue Fassungen im Hintergrund nach (stale-while-revalidate). `version.json` wird immer frisch vom Server geholt.
10. **Kreis-Feld nutzt `inputmode="tel"`**, weil das die Zahlentastatur mit „+“ liefert. Zusätzlich gibt es eine große „+“-Taste (handschuhtauglich). Leerzeichen und Komma werden automatisch zu „+“.
11. **Demo**: Jedes Gerät legt beim ersten Start seine eigene Demo an. Nach einem Abgleich gibt es sie daher zweimal. Einfach eine löschen, oder in den Einstellungen „Demo beim ersten Start“ ausschalten.

---

## 4. Ausblick (nächste Versionen)

**PWA-Paket: in 1.2.0 umgesetzt.** Manifest, Icons, Service Worker und Update-Hinweis über `version.json` sind enthalten. Wichtig für die Datensicherheit auf dem iPad: die App über „Zum Home-Bildschirm“ installieren.

**Bester Sync-Weg fürs Theater-Netz:** ein kleiner Sync-Server auf einem Raspberry Pi oder NAS im Fritzbox-Netz.
- Der Server nimmt per `POST /api/sync` genau das heutige Paketformat an, speichert es, führt es mit derselben Logik zusammen und gibt die Änderungen der anderen Geräte zurück. Das ist der vorbereitete `ServerAdapter`.
- Damit wird Abgleich zu „App öffnen → automatisch“, ohne QR-Codes und ohne Handarbeit. Es funktioniert iPad ↔ Android gleichermaßen, im Theater ohne Internet.
- Hürde: Kamera und PWA brauchen https. Entweder läuft die App selbst vom Pi über https (eigenes Zertifikat auf jedem Gerät einmal vertrauen), oder die App kommt von GitHub Pages und der Pi spricht https mit einem gültigen Zertifikat (z. B. über eine eigene Domain mit DNS-Challenge). Ein reiner http-Server im LAN wird von einer https-Seite aus blockiert (Mixed Content).
- Optional als weiterer Adapter: **WebDAV** (z. B. auf einer NAS). Er braucht eine CORS-Konfiguration, die die Fritzbox selbst nicht bietet; ein NAS kann das. **Google Drive** würde ich nur noch als optionalen Backup-Adapter anbieten, nicht als Hauptweg.

**Weitere Ideen:** Text-Inhalte im PDF komprimieren (Flate); QR-Signalisierung zusätzlich über NFC (Android); Mehrfachauswahl, um Einträge zu verschieben; Filter nach „noch nicht aufgebaut“.

---

## Hinweis zum Namen
Intern heißen Speicher und Paketformat weiterhin `lichtdoku`. Dadurch bleiben Backups, Sync-Pakete und Verbindungscodes aus Version 1.0.0 lesbar.

---

## Kamera-Objektive im Browser – was geht

Ob eine Web-App die einzelnen Objektive (Ultraweitwinkel, Normal, Tele) ansteuern kann, entscheidet der Gerätehersteller, nicht die App:
- **iPhone/iPad (Safari):** Die Objektive sind einzeln verfügbar → Auswahl direkt in der Doku-VT-Kamera.
- **Android mit einzeln freigegebenen Kameras (oft Samsung):** ebenfalls direkte Auswahl.
- **Android mit „logischer“ Kamera (z. B. Pixel):** Der Browser sieht nur eine Rückkamera. Nur wenn sie Zoom unter 1× meldet, schaltet Doku VT darüber auf Weitwinkel; sonst ist das Weitwinkel für Web-Apps nicht erreichbar.
- **Auf jedem Gerät:** „Geräte-Kamera“ (Kamera-App des Herstellers) – dort sind alle Objektive verfügbar.
