# Doku VT – Beleuchtungsdokumentation

**Version 1.7.0** · Web-App für die Beleuchtungsdokumentation im Theater: Kreise mit Fotos (Aufbau/Einleuchten), PDF-Export, Checkliste und Geräte-Abgleich. Die App läuft komplett offline, braucht keine Anmeldung und keinen Server.

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

Die Daten liegen **nur lokal auf dem jeweiligen Gerät** (IndexedDB). Das Repository enthält keine Daten. Regelmäßig über *Abgleich → Komplett-Backup* sichern.

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

Kamera, Teilen und Live-Abgleich brauchen **https**. Das bietet GitHub Pages automatisch. Per Doppelklick (`file://`) geöffnet funktioniert die App ebenfalls, aber ohne Kamera-Live-Vorschau und ohne Offline-Installation.
