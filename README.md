# Doku VT – Technikdokumentation

**Version 2.6.1** · Web-App für die technische Dokumentation im Theater – Beleuchtung, Ton, Bühnentechnik und Requisite: Einträge mit Fotos, Abläufe zum Abhaken, PDF-Export und Geräte-Abgleich. Die App läuft komplett offline, braucht keine Anmeldung und keinen Server.

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

Unter *Einstellungen → Dieses Gerät dokumentiert* festlegen, welche Abteilungen das Gerät führt (Standard nach dem Update: nur Licht). Jede Veranstaltung hat zusätzlich eigene Abteilungen. Sichtbar ist, was beide gemeinsam haben. Beim Abgleich gehen Einträge nur für die Abteilungen des Geräts mit; Veranstaltungen, Einrichtung und Züge immer.

Die Daten liegen **nur lokal auf dem jeweiligen Gerät** (IndexedDB). Das Repository enthält keine Daten. Regelmäßig über *Abgleich → Komplett-Backup* sichern und das Backup auf einem zweiten Ort ablegen (z. B. Fritzbox-Speicher).

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
| `test/test_dokuvt.py` | Automatischer Test (Python + Playwright/Chromium): `python3 test/test_dokuvt.py` (mit `--alt <ordner mit 2.4.4>` zusätzlich der Vergleich mit der Vorversion). Nicht nötig für den Betrieb; muss nicht hochgeladen werden. |

Kamera, Teilen und Live-Abgleich brauchen **https**. Das bietet GitHub Pages automatisch. Per Doppelklick (`file://`) geöffnet funktioniert die App ebenfalls, aber ohne Kamera-Live-Vorschau und ohne Offline-Installation.
