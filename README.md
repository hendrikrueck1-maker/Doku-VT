# Doku VT – Technikdokumentation

**Version 2.9.0** · Web-App für die technische Dokumentation im Theater – Beleuchtung, Ton, Bühnentechnik und Requisite: Einträge mit Fotos, Abläufe zum Abhaken, PDF-Export und Geräte-Abgleich. Dazu **Cue-Fotos**: Lichtstimmungen vom Stellwerk aus fotografieren und als PDF ablegen. Die App läuft komplett offline, braucht keine Anmeldung und keinen Server.

## Auf GitHub veröffentlichen

1. Neues Repository auf GitHub anlegen, z. B. `doku-vt`.
2. Den **Inhalt** dieser ZIP-Datei in das Repository hochladen, also alle Dateien direkt ins Hauptverzeichnis. Es gibt keine Unterordner, deshalb klappt das auch vom Handy aus. Im Browser: *Add file → Upload files*, Dateien hineinziehen, *Commit changes*.
   - Hinweis: `.nojekyll` ist eine versteckte Datei und wird beim Entpacken auf Mac oder iPad oft nicht angezeigt. Sie ist nicht zwingend nötig.
3. *Settings → Pages → Build and deployment*: Source **Deploy from a branch**, Branch **main**, Ordner **/ (root)**, *Save*.
4. Nach etwa einer Minute ist die App erreichbar unter `https://<benutzername>.github.io/doku-vt/`.

## Auf iPad, iPhone und Android installieren

- **iPad/iPhone (Safari):** Seite öffnen → Teilen-Symbol → **Zum Home-Bildschirm**.
- **Android (Chrome):** Seite öffnen → Menü ⋮ → **App installieren** bzw. **Zum Startbildschirm hinzufügen**.

Installiert startet Doku VT auch ohne Internet, und der Browser behandelt die Daten als dauerhaft. Gerade auf dem iPad ist das wichtig: Safari kann Daten nicht installierter Webseiten nach längerer Nichtnutzung löschen.

## Abteilungen einstellen

Unter *Einstellungen → Dieses Gerät dokumentiert* festlegen, welche Abteilungen das Gerät führt (Standard nach dem Update: nur Licht). Jede Veranstaltung hat zusätzlich eigene Abteilungen. Sichtbar ist, was beide gemeinsam haben. Beim Abgleich gibt jedes Gerät ab 2.8.3 alles weiter, was es hat (Licht, Ton, Bühne – auch Einträge anderer Geräte), die Requisite nur an Geräte mit Requisite. Die Reihenfolge der Abgleiche ist damit egal.

Die Daten liegen **nur lokal auf dem jeweiligen Gerät** (IndexedDB). Das Repository enthält keine Daten. Regelmäßig über *Abgleich → Komplett-Backup* sichern und das Backup auf einem zweiten Ort ablegen (z. B. Fritzbox-Speicher).

## Stückdaten, Besetzung, Zuständige (ab 2.9.0)

Anlegen und Bearbeiten nutzen **ein Formular** (Titel antippen oder ⋯ → „Stückdaten bearbeiten“, nur im Bearbeitungsmodus). Unter **„Mehr Angaben“** – alles optional:

- **Dauer** – gilt jetzt für alle Abteilungen (bei der Requisite dasselbe Feld wie bisher).
- **Besetzung** – beim Anlegen Personen aus dem Ensemble antippen und die Rolle dazuschreiben, oder „+ Person“. Beim Bearbeiten über „Besetzung bearbeiten“. In der Requisite heißen sie weiter „Personen“.
- **Zuständig** – je Abteilung ein Name (z. B. „Hendrik“). Steht in der Veranstaltung über den Kästen („Zuständig: Hendrik · Dauer 1:40“), auf der Kapitelseite im PDF und in der Fußzeile jeder Seite der Abteilung.
- **Notiz**, beim Bearbeiten außerdem **Abgespielt**.

**Abgespielt:** ⋯ → „Als abgespielt markieren“. Das Stück verschwindet von der Startseite und steht unten unter **„Abgespielt (n)“**. Nichts wird gelöscht, abgeglichen wird weiter; „Wieder in den Spielplan“ holt es zurück.

**Gastspiel / Abstecher:** Im Formular unter „Nur auf diesem Gerät“ → **„Alle Abteilungen dieses Stücks hier anzeigen“**. Gilt nur für dieses Stück und nur auf diesem Gerät, „Dieses Gerät dokumentiert“ bleibt, wie es ist. Solange das bei einem Stück mit Requisite eingeschaltet ist, bekommt das Gerät beim Abgleich die Requisite aller Stücke (angezeigt wird sie nur im Gastspiel-Stück).

**Mischbetrieb:** 2.9.0 und 2.8.x gleichen ohne Einschränkung miteinander ab – Geräte können auch erst Tage später aktualisiert werden. Ausblenden abgespielter Stücke und die Zuständigen sind nur auf Geräten mit 2.9.0 sichtbar; ältere Geräte tragen die Angaben unverändert weiter.

## Vorstellungs-Checkliste: Spieltag (ab 2.8.3)

„Heute“ wechselt erst um **4 Uhr morgens**. Wer nach Mitternacht abbaut und abhakt, bleibt im Durchgang des Vorabends. Beginnen zwei Geräte unabhängig voneinander, wird daraus beim Abgleich **ein** Durchgang. **Alle Geräte auf 2.8.3 aktualisieren** – erst dann greift das vollständig (Züge: Licht-Bestückung und Bühnen-Last am selben Zug bleiben beide erhalten).

## Cue-Fotos (ab 2.8.0)

Startseite → **Cue-Fotos**. Je Probe oder Vorstellung eine Cue-Liste anlegen (Stück, Spielstätte, Datum). In den Bearbeitungsmodus schalten, dann:

- **Live:** „Kamera“. Der Auslöser macht das nächste Bild der angezeigten Cue (A, B, C …). „Nächster Cue“ springt zur nächsten vorbereiteten Cue bzw. zur nächsten ganzen Nummer (12.5 → 13) und löst aus. Nummer oben antippen = ändern.
- **Punktstimmungen (ab 2.8.2):** In der Kamera über „Nächster Cue“ die Knöpfe **−0.1 / +0.1** (13 → 13.1 …). Die Cue entsteht mit dem ersten Foto.
- **Vorbereiten:** „+ Cue“ (mit Schnellauswahl: nach Cue 13 stehen 14 · 15 · 16 und 13.1 … 13.9 zum Antippen bereit) oder „Mehrere“ (z. B. 1–40), später fotografieren.
- Notiz und Hinweis je Bild; Markieren wie bei den Doku-Fotos, das Original bleibt erhalten.
- **PDF:** Deckblatt mit Übersicht, dann ein Foto je Seite (A4 hoch). Danach lässt sich die Liste löschen – „endgültig“ gibt den Speicher frei.

**Wichtig:** Ein Paket mit Cue-Fotos hat Format 4. **Alle Geräte, die miteinander abgleichen, zuerst auf 2.8.0 aktualisieren** – 2.7.0 lehnt es mit „bitte zuerst aktualisieren“ ab.

## Licht, Ton, Bühne: Reihenfolge über der Liste (ab 2.8.1)

Hinweis Einrichten → Vor der Vorstellung (feste Punkte und Ablauf „vorher“) → Ablauf (während, Pause, danach – abhakbar) → Beleuchterzüge bzw. Positionen. Bei Licht gibt es unter „Weitere Angaben“ das Feld **Sub**; es steht, wenn eingetragen, direkt neben dem Kreis.

## Spielstätte (ab 2.6.0)

Jede Veranstaltung kann eine Spielstätte haben: Großes Haus, Werkstattbühne, Spiegelhalle, Münsterplatz oder Sonstiges (freier Text). Sie steht über dem Titel auf der Startseite, in der Kopfzeile der Veranstaltung und in jeder PDF-Kopfzeile; auf der Startseite lässt sich danach filtern.

## Requisite einschalten (ab 2.5.0)

*Einstellungen → Dieses Gerät dokumentiert → Requisite.* Beim ersten Einschalten legt die App die Haus-Orte (Requisitentisch, Gassen, Waffenschrank …), Vorlagen für häufige Gegenstände und die Demo „Einfache Leute“ an. In einer Veranstaltung mit Requisite gibt es die Ansichten „Einrichten“ (= Checkliste vor der Vorstellung, nach Ort, mit großen Haken), „Ablauf“ und „Personen“ sowie den Filter „Sicherheit“. Am Gegenstand legt „Wann gebraucht?“ fest, in welchen Abschnitten er gebraucht wird (Vorgabe: vor der Vorstellung), „Wofür“ sagt, wozu. Anlegen und Ändern nur im Bearbeitungsmodus, Ansehen und Abhaken immer.

**Wichtig:** Ein Sync-Paket oder Backup mit Requisite-Inhalt hat das Paketformat 3. **Alle Geräte, die Requisite-Pakete bekommen, zuerst auf 2.5.0 oder neuer aktualisieren** – Doku VT 2.4.4 lehnt solche Pakete mit „bitte zuerst aktualisieren“ ab. Pakete ohne Requisite (z. B. von einem reinen Licht-Gerät) bleiben für ältere Versionen lesbar. Geräte ohne Requisite übernehmen aus Sync-Paketen keine Requisite-Gegenstände.

**Nach dem Update auf 2.4.3:** auf jedem Gerät einmal *Abgleich → Sync-Paket senden → Komplett*. Danach geben auch „Nur Änderungen“-Pakete alles weiter, was ein Gerät von anderen bekommen hat.

## Neue Version veröffentlichen

1. In `index.html` die Konstante `APP_VERSION` erhöhen.
2. In `sw.js` die Konstante `VERSION` auf denselben Wert setzen.
3. In `version.json` dieselbe Nummer eintragen.
4. Alles hochladen. Geöffnete Apps zeigen dann „Neue Version verfügbar → Aktualisieren“.

## Dateien

| Datei | Zweck |
|---|---|
| `index.html` | Die komplette App (HTML, CSS, JavaScript – keine externen Abhängigkeiten) |
| `manifest.json` | App-Name, Icons, Vollbildmodus für die Installation |
| `sw.js` | Service Worker: Offline-Start und Aktualisierung |
| `version.json` | Aktuelle Versionsnummer für den Update-Hinweis |
| `icon-192.png`, `icon-512.png`, `icon-maskable-512.png`, `apple-touch-icon.png` | App-Icons |
| `DOKUMENTATION.md` | Architektur, Testcheckliste, Designentscheidungen, Ausblick |
| `CHANGELOG.md` | Änderungen je Version |
| `test_basis.py`, `test_281.py`, `test_282.py`, `test_283.py`, `test_290.py`, `test_cues.py`, `test_stress.py` | Automatische Tests (Python + Playwright/Chromium): `python3 test_290.py <ordner> [<ordner mit 2.8.3>]` (Stückdaten, Besetzung, Zuständige, Archiv, Gastspiel, PDF; optional Mischbetrieb mit einem Gerät auf 2.8.3), `python3 test_basis.py <ordner>` (Grundfunktionen, Licht/Ton/Bühne/Requisite), `python3 test_281.py <ordner>` (Änderungen aus 2.8.1), `python3 test_282.py <ordner>` (Schnellauswahl und ±0,1 der Cue-Fotos), `python3 test_283.py <ordner> [<ordner mit 2.8.2>]` (Korrekturen aus dem QA-Bericht zu 2.8.2, optional Abgleich mit einem Gerät auf 2.8.2), `python3 test_cues.py <ordner> [<ordner mit 2.7.0>]` (Cue-Fotos mit simulierter Kamera, optional Ablehnung durch 2.7.0), `python3 test_stress.py <ordner> [-k A1,B3]` (Stresstest der QA-Runde, an 2.8.3 angepasst, ca. 8 min). Nicht nötig für den Betrieb; müssen nicht hochgeladen werden. |

Kamera, Teilen und Live-Abgleich brauchen **https**. Das bietet GitHub Pages automatisch. Per Doppelklick (`file://`) geöffnet funktioniert die App ebenfalls, aber ohne Kamera-Live-Vorschau und ohne Offline-Installation.
