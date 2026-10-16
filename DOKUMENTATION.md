# Doku VT 2.4.3 – Dokumentation

Die App ist eine Datei (`index.html`, ca. 440 KB), keine Abhängigkeiten, kein CDN, keine Webfonts. Läuft per Doppelklick oder über GitHub Pages. Für Kamera und Live-Abgleich ist **https** nötig (also GitHub Pages), denn Browser geben die Kamera nur in sicheren Kontexten frei.

---

## 1. Architektur

| Modul | Aufgabe |
|---|---|
| `DEPT` (+ `abtOf`, `katName`, `katHex`, `fieldLabel`, `tagHtml`) | **Zentrale Konfiguration der Abteilungen** (ab 2.0.0): je Abteilung Name, Kurzname, Phasennamen, Foto-Phasen, Hauptfeld, Chips, Felder (mit Optionen wie `main`, `plus`, `req`, `extra`, `bool`, `qkeys`), PDF-Spalten und Farben. Editor, Karten, Detail, Bildansicht, Kamera und PDF lesen nur hier. Eine neue Abteilung = ein Eintrag in `DEPT` + `DEPT_ORDER` + drei Farbvariablen im CSS. |
| `Utils`, `Clock`, `ICONS` | Helfer, monotone Uhr für Zeitstempel, Inline-SVG-Icons |
| `Store` | IndexedDB, Stores: `shows`, `entries`, `photos` (nur Metadaten), `fulls`/`thumbs` (Bilddaten als ArrayBuffer), `meta` (Einstellungen, Sync-Zustand und ab 2.4.1 die Durchgänge der Vorstellungs-Checkliste unter `run:<id>`). **Ab 2.4.1 ohne Versionsnummer geöffnet – es gibt nie ein Datenbank-Update** (ein Update wartet auf iPad/iPhone endlos, wenn eine eingefrorene Instanz im Hintergrund die Datenbank offen hält; das war das schwarze Startbild in 2.3.0/2.4.0). Der Speicher `runs` aus 2.3.0/2.4.0 wird, falls vorhanden, weiter gelesen. Antwortet der Speicher nicht, zeigt `Boot.wait()` nach 5 s einen Hinweis; Startfehler zeigt `Boot.fail()`. Alle Schreibvorgänge laufen in **einer atomaren Transaktion**; schlägt ein einzelner Request fehl, bricht die ganze Transaktion ab (ab 2.4.3, vorher wurde der Rest still committet). Ist der Speicher voll, gibt es eine klare Meldung „Es wurde NICHTS gespeichert“. |
| `Rec` | Datensatzformat mit **Zeitstempel je Feld** (`f` = Werte, `t` = Zeiten). Beim Merge gewinnt pro Feld der jüngere Wert. Löschen setzt das Feld `del` (Tombstone). `Rec.patch` vergibt nie einen älteren Zeitstempel als den bisherigen des Felds (ab 2.4.3, Schutz gegen vorgehende Geräteuhren). `Rec.valid` prüft fremde Datensätze: Kennungen nur `[A-Za-z0-9_.:-]` (bis 200 Zeichen), keine Feldnamen `__proto__`/`constructor`/`prototype`, Zeitstempel endliche Zahlen ≥ 0, höchstens 2 000 Felder und 100 000 Zeichen je Text; `Rec.sanitize` entfernt verschachtelte `__proto__`-Schlüssel. Außerhalb von `f`/`t` trägt jeder Datensatz die lokale Eingangszeit `rx` (ab 2.4.3, von `Repo._write` gesetzt, kein Merge-Feld). |
| Papierkorb (`Repo.deletedShows`, `restoreShow`, ab 2.4.2) | Gelöschte Veranstaltungen bleiben als Tombstone erhalten. Wiederherstellen setzt `del: false` mit neuem Zeitstempel für die Veranstaltung und alles, was zusammen mit ihr gelöscht wurde. Ab 2.4.3 trägt jeder Löschvorgang eine Kennung `delGrp` (gleicher Zeitstempel wie `del`); zurück kommt nur, was diese Kennung hat und seitdem nicht neu gelöscht wurde (`t.del ≤ t.delGrp`). Ohne Kennung (gelöscht mit 2.4.2) gilt die alte Regel: Zeitstempel des Löschens ≥ dem der Veranstaltung. `Repo.cleanup` behält die Bilddaten aller Fotos von Veranstaltungen im Papierkorb (`usedBlobs`), die Diagnose fragt vor dem Aufräumen nach (`orphanBlobs`). Der Backup-Import meldet hier gelöschte, im Backup vorhandene Veranstaltungen (`restorable`) und bietet das Wiederherstellen an. |
| `Repo` | Datenzugriff mit RAM-Cache aller Metadaten, Index Eintrag → Fotos, `saveDraft` (nur übergebene Felder der Abteilung – der Editor übergibt ab 2.4.3 bei bestehenden Einträgen nur geänderte Felder und `initialPhotos`, damit live eingegangene Änderungen und Fotos stehen bleiben; zusammengeführt wird bei gleichem Hauptfeld **innerhalb** derselben Abteilung, Bühne nie), `showDepts` (Abteilungen einer Veranstaltung, mit Lese-Migration), `stats(showId, depts)`, `applyRemote` (Import/Sync; prüft mit `Rec.valid`, Bilddaten nur als JPEG), `duplicatesOf(showId, depts)` (nur sichtbare Abteilungen), Aufräumen |
| `Settings` | Geräte-Einstellungen (werden nicht synchronisiert): Theme, Dimmer, Fotoauflösung, **`depts`** (Abteilungen dieses Geräts, Standard `['L']`), Filter- und Mikrofon-Schnelltasten … |
| `Photo`, `Thumbs` | 1:1-Zuschnitt, JPEG-Kompression (Standard 1600 px / 0,82), Vorschau 360 px; LRU-Cache für Object-URLs (max. 500, alte werden freigegeben), Lazy Loading per IntersectionObserver |
| `Camera` | Live-Vorschau 1:1, Auswahl der Rückkamera-Objektive 0,5×/1×/Tele ohne Selfie- und Kombi-Kameras, bei nur einer Rückkamera Zoomstufen (gemerkt in `Settings.cameraId`), Serienaufnahme, Umschalter Aufbau/Einleuchten mit farbigem Sucherrand, Taschenlampe, Fallback auf Mediathek/System-Kamera |
| `Annotator` | Pfeil, Kreis oder Freihand auf ein Foto zeichnen. Das Ergebnis wird als **neues** Foto gespeichert (Bilddaten bleiben unveränderlich und damit sync-sicher). |
| `Lightbox` | Vollbild: Pinch-Zoom, Doppeltipp, Wischen links/rechts (blättert über alle sichtbaren Karten), hoch/runter schließt, große Info-Einblendung |
| `QR`, `QrScan` | Eigener QR-**Generator** (Version 1–40, L/M) und eigener **Decoder** (Finder-Suche, perspektivische Entzerrung, Reed-Solomon-Korrektur). Der Scanner nutzt `BarcodeDetector`, wo vorhanden, sonst den eigenen Decoder. Auf iPad/iPhone gibt es keinen BarcodeDetector, dort ist der eigene Decoder also nötig. |
| `Pdf` | Eigener PDF-1.4-Generator: Helvetica mit WinAnsiEncoding (Umlaute), JPEG per DCTDecode. Aufbau ab 2.4.0, in jeder Abteilung gleich: Deckblatt mit einspaltigem Inhaltsverzeichnis (je Abteilung Kopfzeile mit Spaltennamen und Kapitelseite) → je Abteilung eine **Kapitelseite** (Farbband bei mehreren Abteilungen; Blöcke „Allgemein“, „Vor der Vorstellung“ mit Kästchen zum Abhaken, Bühne „Ablauf“ und „Positionen“ als Tabelle, Licht „Beleuchterzüge“) → Einträge mit Fotos (eine Seite je Eintrag und Phase, Infoblock unten) → **Einträge ohne Fotos kompakt** auf Sammelseiten (gleicher Infoblock, mehrere je Seite, Reihenfolge bleibt). `measure`/`drawBox` für den Infoblock, `paginate` hält Überschriften beim folgenden Block und wiederholt Tabellenköpfe. `buildRun` erzeugt das Protokoll eines Durchgangs. |
| `Legacy` | Import von JSON-Dateien der früheren Lichtdoku-App (`{show, entries}` mit `bilderAufbau`/`bilderEinleuchten` als Data-URLs). Feste IDs aus alten IDs (`lgs-`, `lge-`) und Bildinhalt (`lgb-` + Hash) → wiederholter Import idempotent. Original-JPEGs werden unverändert gespeichert, nur das Vorschaubild wird erzeugt. |
| `Sync` + Adapter | Kern: Pakete bauen und einspielen, Status, Protokoll. `collect({since, showIds, depts})` (ab 2.4.3 nach `rx`, sonst `mod`) und `filterRecs()` beschränken Einträge und Fotos auf Abteilungen; Veranstaltungen gehen immer mit. Paketformat 2 (Feld `depts` im Kopf). Adapter mit gleichem Interface (`id, name, available(), push(), pull()`): `FileAdapter`, `PeerAdapter`/`PeerSession` (WebRTC), `ServerAdapter` (vorbereitet für eine spätere Version) |
| `Kb` | Bildschirmtastatur (ab 2.1.0): misst die Überdeckung über `visualViewport`, setzt `--kb` und `html.kb-open` (nur Innenabstand unten in `.sheet-b`, keine Größenänderung des Blatts), scrollt das aktive Feld samt Beschriftung in den sichtbaren Bereich, hebt kleine Blätter/Dialoge per `transform` an, lässt Textfelder mitwachsen. Android zusätzlich über `interactive-widget=resizes-content` im Viewport. |
| `Ui` | Ebenen mit History-Eintrag (Android-Zurück, Wischgeste und Esc schließen die oberste Ebene), eigene Dialoge, Toasts, Busy-Anzeige |
| `SetupView` | Über der Liste (ab 2.4.0 einheitlich): **„Vor der Vorstellung“** (heutiger Durchgang direkt abhaken; bei Ton/Bühne von selbst aufgeklappt), dann je Abteilung **„Einrichtung · Licht / Ton / Bühne“** mit den Abschnitten „Allgemein“ (`einrichtung`, `einrichtungT`, `einrichtungB`), Licht „Beleuchterzüge“ und Bühne „Ablauf“ und „Positionen“ als kompakte Tabelle (`ztab`, eingeklappt). Bearbeitungsblätter `editL`, `editT`, `editB` (Allgemein + Ablauf), `editP` (Züge & Positionen). Daten im Show-Datensatz: je Zug `z:<id>` = {name, typ licht/buehne, ebene, bereich, hoehe, bestueckung, last, bemerkung, ord, del}, je Ablauf-Schritt `b:<id>` = {abschnitt grund/pause/ende, text, entryId, ord, del} → feldweiser Merge je Zug und je Schritt. Gespeichert wird immer als Ergänzung des alten Werts (`Repo.zugValue`) und nur, was sich geändert hat. |
| `RunList` | Vorstellungs-Checkliste (ab 2.3.0). Punkte im Show-Datensatz als `ci:<id>` = {abt, text, ord, del}; bei Bühne kommen die Ablauf-Schritte (`b:<id>`) dazu. Ein Durchgang ist ein eigener Datensatz (ab 2.4.1 im Store `meta` unter `run:<id>`, davor im Store `runs`) (`showId`, Felder `datum`, `titel`, `del` und je Haken `h:<Punkt>` = {ok, at, dev}) → feldweiser Merge, Haken mehrerer Geräte gehen nicht verloren; `Sync.filterRecs` schickt nur Haken der eigenen Abteilungen. Hausvorlage in `Settings.ciTemplate`. Protokoll über `Pdf.buildRun` (kleiner Textseiten-Schreiber `Pdf._writer`). |
| `Views`, `Editor`, `SyncView`, `PeerView`, `DiagView`, `SettingsView`, `App` | Oberfläche, Routing per Hash (`#/show/<id>`), Ereignis-Delegation |

**Farbsystem (ab 2.0.0):** `[data-abt]` setzt `--da` (Aufbau, dunkel), `--de` (2. Phase, hell), `--dei`/`--dai` (Schrift darauf); `[data-k="A|E|N"]` wählt daraus `--k`, `--ks`, `--ki`. Komponenten benutzen nur `--k`/`--ks`/`--ki` und erben die Abteilung vom nächsten Vorfahren mit `data-abt`. Ohne Abteilung (Leiste bei „Alle“) sind die Werte neutral. Kamera und PDF nehmen die Hex-Werte aus `DEPT[abt].col`.

**Migration (beim Lesen, nie als Massen-Schreibvorgang):** Eintrag ohne `abt` = Licht (`abtOf`). Veranstaltung ohne `abteilungen` = Licht + jede Abteilung, die Einträge hat (`Repo.showDepts`). Gerät ohne `depts` = Licht. Beim Speichern eines bestehenden Eintrags werden leere Felder, die es im Datensatz noch nicht gibt, nicht angelegt und `abt` wird nicht nachgetragen – ein unverändert gespeicherter 1.8.1-Eintrag bekommt keinen neuen Zeitstempel. `abteilungen` wird erst geschrieben, wenn jemand die Auswahl bewusst ändert.

**Bühne – Einrichte-Reihenfolge (ab 2.4.0):** „Von vorne nach hinten und von unten nach oben.“ `Repo.bposOf(e)` liefert die Position eines Bühnen-Eintrags (Zug aus der Zugliste über `zugId`, sonst freie Position mit `ebene`/`bereich`). `Repo.bcmp` sortiert: Bereich (Vorbühne → Portal → Haupt-/Seitenbühne → Hinterbühne), darin Ebene (Unterbühne → Boden → Oben), Platz in der Zugliste (`ord`), „Reihenfolge Umbau“, Name. Die Bühnen-Liste ist nach Bereich gegliedert; Ort einer Position = `ortText()` („Vorbühne · Boden“). Lese-Migration für 2.0/2.1-Einträge ohne `zugId`/`ebene`: „Zug …/OLZ/BGZ/PZ …“ = oben, sonst Boden. Hauptfeld-Sortierung aller Abteilungen über `mainCmp`: erst Nummern, dann Namen nach Wort und Nummer (Ton: 1, 2, 11 … Aux 1 … Video 1).

**Sichtbarkeit:** In einer Veranstaltung erscheinen nur die Abteilungen aus `Repo.showDepts(show) ∩ Settings.v.depts` (`App.visibleDepts`). `App.curAbt()` liefert die Abteilung, nach der sich Beschriftungen richten (gewählte, sonst die einzige sichtbare, sonst keine = „Alle“).

**Abgleich nach Abteilungen:** Sync-Paket: Einträge/Fotos der Geräte-Abteilungen (Option „Komplett, alle Abteilungen“). Live: beide Geräte senden `d` (ihre Abteilungen) in `hello`; `meta` und jede `delta` enthalten nur die Schnittmenge. Ältere Gegenstellen ohne `d` gelten als „nur Licht“. Komplett-Backup: immer alles. Empfangen wird immer alles, was ankommt (Merge wie bisher).

**Datenfluss:** UI → `Repo.saveDraft/patch…` → Cache (ab 2.4.3 sofort, bei Fehler zurückgerollt) → eine IDB-Transaktion → `Repo.emit(change)` → (a) UI zeichnet die Liste debounced neu, **nie während ein Eingabefeld fokussiert ist**; (b) eine offene Live-Verbindung schickt die Änderung sofort als `delta` an das andere Gerät.

**Sync-Konzept:** Jedes Feld trägt seinen eigenen Zeitstempel, Löschungen sind Tombstones, Bilddaten sind unveränderlich (Blob-ID). Ein Merge ist dadurch kommutativ und idempotent: Egal in welcher Reihenfolge und wie oft Pakete eingespielt werden, das Ergebnis ist gleich. Getestet: Ein zweiter Import desselben Backups ergibt „0 neu, 0 geändert“, dazu 500 zufällige Paare auf Kommutativität und Idempotenz.

**Grenzen (ehrlich):** Ändern zwei Geräte *dasselbe* Feld, gewinnt die jüngere Änderung (gewollt). Ein Zug (`z:<id>`), ein Ablauf-Schritt (`b:<id>`) und ein Checklisten-Punkt (`ci:<id>`) ist je **ein** Feld: Ändert Licht die Bestückung und Bühne die Last desselben Zugs, bevor sie abgleichen, gewinnt das ganze Objekt des Jüngeren – die feinere Aufteilung kommt in 2.4.4. Ein inkrementelles Paket („Nur Änderungen“) gilt je Gerät, nicht je Empfänger: Wer an zwei verschiedene Geräte abwechselnd Pakete schickt, sendet besser „Komplett“.

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
- [ ] Kamera öffnet die Rückkamera mit quadratischer Vorschau. Raster und Foto-Nummer sind sichtbar.
- [ ] Serienaufnahme: mehrere Fotos, dann „Fertig“. Speichern ist gesperrt, bis „Fotos werden verarbeitet“ verschwindet.
- [ ] Kamera verweigern → Hinweis plus System-Kamera/Mediathek funktioniert.
- [ ] Taschenlampe (falls angeboten), Umschalter Aufbau/Einleuchten: Sucherrand wechselt zwischen dunkler und heller Abteilungsfarbe.
- [ ] Kameraleiste zeigt nur die Rückseite (iPhone: 0,5× Weitwinkel / 1× Normal / Tele, keine Selfie-Kamera); Pixel: Zoomstufen. Auswahl bleibt beim nächsten Öffnen erhalten.
- [ ] Filter-Schnelltasten: setzen, entfernen, kombinieren (L201+nc).
- [ ] Foto: markieren (Pfeil/Kreis), ersetzen, nach vorn/hinten, in andere Kategorie verschieben, entfernen.

**Ansicht**
- [ ] Ansichtsmodus: Antippen öffnet das Detail, nichts lässt sich versehentlich ändern.
- [ ] iPad quer: Liste links, Detail rechts. iPad hoch und iPhone: Detail als eigene Seite, Zurück-Geste schließt sie.
- [ ] Lightbox: Pinch-Zoom, Doppeltipp, Wischen zum nächsten Kreis, nach unten wischen schließt.
- [ ] Großbild-Ansicht: Fotos groß und scharf; Kreis-Kopfzeile bleibt beim Scrollen oben stehen; Detail öffnet als eigene Seite.
- [ ] Bildansicht: Pfeile links/rechts blättern (Pfeile bleiben an derselben Stelle), auch über Kreise hinweg; „Nächster Kreis“ springt zum nächsten Kreis.
- [ ] Filter Alle/Aufbau/Einleuchten bleibt beim Scrollen sichtbar. Sortierung immer Kreis aufsteigend.
- [ ] Lichtdoku-Datei (alte App) importieren: eigene Veranstaltung, Fotos vollständig; zweiter Import legt nichts doppelt an.
- [ ] Checkliste: abhaken, Fortschritt erscheint, Zurücksetzen funktioniert.
- [ ] Rotlicht, Hell, Dimmer im dunklen Saal ausprobieren.

**PDF & Teilen**
- [ ] PDF teilen: Das Teilen-Menü erscheint mit der Datei (AirDrop, Mail, Dateien).
- [ ] PDF herunterladen: Umlaute stimmen, eine Seite pro Kreis und Kategorie, Inhaltsverzeichnis mit korrekten Seitenzahlen.
- [ ] Kompakt-PDF ist deutlich kleiner.

**Abteilungen (ab 2.0.0)**
- [ ] Update 1.8.1 → 2.0.0 mit bestehenden Daten: Alles ist da, alles ist Licht, Farben sind rot, Sync-Status bleibt „Synchron“ (kein Eintrag gilt als geändert).
- [ ] Gerät nur Licht: Oberfläche wie 1.8.1, keine Abteilungsleiste, „Aufbau / Einleuchten“.
- [ ] Einstellungen → „Dieses Gerät dokumentiert“: alle drei an → Leiste Alle/Licht/Ton/Bühne, bei Alle „Aufbau / Einrichtung“, im Bearbeiten-Modus „+ Licht“, „+ Ton“, „+ Bühne“. Letzte Abteilung lässt sich nicht abschalten.
- [ ] iPhone und Pixel (auch mit großer Systemschrift): Leiste passt ohne waagrechtes Scrollen, Hinzufügen-Knöpfe gestapelt, letzte Karte erreichbar. Kamera-Knopf sitzt unten.
- [ ] Ton-Kanal „17 18“ wird zu „17+18“. Zweiter Eintrag „18+17“ wird zusammengeführt; Licht-Kreis „17+18“ bleibt eigener Eintrag.
- [ ] Bühne: ohne Zug/Position kein Speichern (Hinweis am Feld). Zwei Elemente am selben Zug bleiben getrennt. Checkliste: zwei Haken je Karte.
- [ ] Neue Veranstaltung: Abteilungen vorausgewählt wie das Gerät. „Titel & Details“: Abteilung abwählen → Rückfrage, Einträge nur ausgeblendet.
- [ ] Gerät „nur Bühne“, Veranstaltung „nur Licht“: Hinweis mit Knopf zu den Einstellungen.
- [ ] Sync-Paket von einem Ton-Gerät auf ein Licht-Gerät: Veranstaltung/Einrichtung kommt an, Ton-Einträge sind auf dem Licht-Gerät ausgeblendet; Licht-Einträge des Ton-Geräts wurden nicht übertragen.
- [ ] Sync-Paket 2.0.0 auf einem Gerät mit 1.8.1 einspielen → Meldung „bitte zuerst aktualisieren“.
- [ ] Rotlicht: Aufbau-Streifen schraffiert, 2. Phase gefüllt, Tag mit Abteilungsname.
- [ ] „Allgemeine Einrichtung“ ausgefüllt → pinker Rahmen mit Hinweis-Symbol.
- [ ] PDF „nur Ton“: nur Ton-Seiten, Spalten Kanal/Phase/Quelle/Mikrofon, Dateiname `…_Ton_Datum.pdf`.
- [ ] iPad: Tastatur im Ton- und Bühnen-Editor öffnen und schließen; Felder bleiben antippbar, Speichern oben und unten funktioniert.

**Tastatur (ab 2.1.0)**
- [ ] iPad hoch und quer, iPhone, Pixel: Eintrag öffnen, „Weitere Angaben“ aufklappen, das unterste Feld antippen → Feld und Beschriftung stehen über der Tastatur, das Getippte ist lesbar.
- [ ] Mit „Weiter“ durch alle Felder springen: jedes Feld wird sichtbar.
- [ ] Bemerkung mit mehreren Zeilen: Das Feld wächst mit, der ganze Text bleibt sichtbar.
- [ ] Neue Veranstaltung (Titel), Gerätename und Filter-Schnelltasten in den Einstellungen: Eingabefeld und Knöpfe über der Tastatur und antippbar.
- [ ] Tastatur schließen: Blatt, Kopfzeile, Speichern-Knöpfe, „+ Eintrag“ und Rahmen stehen wieder an ihrem Platz.

**PDF (ab 2.1.0)**
- [ ] Alle Abteilungen: Kapitelseite je Abteilung (Allgemein, Vor der Vorstellung, Ablauf/Positionen bzw. Beleuchterzüge), Inhaltsverzeichnis einspaltig und vollständig lesbar, Seitenzahlen stimmen. Einträge ohne Fotos stehen zu mehreren auf einer Seite.
- [ ] PDF „nur Ton“: kein Farbband, keine Licht-Einrichtung.

**Bühne (ab 2.2.0)**
- [ ] Bühnen-Liste: Abschnitte Vorbühne → Portal → Haupt-/Seitenbühne → Hinterbühne, darin unten → oben. Kein Merksatz mehr.
- [ ] Bühnen-Eintrag: Zug aus der Auswahl wählen; „+ Neuer Zug …“ legt ihn in der Zugliste an; „Freie Position …“ mit Ebene und Bereich. Ohne Auswahl kein Speichern.
- [ ] „Positionen“: Zug nach vorne/hinten schieben, Ebene/Bereich ändern → Reihenfolge der Bühnen-Karten passt sich an. Zug umbenennen → Karten zeigen den neuen Namen. Zug entfernen → „Zug entfernt“.
- [ ] Beleuchterzug auf dem Bühnen-Gerät ändern (z. B. Last) und auf dem Licht-Gerät in „Einrichtung · Licht“ speichern: Die Bühnen-Angaben bleiben erhalten. Per Sync-Paket kommt der Zug auf dem anderen Gerät an, Einträge der fremden Abteilung nicht.
- [ ] „Ablauf“: Schritte in Grundeinrichtung, Pausenumbau, Ende anlegen, verschieben, verknüpfen; Antippen der Verknüpfung öffnet den Eintrag mit Fotos.
- [ ] Ton: „Einrichtung Ton“ eintragen → pinker Rahmen, eigene Seite im PDF.
- [ ] PDF alle Abteilungen: Einrichtungsseiten im jeweiligen Kapitel, Inhaltsverzeichnis mit allen drei.

**Vorstellungs-Checkliste (ab 2.3.0, in der Liste ab 2.4.0)**
- [ ] Veranstaltung mit Ton oder Bühne öffnen: „Vor der Vorstellung“ steht oben und ist aufgeklappt; „Vorstellung heute beginnen“ und direkt abhaken.
- [ ] Haken-Knopf in der Kopfzeile → „Neue Vorstellung“; im **Ansichtsmodus** Punkte abhaken: Uhrzeit und Gerät erscheinen, Fortschritt zählt mit.
- [ ] Bühne: Ablauf-Schritte erscheinen als Punkte in Grundeinrichtung / Pausenumbau / Ende.
- [ ] Licht-Punkte auf dem iPad, Ton-Punkte auf dem Pixel abhaken, Sync-Paket hin und zurück: Alle Haken sind auf beiden Geräten.
- [ ] Bearbeitungsmodus: Punkte bearbeiten, „Als Hausvorlage speichern“ → neue Veranstaltung hat diese Punkte.
- [ ] PDF-Protokoll herunterladen und teilen: offene Punkte pink und am Ende aufgelistet.
- [ ] Update auf 2.4.1 auf dem iPad (auch während Doku VT in Safari oder einem zweiten Fenster offen ist): Die App startet, alle Veranstaltungen, Fotos und Durchgänge sind da.

**Rotlicht (ab 2.4.0)**
- [ ] Rotlicht, Ansicht „Große Bilder“: Kopf mit Kreis/Kanal/Position gut lesbar, Aufbau nur als schraffierte Linie darunter. Feldnamen, Hinweise und graue Texte im dunklen Saal lesbar.

**Papierkorb (ab 2.4.2)**
- [ ] Veranstaltung auf Gerät A löschen, mit B abgleichen: auf B weg. Auf B Backup dieser Veranstaltung importieren → „Wiederherstellen?“ → Ja: Veranstaltung mit allen Fotos zurück. Wieder mit A abgleichen: auch auf A zurück.
- [ ] Startseite → „Papierkorb“ → „Wiederherstellen“.

**Abgleich & Datensicherheit (ab 2.4.3)**
- [ ] Nach dem Update auf jedem Gerät einmal „Sync-Paket senden → Komplett“.
- [ ] Drei Geräte: Eintrag auf dem iPad anlegen, iPad → iPhone (Komplett), iPhone → Pixel („Nur Änderungen“): Der Eintrag ist auf dem Pixel.
- [ ] Veranstaltung löschen, Diagnose → „Speicher aufräumen“: Rückfrage erscheint; danach Papierkorb → Wiederherstellen: alle Fotos sind da.
- [ ] Live iPad ↔ iPhone: auf dem iPad einen Eintrag öffnen, auf dem iPhone denselben Eintrag ändern (Filter) und ein Foto hinzufügen, auf dem iPad die Bemerkung ändern und speichern → Filter und Foto vom iPhone bleiben, Bemerkung vom iPad ist da.
- [ ] „Vor der Vorstellung“: mehrere Punkte sehr schnell hintereinander abhaken, App neu laden → alle Haken sind gespeichert.
- [ ] Gerät mit Uhr auf +1 Tag (manuell gestellt): Titel ändern, Paket an das iPad; dort Titel ändern, Paket zurück → der spätere Titel vom iPad bleibt. Danach Uhr wieder auf automatisch!
- [ ] Live iPad ↔ Pixel mit vielen Fotos (Erstabgleich), währenddessen auf beiden Geräten Einträge speichern → Abgleich wird fertig.

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

0a. **Automatischer Test (neu ab 2.4.3):** `test/test_dokuvt.py` – Python + Playwright (Chromium), ohne pytest lauffähig: `python3 test/test_dokuvt.py` (prüft die App im Ordner darüber), `python3 test/test_dokuvt.py <ordner>` (andere Fassung zum Vergleich), `-k <teil>` (nur passende Tests). Startet selbst einen lokalen Server; jedes Gerät ist ein eigener Browser-Kontext. 34 Prüfungen: Grundfunktionen (Start/Demo, Speichern und Neuladen, Zusammenführen gleicher Kreise, Editor über die Oberfläche, Speichern ohne Änderung schreibt nichts, alle Ansichten ohne Seitenfehler, PDF mit qpdf-Prüfung, Backup zweimal einspielen, Papierkorb, Live-Abgleich per WebRTC zwischen zwei Kontexten, Smartphone-Breite) und die Befunde der Code-Review 2.4.2 (T1–T17: Weitergabe über ein drittes Gerät, Aufräumen mit Papierkorb, gleichzeitige Schreibvorgänge, Editor bei Live-Änderung, falsche Uhr, XSS über Kennungen, einzeln Gelöschtes beim Wiederherstellen, Rückrollen bei Fehler, `__proto__`, defekte Bilder, QR-Fuzz, Merge-Eigenschaften, Duplikate fremder Abteilungen, Live-Senden unter Last, atomare Transaktion, Rückfrage beim Aufräumen). Gegen 2.4.2 schlagen 15 davon fehl. Die frühere Testsuite (bis 148 Prüfungen) ist nicht mehr vorhanden; Teile davon (Tastatur-Nachbildung, Kamera-Farben, Zug-Auswahl) fehlen im neuen Test und kommen in den nächsten Etappen dazu.
13. **Abteilung bestimmt den Farbton, Phase die Darstellung** (Aufbau umrandet/dunkel, 2. Phase gefüllt/hell) – so bleibt alles auch ohne Farbsehen und im Rotlicht über Form und Tag unterscheidbar.
14. **Rot = Licht, deshalb `--danger` Karminrosa** und der Einrichtungs-Rahmen pink mit Symbol. Gefahr ist zusätzlich immer über Symbol und Text erkennbar.
15. **Ton/Bühne schon in 2.0.0 bedienbar:** Der Editor baut sich aus `DEPT`; Licht ergibt dabei exakt das Layout aus 1.7.0. Die Bühnen-Zugauswahl aus der Zugliste und die PDF-Kapitel je Abteilung kommen in den nächsten Etappen.
15b. **Vorstellungs-Durchgänge als eigener Datensatz** (seit 2.3.0) statt im Show-Datensatz: Bei jeder Vorstellung entstehen neue Haken; im Show-Datensatz würde er stetig wachsen und bei jedem Abgleich mitgeschickt. Abhaken ist bewusst auch im Ansichtsmodus möglich – das ist der Zweck der Liste –, Löschen und Bearbeiten der Punkte nicht.
16. **Bühne: Zug/Position als Auswahl** (seit 2.2.0) mit „+ Neuer Zug“ und „Freie Position“; der Name wird als Kopie mitgespeichert, damit PDF und Abgleich auch ohne Zugliste lesbar bleiben.
19. **Bühne nach Bereich gegliedert (seit 2.4.0):** Bühne hat nur Aufbau-Fotos; die Gliederung nach Bereich (vorne → hinten, darin unten → oben) entspricht der Arbeitsweise der Bühnentechnik. Der Merksatz über der Liste ist entfallen – die Reihenfolge ergibt sich aus der Liste selbst.
20. **Ablauf statt Freitext für die Bühne:** Der Zettel der Bühnentechnik (Garland) beschreibt einen Ablauf in Abschnitten – deshalb Schritte statt eines Textfelds. Abhaken pro Vorstellung kommt mit der Vorstellungs-Checkliste (2.3.0), die die Ablauf-Schritte als Punkte nutzen kann.
21. **Bereich als grobe Tiefe:** Für freie Positionen gibt es keinen Zug mit Listenplatz; der Bereich (Vorbühne … Hinterbühne) ordnet sie trotzdem richtig ein. Züge haben zusätzlich ihren Platz in der Liste.
18. **Tastatur ohne Größenänderung des Blatts:** 1.8.0 hatte das Blatt auf die sichtbare Höhe verkleinert – auf dem iPad ließen sich danach keine Felder mehr antippen. Seit 2.1.0 bleibt die Geometrie des Blatts unverändert; nur Inhalt (Innenabstand, Scrollposition) und bei kleinen Blättern ein `transform` ändern sich. Die Gegenprobe im Test (ohne `Kb`) schlägt an, echte Geräte bitte trotzdem prüfen – die iOS-Tastatur lässt sich im Browser-Test nur nachbilden.
17. **Versionierung:** Etappe 1 erscheint als 2.0.0 (statt 1.9.0), weil sich Farbsystem und Paketformat ändern. Die weiteren Etappen: 2.1.0 (Ton/Bühne vollständig, Tastatur), 2.2.0 (Zugliste, Einrichtung je Abteilung, Bühnen-Reihenfolge und -Ablauf), 2.3.0 (Vorstellungs-Checkliste).
0. **Automatischer Test (ab 1.3.0, erweitert in 1.4.0):** 127 Prüfungen (inkl. Import der echten Garland-Datei) in Chromium mit simulierter Kamera – Start, Liste, Filter, Suche, Sortierung, Lightbox, Checkliste, Editor mit Kamera und Schnelltasten, Zusammenführen, Markieren, PDF (qpdf-Prüfung, Umlaute, Seitenzahl), Backup-Import auf zweitem Gerät, Sync-Paket, QR (auch gedreht), WebRTC-Live-Abgleich zwischen zwei Geräten, Einstellungen, iPad hoch und iPhone. Echte Geräte ersetzt das nicht: Safari-Teilen, mehrere Kameras und Taschenlampe bitte auf iPad/iPhone/Pixel prüfen.
12. **Farbiger Rand nur in der Anzeige**, nicht ins Foto eingebrannt. So bleibt ein Foto korrekt, wenn es später in die andere Kategorie verschoben wird, und das PDF zeigt saubere Bilder.

1. **Feld-Zeitstempel statt Eintrags-Zeitstempel.** Wenn zwei Leute denselben Eintrag ändern (einer die Bemerkung, einer den Filter), bleiben beide Änderungen erhalten. Das geht über die Vorgabe „Merge pro Eintrag“ hinaus.
2. **Fotos als eigene Datensätze** statt als Listen im Eintrag. Reihenfolge, Kategorie und Löschung sind einzeln zusammenführbar. Bilddaten sind unveränderlich, deshalb erzeugen Markieren und Ersetzen ein neues Foto. Beim Duplizieren einer Veranstaltung teilen sich die Fotos die Bilddaten und belegen keinen doppelten Speicher.
3. **Einträge ohne Fotos** erscheinen als gestrichelte Karte „Ohne Foto“ in der Abteilungsfarbe (bis 1.8.1 grau) (die Vorgabe sah nur Karten je Kategorie mit Fotos vor). Sonst wären reine Text-Einträge unsichtbar.
4. **Rotlicht-Modus**: Alle Abteilungen erscheinen rot. Unterschieden wird über das Tag (Abteilung · Phase) und die Darstellung: Aufbau schraffiert/umrandet, 2. Phase gefüllt. Fotos werden standardmäßig rot getönt (abschaltbar).
5. **Bearbeitungsmodus** ist durch einen orangen Rahmen um den ganzen Bildschirm deutlich erkennbar. Im Ansichtsmodus sind Anlegen-Knöpfe ausgeblendet, das Abhaken in der Checkliste ist aber erlaubt.
6. **Schnell-Erfassung**: Kamera-Knopf → Fotos (Kategorie direkt in der Kamera wählbar) → Kreis eintippen → Speichern.
7. **Zusammenführen gleicher Kreise** gilt für „123+124“ und „124+123“ gleichermaßen. Bei abweichenden Feldern gewinnt der neue Wert, alte Werte werden im Hinweis genannt, Bemerkungen werden verbunden. Doppelte Kreise, die erst beim Abgleich entstehen, werden markiert und lassen sich über „⋯ → zusammenführen“ bereinigen.
8. **PDF**: 1–2 Fotos groß untereinander, 3–4 Fotos im 2×2-Raster, mehr als 4 auf Fortsetzungsseiten. Fotos sind durchnummeriert (ohne Zusatz „Nah/Totale“). Das Inhaltsverzeichnis zeigt Kreis, Kategorie, Gruppe und Filter und fasst bis 100 Einträge auf einer Seite. Dateiname: Veranstaltung_Datum.pdf.
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
