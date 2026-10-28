# Änderungsprotokoll – Doku VT

## 2.9.0 – 28.10.2026

Stückdaten an einer Stelle: Anlegen und Bearbeiten in einem Formular, Besetzung schon beim Anlegen, Zuständige je Abteilung, abgespielte Stücke ausblenden und ein Gastspiel-Schalter je Stück. Kein Datenbank-Update, Paketformat unverändert – **2.9.0 und 2.8.x gleichen ohne Einschränkung miteinander ab**, Geräte können auch später aktualisiert werden. Ausblenden und Zuständige sind nur auf Geräten mit 2.9.0 sichtbar; ältere Geräte tragen die Angaben unverändert weiter.

- **Ein Formular für Anlegen und Bearbeiten:** Titel, Spielstätte, Abteilungen und einklappbar **„Mehr Angaben“** (Dauer, Besetzung, Zuständig, Notiz – alles optional). Anlegen geht weiter mit nur dem Titel. Titel antippen bzw. ⋯ → **„Stückdaten bearbeiten“** öffnet dasselbe Formular. Beim Speichern wird nur geschrieben, was geändert wurde – eine gleichzeitige Änderung auf einem anderen Gerät bleibt erhalten.
- **Dauer** gilt jetzt für alle Abteilungen (dasselbe Feld wie bisher bei der Requisite).
- **Besetzung beim Anlegen:** Personen aus dem Ensemble antippen (Person ist ausgefüllt, Rolle dazuschreiben) oder „+ Person“; „Ensemble bearbeiten“ direkt aus dem Formular. Gespeichert wird zusammen mit der Veranstaltung. Beim Bearbeiten: Liste und „Besetzung bearbeiten“. In der Requisite heißen sie weiter „Personen“.
- **Zuständig je Abteilung:** Freitext (z. B. „Hendrik“) je gewählter Abteilung. In der Veranstaltung steht über den Kästen „Zuständig: Hendrik · Dauer 1:40“ (im Bearbeitungsmodus antippen = Stückdaten öffnen). Im PDF auf der Kapitelseite und in der Fußzeile jeder Seite der Abteilung; bei der Requisite neben der Dauer. Das Deckblatt bleibt, wie es ist.
- **Abgespielt:** ⋯ → „Als abgespielt markieren“ (oder Schalter im Formular). Das Stück verschwindet von der Startseite, aus Zählern und Spielstätten-Filter und steht unten unter **„Abgespielt (n)“**. Darin ein Hinweis mit „Wieder in den Spielplan“. Nichts wird gelöscht; abgeglichen, exportiert und abgehakt wird wie gewohnt.
- **Gastspiel / Abstecher:** Im Formular unter „Nur auf diesem Gerät“ → **„Alle Abteilungen dieses Stücks hier anzeigen“**. Gilt nur für dieses Stück und dieses Gerät; „Dieses Gerät dokumentiert“ bleibt. Plakette „alle Abteilungen“ auf der Startseite; bei einem Stück ohne Abteilung dieses Geräts der Knopf **„Hier trotzdem anzeigen“**. Beim Abgleich nimmt das Gerät dann auch die Requisite an (solange eingeschaltet, die aller Stücke – angezeigt nur im Gastspiel-Stück). Die Diagnose nennt die Gastspiel-Stücke.
- **Duplizieren** übernimmt Dauer, Zuständige und Besetzung; die Kopie ist nie abgespielt.
- **Test:** `test_290.py` (50 Prüfungen, mit zweitem Ordner 2.8.3 57 – dann auch Mischbetrieb mit 2.8.3 per Paket und live in beide Richtungen). `test_basis.py`, `test_281.py`, `test_282.py`, `test_283.py`, `test_cues.py` und `test_stress.py` laufen unverändert durch.

## 2.8.3 – 24.10.2026

Korrekturen aus dem QA-Bericht zu 2.8.2. Kein Datenbank-Update, Paketformat unverändert – 2.8.0 bis 2.8.3 gleichen weiter miteinander ab. **Alle Geräte auf 2.8.3 aktualisieren:** Erst dann wirken ein Durchgang je Spieltag und das feldweise Zusammenführen der Züge überall.

- **Vorstellungs-Checkliste – Mitternacht:** „Heute“ ist jetzt der Spieltag, er wechselt um **4 Uhr**. Haken nach 0 Uhr (Ablauf, Abbau, Requisite „Einrichten“) landen im Durchgang des Vorabends, das Protokoll bleibt vollständig. Vorher begann um 0 Uhr still ein zweiter Durchgang mit dem Folgedatum.
- **Ein Durchgang je Spieltag auf allen Geräten:** Beginnen zwei Geräte unabhängig „Vorstellung heute beginnen“ (oder haken ab, ohne begonnen zu haben), entsteht derselbe Durchgang (feste Kennung je Veranstaltung, Tag und Nummer). Doppelte Durchgänge aus älteren Versionen werden beim Abgleich und beim Start zusammengeführt – Haken gehen nicht verloren. „Neu beginnen“ bleibt ein eigener Durchgang.
- **Cue-Kamera und Doku-Kamera quer:** Auf dem Smartphone im Querformat Sucher links, Knöpfe rechts (vorher Sucher 12 px in der Cue-Kamera). Im Hochformat auf kleinen Smartphones (320 × 568) ist der Cue-Sucher größer (178 statt 148 px).
- **Doku-Kamera im Rotlicht:** dunkle rote Knöpfe statt Weiß, Sucherbild rot gefiltert, Phase über Rahmenart. Kein weißes Aufblitzen mehr im dunklen und im Rotlicht-Modus (dezenter Rand wie bei der Cue-Kamera).
- **Sehr lange genutzte Veranstaltungen:** Der Empfänger nimmt jetzt bis 20 000 Felder an (vorher 2 000 – die Veranstaltung wurde still verworfen). Was trotzdem abgelehnt wird, steht im Import-Dialog („NICHT übernommen“), im Protokoll und als „Fehler“ im Status – auch beim Live-Abgleich. Die Diagnose warnt, wenn Geräte mit 2.8.2 eine Veranstaltung nicht mehr annehmen würden.
- **Rotlicht:** Fehler- und Warnmeldungen sehen anders aus als „Gespeichert“ (Fehler hell hinterlegt, Warnung mit kräftigem Rahmen, beide mit Symbol – in allen Farbschemata). Bildansicht rot statt weiß. Gedämpfte Schrift etwas heller.
- **Großbild auf dem Smartphone:** „Kreis“ steht über der Nummer, die Nummer bricht nur nach „+“ um (vorher „123+1“ / „24“). Die Fotozahl entfällt im Kopf auf schmalen Smartphones.
- **Smartphone quer:** Die Werkzeugleiste klappt beim Runterscrollen weg und kommt beim Hochscrollen zurück (vorher blieben 63–85 px für den Inhalt).
- **Cue-Fotos:** „Nächster Cue“ nach einer Text-Cue („Ende“) springt hinter die höchste Nummer statt auf Cue 1. „Mehrere Cues“ legt bis 2000 auf einmal an und sagt, wenn es mehr wären (vorher still bei 500 gekappt). Die Schnellauswahl hängt nicht mehr an einer Cue eines Geräts mit vorgehender Uhr.
- **PDF:** Gekürzte Texte enden sichtbar mit „…“ (Warnhinweise jetzt bis 12 Zeilen, vorher still nach 6). Sehr lange Kreise laufen nicht mehr aus der Seite. Das Protokoll nennt in der Nacht der Zeitumstellung die Zone (MESZ/MEZ).
- **Ansichtsmodus:** Titel antippen, ⋯-Menü (Ändern, Duplizieren, Zurücksetzen, Zusammenführen, Löschen) und „Haken zurücksetzen“ fragen erst, ob der Bearbeitungsmodus eingeschaltet werden soll – auch in der Cue-Liste. Die Übersichten bleiben unverändert.
- **Abgleich:** Nach dem Abgleich mit einem Gerät, dessen Uhr vorgeht, steht „Synchron“ statt „22 offen“. **Gemeinsamer Zug:** Licht-Bestückung und Bühnen-Last am selben Zug bleiben beide erhalten (Angabe für Angabe zusammengeführt). **Weitergeben:** Jedes Gerät gibt beim Abgleich alles weiter, was es hat – auch im Kreis (Licht → Ton → Bühne → Alle) kommt alles an. Requisite weiterhin nur an Geräte mit Requisite; „Komplett, alle Abteilungen“ entfällt (steckt in „Komplett“).
- **Bedienung:** Sync-Pille, Ansichts-Umschalter und Schnellzugriff mindestens 44 px hoch. „Löschen“-Knopf und Fehlermeldung mit ausreichendem Kontrast. Titel-Knopf mit sichtbarem Fokusrahmen. Auf dem Smartphone steht PDF im ⋯-Menü, der Titel hat mehr Platz. „Lichtzeichen“ wird nicht mehr mitten im Wort getrennt.
- **Robustheit:** Texte über 100 000 Zeichen werden nicht gespeichert (klare Meldung, Editor bleibt offen) – vorher verwarf sie der Empfänger still. Zeitstempel jenseits eines gültigen Datums und falsche Feldtypen (z. B. „Zustand“ als Zahl) werden beim Import abgelehnt statt die Ansicht abstürzen zu lassen. Speicherfehler ohne Angabe des Browsers und „Speicher voll“ beim Schreiben melden klar „Es wurde NICHTS gespeichert“. Transparente PNG werden weiß statt schwarz hinterlegt. „Wiederherstellen“ bringt keinen Eintrag zurück, den ein anderes Gerät vorher einzeln gelöscht hatte.
- **Nicht geändert (siehe DOKUMENTATION, Ausblick):** Cue-Fotos in der Warteschlange beim Beenden der App, Sonderschriften im PDF, Speicherbedarf sehr großer Pakete.
- **Test:** `test_283.py` (61 Prüfungen zu allen Korrekturen, mit zweitem Ordner 2.8.2 64 – dann auch gemischter Betrieb mit 2.8.2; u. a. Mitternacht mit verstellter Uhr, zwei und fünf Geräte, Kameras quer und im Rotlicht, Zug-Simulation mit Geräten auf 2.8.2). `test_stress.py` an 2.8.3 angepasst. `test_basis.py`, `test_281.py`, `test_282.py`, `test_cues.py` laufen unverändert durch.

## 2.8.2 – 23.10.2026

Cue-Fotos schneller vorbereiten und Punktstimmungen beim Fotografieren. Kein Datenbank-Update, Paketformat unverändert – 2.8.0, 2.8.1 und 2.8.2 gleichen weiter miteinander ab.

- **„+ Cue“ mit Schnellauswahl:** Unter dem Feld „Cue-Nummer“ stehen die nächsten drei ganzen Nummern und die Punktstimmungen zur zuletzt angelegten Cue – ist das die 13, also **14 · 15 · 16** und **13.1 … 13.9**. Antippen setzt die Nummer, „Anlegen“ legt die Cue an. Nummern, die es in der Liste schon gibt, fallen weg; vorgeschlagen ist die erste freie ganze Nummer. Ausgangspunkt ist die zuletzt angelegte Cue (darunter steht „Zuletzt angelegt: Cue …“).
- **Cue-Kamera: −0.1 / +0.1** über „Nächster Cue“. Zählt die angezeigte Nummer um 0,1 runter oder hoch (13 → 13.1 → 13.2, 13.9 → 14). Die Punktstimmung entsteht erst mit dem ersten Foto – Durchzählen ohne Auslösen legt nichts an. Gibt es die Nummer schon, gehen die Fotos dorthin. Nicht unter 0; bei Text-Nummern (z. B. „Ende“) ein Hinweis. Am Computer auch mit ↑/↓ bzw. +/−.
- Der Sucher der Cue-Kamera ist auf kleinen Smartphones etwas kleiner, damit die neuen Knöpfe mit dem Daumen erreichbar bleiben.
- **Test:** `test_282.py` (21 Prüfungen: Vorschläge, Wegfall vorhandener Nummern, Antippen über die Oberfläche, ±0,1 mit simulierter Kamera, Smartphone 390×844 und 375×667, Rotlicht); `test_281.py` prüft die Version jetzt gegen `version.json`. `test_basis.py`, `test_cues.py`, `test_281.py` laufen durch.

## 2.8.1 – 23.10.2026

Kleinere Korrekturen für Licht, Requisite und den Foto-Import. Kein Datenbank-Update, Paketformat unverändert – 2.8.0 und 2.8.1 gleichen weiter miteinander ab.

- **Licht, Ton, Bühne – Kästen getrennt:** Über der Liste stehen jetzt nacheinander **Hinweis Einrichten** → **Vor der Vorstellung** → **Ablauf** → **Beleuchterzüge** (Licht) bzw. **Positionen** (Bühne). Beleuchterzüge und Ablauf sind nicht mehr in einem Kasten; bei der Bühne sind Ablauf und Positionen ebenso getrennt. Der Schnellzugriff in der Werkzeugleiste hat je einen Knopf dafür.
- **„Vor der Vorstellung“ enthält nur, was vorher zu tun ist:** feste Punkte und die Ablauf-Schritte „Vor der Vorstellung“ (Bühne: „Grundeinrichtung“). Während der Vorstellung, Pausenumbau und danach stehen im Kasten **Ablauf** – dort weiter abhakbar, im selben Durchgang. Wer im Ablauf abhakt, ohne die Vorstellung begonnen zu haben, legt den Durchgang für heute damit an. Das PDF ist genauso gegliedert.
- **Hinweis Einrichten:** heißt nur noch so (vorher „Hinweis Einrichten / Ablauf“) und hat ein eigenes Bearbeiten-Blatt. Im Ablauf-Editor steht er nicht mehr. Ohne Hinweis zeigt der Bearbeitungsmodus oben den Knopf „+ Hinweis Einrichten · Licht“.
- **Sub (Licht):** neues Feld unter „Weitere Angaben“ (Zahlentastatur, „3 7“ wird zu „3+7“). Steht nur, wenn eingetragen, direkt neben dem Kreis – in der Liste, den Kacheln, der Großbild-Kopfzeile, im Detail, in der Bildansicht und im PDF (Seitenkopf, Infoblock, Inhaltsverzeichnis).
- **Foto kopieren:** Im Foto-Menü des Eintrags gibt es neben „Zu Einleuchten verschieben“ jetzt **„Zu Einleuchten kopieren“** (umgekehrt „Zu Aufbau kopieren“, bei Ton „Soundcheck“). Die Kopie ist ein eigenes Foto, die Bilddaten werden geteilt – kein doppelter Speicher.
- **Requisite – „Vor der Vorstellung“ beim Gegenstand sichtbar:** Unter „Wann gebraucht?“ steht der Knopf wieder, bei neuen Gegenständen vorgewählt. Er hat keine Auswirkung auf „Einrichten“ – eingerichtet wird weiterhin jeder Gegenstand.
- **Requisite – Ensemble sofort sichtbar:** Wer aus „Personen“ heraus das Ensemble bearbeitet, sieht neue Namen beim Zurückkehren sofort unter „Aus dem Ensemble“ (vorher erst nach erneutem Öffnen). Alle Listen aktualisieren sich jetzt auch bei Änderungen der Einstellungen.
- **Requisite – „Bühne hinten“ heißt „Hinterbühne“:** Der Haus-Ort ist umbenannt, für alle Stücke und auf Geräten mit bestehenden Daten (beim Start). Die Kennung bleibt gleich, beim Abgleich mit 2.8.0 entstehen keine Dubletten; kommt von dort der alte Name zurück, passt der nächste Start ihn wieder an. Ein von Hand umbenannter Ort bleibt, wie er ist.
- **Behoben – Fotos aus der Galerie (Samsung-Tablet):**
  - Konnte der Browser ein Foto zunächst nicht dekodieren, wartete die App endlos – das Foto blieb „in Arbeit“ und Speichern war gesperrt. Jetzt gibt es ein Zeitlimit und einen zweiten Leseweg (createImageBitmap).
  - Mehrere ausgewählte Fotos werden **nacheinander** statt gleichzeitig verarbeitet. Große Handy-Fotos (50–200 MP) auf einmal brachten den Speicher des Tablets an die Grenze.
  - **HEIF/HEIC** (Samsung „Hocheffiziente Bilder“) kann Chrome auf Android nicht lesen. Statt eines stillen Fehlers erscheint jetzt ein Hinweis, wie man es in der Kamera-App abstellt.
  - Jedes nicht übernommene Foto steht mit Dateiname, Typ und Größe im Protokoll (Diagnose).
  - Gilt für Doku-Fotos, Requisite-Fotos und Cue-Fotos.
- **Test:** `test_281.py` (36 Prüfungen zu 2.8.1, u. a. Reihenfolge der Kästen, Abhaken im Ablauf, Sub in Liste/Detail/Großbild/PDF, Foto kopieren, Ensemble, Hinterbühne, Galerie-Import mit großem, kaputtem und HEIF-Bild über die Oberfläche); `test_basis.py` (bisher `test_280.py`, an 2.8.1 angepasst) und `test_cues.py` laufen durch.

## 2.8.0 – 22.10.2026

Neuer Bereich **Cue-Fotos**: Lichtstimmungen vom Stellwerk/FOH fotografieren, mit Cue-Nummer, Notizen und Hinweisen ablegen und als PDF exportieren. Eigenständig neben den Dokumentationen – Licht, Ton, Bühne und Requisite bleiben unverändert. Kein Datenbank-Update. **Alle Geräte, die miteinander abgleichen, auf 2.8.0 aktualisieren** – ein Paket mit Cue-Fotos hat Format 4, Doku VT 2.7.0 lehnt es mit „bitte zuerst aktualisieren“ ab. Pakete ohne Cue-Fotos bleiben für ältere Geräte lesbar.

- **Einstieg:** Auf der Startseite oben der Umschalter **Dokumentation | Cue-Fotos**. Unter Cue-Fotos stehen die Cue-Listen (je Probe oder Vorstellung eine) mit Titel, Spielstätte, Datum und Notiz; beim Anlegen lässt sich der Titel einer Veranstaltung antippen.
- **Zwei Arbeitsweisen:** *Vorbereiten* – „+ Cue“ oder „Mehrere“ (von–bis, Schritt, z. B. 1–40 oder 0,5), später fotografieren. *Live* – „Kamera“ antippen und loslegen, Nummer, Notiz und Hinweis gleich oder danach ergänzen.
- **Cue-Kamera** (die Doku-Kamera bleibt, wie sie ist): Groß die aktuelle Cue („Cue 12 · Bild B“, antippen = Nummer ändern). Der **Auslöser** macht das nächste Bild dieser Cue – A, B, C … **„Nächster Cue“** springt zur nächsten vorbereiteten Cue (gibt es keine, zur nächsten ganzen Nummer: 12 → 13, 12.5 → 13) und löst sofort aus.
- **Schnelle Folgen ohne Warten:** Das Bild wird sofort aus dem Sucher kopiert; Komprimieren und Speichern laufen im Hintergrund nacheinander („2 wird gespeichert …“ / „✓ 34 gespeichert“). Jedes Foto wird einzeln gespeichert, auch nach dem Schließen der Kamera läuft die Warteschlange weiter.
- **Dunkler Saal:** kein weißes Aufblitzen beim Auslösen, dunkle Knöpfe, im Rotlicht-Modus rot. Die Taschenlampe startet immer aus. Der Bildschirm bleibt an, solange die Kamera offen ist (wo der Browser es kann). Belichtungskorrektur (−/+), wo das Gerät sie anbietet (z. B. Pixel). Das Objektiv der Cue-Kamera wird getrennt gemerkt (vom FOH oft Tele).
- **Fotos:** 1:1, 1200 px, JPEG 0,75 – dunkle Bühnenbilder meist 100–200 KB.
- **Je Bild eigene Notiz und eigener Hinweis**, die Cue (Nummer, Name, Notiz) ist gemeinsam. Hinweise auffällig mit Symbol wie der Warnhinweis.
- **Bearbeiten nur im Bearbeitungsmodus:** Cue antippen = Nummer, Name, Notiz und je Bild Notiz/Hinweis. Foto antippen = Ansehen, Notiz & Hinweis, **Markieren** (gleiche Bedienung wie bei den Doku-Fotos), **Original wiederherstellen** (das Original bleibt beim Markieren erhalten), nach vorn/hinten, zu anderer Cue, löschen. Wird eine Nummer auf eine vorhandene geändert, fragt die App: zusammenführen oder zwei behalten. Doppelte Nummern sind markiert.
- **Ansichtsmodus:** Foto antippen öffnet die Bildansicht mit Cue, Bild, Name, Hinweis und Notizen; „Nächster Cue“ springt weiter.
- **PDF** (A4 hoch): Deckblatt mit Übersicht aller Cues – auch ohne Foto („kein Foto“) – und Seitenzahlen, dann je Foto eine Seite: Kopfzeile Stück · Spielstätte · Datum, Plakette „CUE 12 · A“, Foto groß, darunter Cue-Nummer, „Bild B von 3“, Name, Hinweis (rosa), Notiz zum Bild, Notiz zur Cue. Sortiert nach Cue-Nummer. Option „Kompakt“ zum Mailen. Nach dem Export fragt die App, ob die Liste gelöscht werden soll.
- **Löschen:** Papierkorb (wiederherstellbar, Speicher bleibt belegt) oder **endgültig** (gibt den Speicher sofort frei; andere Geräte geben ihn nach dem Abgleich mit „Speicher aufräumen“ frei). „Speicher aufräumen“ fasst Cue-Fotos lebender Listen und im Papierkorb nicht an.
- **Abgleich:** Cue-Fotos gehen an jedes abgeglichene Gerät – unabhängig von dessen Abteilungen – per Sync-Paket und live. Notiz auf dem einen und Foto auf dem anderen Gerät gehen beide durch. Das Backup einer einzelnen Veranstaltung enthält keine Cue-Fotos, das Komplett-Backup schon.
- **Behoben:** „Sync-Paket senden → Nur Änderungen“ meldete „Keine Änderungen“, wenn sich nur Durchgänge der Vorstellungs-Checkliste oder Haus-Daten der Requisite geändert hatten.
- **Test:** `test_cues.py` (43 Prüfungen mit simulierter Kamera, u. a. Auslöser A/B/C, „Nächster Cue“, PDF mit qpdf, Paket an ein Gerät nur mit Ton, Ablehnung durch 2.7.0, Live-Abgleich, Papierkorb und endgültiges Löschen, Smartphone-Breite); `test_280.py` (die Prüfungen aus 2.7.0) läuft unverändert durch.

## 2.7.0 – 22.10.2026

Licht überarbeitet, Ton und Bühne angeglichen, Bildübertragung repariert. Kein Datenbank-Update, Paketformat unverändert. **Alle Geräte auf 2.7.0 aktualisieren** – 2.6.5 behält die neuen Angaben (Zug, Warnhinweis, Ablauf Licht/Ton) beim Abgleich, zeigt sie aber nicht an (Bühnen-Schritte „Während der Vorstellung“ erscheinen dort nicht bzw. unter „Grundeinrichtung“).

- **Bilder fehlten nach dem Abgleich (z. B. Pixel → iPad):** Beim Live-Abgleich kommt ein Eintrag vor seinen Bildern an. Die Vorschau merkte sich dann „kein Bild“ und blieb leer, bis die App neu gestartet wurde – in allen Abteilungen. Jetzt erscheint das Bild, sobald es da ist; bis dahin steht „Bild fehlt“. Sync-Pakete werden auf iPad/iPhone portionsweise eingelesen (weniger Speicher, große Pakete brechen nicht mehr ab).
- **Licht – Eintrag:** DMX-Adresse entfällt (steht in „Adresse“; alte Werte bleiben sichtbar). **Position und Zug getrennt**, beide im Hauptteil; Zug mit Schnelltasten aus den Beleuchterzügen der Veranstaltung. Farbe/Gobo, Gerät, Szene bleiben unter „Weitere Angaben“.
- **Warnhinweis** (Licht, Ton, Bühne): auffällig mit Symbol auf der Karte, im Detail, in der Bildansicht, im Großbild und im PDF.
- **Ablauf für Licht und Ton** (wie Bühne): Vor der Vorstellung · Während der Vorstellung · Pausenumbau · Nach der Vorstellung. Im Eintrag unter „Ablauf-Hinweise“ direkt zum Kreis/Kanal anlegen, oder gesammelt über „Ablauf“. Die Hinweise stehen auf der Karte, in „Vor der Vorstellung“ zum Abhaken und im PDF. Bühne bekommt zusätzlich „Während der Vorstellung“.
- **Hauptansicht:** Karten zeigen alle ausgefüllten Angaben, auch die „Weiteren Angaben“.
- **Großbild:** Die fixierte Leiste zeigt Kreis, Gruppe, Filter, Adresse, Position und Zug (Ton: Kanal, Quelle, Mikrofon, Stagebox, Ausgang, Position · Bühne: Position, Element, Ort, Höhe, Reihenfolge), darunter – ebenfalls fixiert – Warnhinweis, weitere Angaben, Ablauf und Bemerkung.
- **„Hinweis Einrichten / Ablauf“:** Der allgemeine Text jeder Abteilung steht, sobald ausgefüllt, als eigener, immer offener Kasten ganz oben (Requisite: „Wichtig“).
- **Auffälliger und immer erreichbar:** „Vor der Vorstellung“ und die Kästen „Licht · Beleuchterzüge & Ablauf“, „Ton · Ablauf“, „Bühne · Ablauf & Positionen“ haben farbige Kopfzeilen. Neue Schnellzugriff-Leiste in der fixierten Werkzeugleiste (Hinweis · Vor der Vorstellung mit Fortschritt · Beleuchterzüge · Ablauf) springt beim Scrollen jederzeit zum Kasten und klappt ihn auf.
- **Spielstätten-Farben** klar anders als die Abteilungen: Großes Haus Gold, Werkstattbühne Ocker, Spiegelhalle Violett, Münsterplatz Cyan, Sonstiges Oliv.
- **Startseite:** Demo- und Testveranstaltungen stehen immer am Ende.
- Ablauf-Hinweise im Eintrag speichern nur, was geändert wurde – Änderungen oder Löschungen eines anderen Geräts (Live-Abgleich) bleiben erhalten. Zug-Schnelltasten setzen genau einen Zug.

## 2.6.5 – 20.10.2026

- **Ablauf neu geordnet (teils nebeneinander, teils untereinander):** oben der Name groß und daneben „für …“, darunter eine Leiste mit festen Feldern nebeneinander – Ort · Zu wem · Lichtzeichen · Übergabe (leere Felder mit „–“, damit alles immer an derselben Stelle steht). Schritte genauso: Wann + Text, darunter Ort · Zu wem · Lichtzeichen · Gegenstand. Auf dem Smartphone 2 × 2.
- **Einrichten nur mit Einrichte-Angaben:** Name, darunter Stelle · Zu wem · Zustand/Markierung, dazu Sicherheit und Bemerkung. Wann, wofür, Lichtzeichen und Übergabe stehen nur noch im Ablauf.
- **„Ohne Person“ obwohl „Zu wem“ ausgefüllt:** behoben. Namen aus „Zu wem sonst“ und Verweise auf gelöschte/neu angelegte Personen werden über Person oder Rolle der richtigen Person des Stücks zugeordnet (Gliederung am Requisitentisch, PDF, Sortierung).
- **Testvorstellung „Kabale und Liebe“** (Großes Haus): 8 Personen, 50 Gegenstände, 15 Übergaben mit Übergabe-Orten (Gassen, Hinterbühne, Unterbühne, Inspizientenpult, Unter dem Podest), 7 mit Sicherheit (Waffe, Glas, Pyro, Nebel, Akku), Übergaben an Bühnentechnik, Inspizient/in und Beleuchtung, 12 Requisiten im Bühnenbild, 2 in Kostümen, Pause mit Umbau, 9 Schritte. Wird einmalig angelegt; jederzeit neu unter Einstellungen → Requisite → „Testvorstellung anlegen“.

## 2.6.4 – 19.10.2026

- **Ablauf und Einrichten lesbar:** Statt gequetschter Spalten steht unter dem Namen eine Angabenliste in fester Reihenfolge – Ort/Stelle · Zu wem · Lichtzeichen · Übergabe (nur ausgefüllte Angaben). Große Schrift, „Lichtzeichen JA“ hervorgehoben, ein Foto rechts. Auf dem Tablet zweispaltig, auf dem Smartphone untereinander.
- **PDF-Ablauf groß gesetzt:** jeder Schritt/Gegenstand als eigener Eintrag mit großem Kästchen, Wann (farbig), Was in 14 pt, Angaben in 12 pt und „Foto S. x“; Abschnitts-Überschriften groß. Gegenstandsliste mit größerer Schrift und weniger, breiteren Spalten (Was · Stelle · Zu wem · Foto, Details darunter).
- **PDF:** Requisite-Gegenstände mit Foto kommen jetzt automatisch vor denen ohne – im Inhaltsverzeichnis, auf den Fotoseiten und in den Listen.
- **Allgemeine Infos** größer (App und PDF).

## 2.6.3 – 19.10.2026

- **Ablauf:** Teile und Pausen sind beim Öffnen aufgeklappt, Vor/Nach der Vorstellung zugeklappt.
- **Feste Spalten:** Jeder Gegenstand (Einrichten und Ablauf) und jeder Schritt hat denselben Aufbau – Kästchen · Was (mit wofür, Sicherheit, Zustand, Bemerkung) · ein Foto · Ort bzw. Stelle · Zu wem · Lichtzeichen · Übergabe. Ort, Person und Lichtzeichen stehen immer an derselben Stelle.
- **Gegenstand bearbeiten:** Die Felder Person/Rolle sind weg (Personen kommen aus „Allgemeine Infos → Personen“). Neu: „Zu wem sonst (Übergabe)“ mit Schnelltasten Bühnentechnik, Inspizient/in, Beleuchtung, Ton, Maske, Garderobe – oder frei eintippen.
- **Übergabe-Ort:** Schnelltasten Gasse links, Gasse rechts, Unterbühne, Hinterbühne; frei eintragen geht weiter.
- **Spielstätten-Farben:** Großes Haus rot, Werkstattbühne blau, Spiegelhalle violett, Münsterplatz gold, Sonstiges türkis – als Rahmen der Veranstaltungskarte, in der Plakette und im Filter.
- **PDF:** Personen (Person · Rolle) stehen auf dem Deckblatt beim Inhaltsverzeichnis. „Vor der Vorstellung“ enthält jetzt alle Gegenstände nach Ort. Ablauf und Gegenstände haben dieselben Spalten wie die App: Kästchen · Was (fett, darunter wofür/Sicherheit/Zustand/Bemerkung) · Ort/Stelle · Zu wem · Lichtz. · Übergabe · Foto. Innerhalb jedes Orts zuerst die Gegenstände mit Foto, dann ohne.

## 2.6.2 – 19.10.2026

Zweite Runde Nachbesserungen Requisite. Kein Datenbank-Update, Paketformat unverändert.

- **Ensemble statt Schnellauswahl:** Unter Einstellungen → Requisite → „Ensemble (Personen)“ stehen nur Namen. Im Stück (Allgemeine Infos → Personen) tippst du einen Namen aus dem Ensemble an und gibst die Rolle dazu. Die Schnellauswahl im Gegenstand ist entfernt; dort bleibt das Eintragen (Person, Rolle) mit Namensvorschlägen aus dem Ensemble.
- **Person vor Rolle:** überall „Julian (Mackie)“, in Formularen erst Person, dann Rolle. Einträge aus 2.6.1 werden als Namen übernommen.
- **Im Stück gebraucht (Teil, Pause, Sonstiges):** zusätzlich „Lichtzeichen? Ja / Nein“ und „Übergabe-Ort“. Steht im Ablauf, auf der Karte und im PDF.
- **Zustand „Sonstiges …“** mit eigenem Text.
- **Einrichten:** jeder Gegenstand hat ein Kästchen (vorher nur die mit „Vor der Vorstellung“). Neue Zeile: Kästchen · Gegenstand · Foto · Angaben (wann, wofür, Person, Stelle, Zustand), ohne Schraffur. „Vor der Vorstellung“ fällt bei „Wann gebraucht?“ weg – eingerichtet wird alles.
- **Reiter „Personen“ entfernt** (Einrichten · Ablauf).
- **PDF Requisite neu gegliedert, jeder Teil auf eigener Seite:** 1. Allgemeine Infos, Sicherheit, Personen (kompakt, zweispaltig, Person · Rolle) · 2. Vor der Vorstellung (feste Punkte, Schritte, Verbrauch) · 3. Ablauf in der Vorstellung · 4. Nach der Vorstellung · 5. Gegenstände nach Ort/Person. Ablauf-Tabelle: Kästchen · Wann · Was · Wo · Foto. Überall Kästchen und „Foto S. x“, wenn es ein Foto gibt. Tabellen werden nicht über einen Seitenumbruch getrennt, wenn sie auf eine Seite passen.

## 2.6.1 – 19.10.2026

Nachbesserungen an der Requisite nach dem ersten Test auf dem Tablet. Kein Datenbank-Update, Paketformat unverändert.

- **Personen: Rolle und Darsteller/in getrennt.** Im Gegenstand stehen unter „Zu wem“ zwei Felder (Rolle, Darsteller/in) statt einem.
- **Schnellauswahl Personen:** Im Gegenstand erscheint unter den Personen des Stücks die Schnellauswahl; ein Tipp fügt die Person dem Stück hinzu und wählt sie. „bearbeiten“ öffnet die Liste direkt aus dem Gegenstand (anlegen, ändern, sortieren, entfernen), dieselbe Liste gibt es unter Einstellungen → Requisite → „Personen-Schnellauswahl“. Neue Personen lassen sich mit dem Haken „auch in die Schnellauswahl“ gleich mit aufnehmen. Die Schnellauswahl gilt je Gerät für alle Stücke.
- **„Durchgänge & PDF“ entfernt.** Statt des unklaren Knopfs steht dort „Neu beginnen“ (erscheint, sobald etwas abgehakt ist): leert alle Haken in einem neuen Durchgang; der alte bleibt im Protokoll (Listen-Symbol oben). „Heute · 3 von 28 erledigt“ statt Durchgangs-Titel.
- **Orte deutlich abgesetzt:** Jeder Ort ist ein kräftiges farbiges Band mit großer Schrift, bleibt beim Scrollen oben stehen (so sieht man immer, wo man gerade einrichtet) und wird grün, wenn alles abgehakt ist. Personen am Requisitentisch sind mit Balken abgesetzt.
- **Ablauf: Reihenfolge ändern und verschieben.** Im Bearbeitungsmodus hat jede Zeile (Schritt wie Gegenstand) drei Knöpfe: nach oben, nach unten, „in anderen Abschnitt verschieben“. Schritte und Gegenstände eines Abschnitts stehen in einer gemeinsamen Reihenfolge; sie gilt auch für die Checkliste und das PDF und wird beim Duplizieren mitgenommen. Wer nichts verschiebt, sieht wie bisher erst die Schritte, dann die Gegenstände nach Ort.
- **„Waffenschrank verschlossen“ ist keine Vorauswahl mehr** (weder in der Hausvorlage noch in der Demo). In bestehenden Stücken bleibt der Punkt stehen, bis er unter „Feste Punkte“ (Einrichten, Bearbeitungsmodus) gelöscht wird.
- Test: 37 Prüfungen (neu: Schnellauswahl, Ablauf verschieben, Neu beginnen).

## 2.6.0 – 19.10.2026

Requisite übersichtlicher: **„Einrichten“ ist die Checkliste vor der Vorstellung**, jeder Gegenstand weiß, **wann und wofür** er gebraucht wird, und jede Veranstaltung hat eine **Spielstätte**. Kein Datenbank-Update, Paketformat unverändert (2 bzw. 3 mit Requisite).

- **Ansichten heißen jetzt Einrichten · Ablauf · Personen** (vorher „Nach Ort“). Der Knopf „Abhaken“ entfällt bei Requisite – abgehakt wird direkt in Einrichten und Ablauf.
- **Einrichten = Checkliste „Vor der Vorstellung“:** oben groß „Vor der Vorstellung“ mit Fortschritt („1 von 28 erledigt“) und „Durchgänge & PDF“, darunter „Vorbereiten“ (feste Punkte und Schritte aus „Vor der Vorstellung“), Verbrauch und alle Gegenstände nach Ort – jeder mit **großem Haken** links. Antippen hakt ab; gibt es heute noch keinen Durchgang, wird er dabei angelegt („Vorstellung heute beginnen“ entfällt). Die Checkliste muss nicht mehr extra gepflegt werden: Jeder neue Gegenstand steht von selbst darauf.
- **„Wann gebraucht?“ und „Wofür“ am Gegenstand:** im Editor direkt unter „Stelle“ die Abschnitte des Stücks als Knöpfe (Vorgabe „Vor der Vorstellung“), Mehrfachauswahl, dazu ein Feld „Wofür“ (z. B. „Szene 3 – Anna raucht“). Auf der Karte steht „🕘 Teil 1 – für Szene 3“. Ohne „Vor der Vorstellung“ steht der Gegenstand ohne Haken in Einrichten (z. B. etwas, das erst in der Pause gebraucht wird).
- **Ablauf:** je Abschnitt die Schritte und darunter die dort gebrauchten **Gegenstände mit Haken**. „Vor der Vorstellung“ zeigt nur „26 Gegenstände einrichten →“ und springt nach Einrichten. Im Bearbeitungsmodus je Abschnitt „+ Schritt“, „+ Gegenstand“ (mit diesem Abschnitt vorgewählt) und **„Gegenstände zuordnen“** (Mehrfachauswahl mit Suche, eine Speicherung).
- **„+ Abschnitt“** statt „+ Pause“/„+ Abbau“: Menü mit Vor der Vorstellung · Teil · Pause · Nach der Vorstellung · Abbau · Sonstiges (eigener Name). Es wird nur der gewählte Abschnitt angelegt, an der passenden Stelle – eine Pause bringt **keinen** zweiten Teil mehr mit. **Neue Stücke starten mit Vor der Vorstellung · Teil 1 · Nach der Vorstellung.** Teile heißen immer „Teil 1“, „Teil 2“ …, mehrere Pausen „Pause 1“, „Pause 2“. Löschen eines Abschnitts löscht seine Schritte; Gegenstände bleiben.
- **„Einrichtung · Requisite“ heißt jetzt „Allgemeine Infos“** (Kasten über der Liste, Bearbeiten-Blatt, PDF).
- **Spielstätte für alle Abteilungen:** beim Anlegen und unter „Titel & Details bearbeiten“ große Knöpfe Großes Haus · Werkstattbühne · Spiegelhalle · Münsterplatz · Sonstiges (freier Text). Sichtbar als Plakette über dem Titel jeder Veranstaltungskarte, mit Ortssymbol in der Kopfzeile der Veranstaltung und in jeder PDF-Kopfzeile („Titel · Spielstätte“, auch Kapitelband und Fußzeile). Auf der Startseite Filter nach Spielstätte, sobald es mehr als eine gibt; eine neue Veranstaltung übernimmt den gewählten Filter.
- **PDF Requisite:** Ablauf je Abschnitt mit den zugeordneten Gegenständen; Gegenstandstabelle mit Kästchen (= vor der Vorstellung einrichten) und neuer Spalte „Wann · Wofür“. Kapitel-Plakette „EINRICHTEN“.
- **Demo „Einfache Leute“:** Crashglas-Flasche und Handtuch sind „Vor der Vorstellung“ und „Teil 1 – für Umbau nach ca. 60 min“.
- Am Requisitentisch (nach Person gegliedert) steht die Person nicht mehr zusätzlich auf jeder Karte.
- **Test:** 34 Prüfungen (neu: Einrichten als Checkliste mit automatisch angelegtem Durchgang, „Wann gebraucht“/Zuordnen, Abschnitt-Menü, Spielstätte); Version wird gegen `version.json` geprüft.

## 2.5.0 – 19.10.2026

Neue Abteilung **Requisite** (Grün): Was liegt wo, wem gehört es, was ist vor, während und nach der Vorstellung zu tun. Licht, Ton und Bühne bleiben unverändert. Kein Datenbank-Update.

- **Einschalten:** Einstellungen → „Dieses Gerät dokumentiert“ → Requisite. Beim ersten Einschalten kommen die Haus-Orte (Requisitentisch, Gassen, Waffenschrank …), Vorlagen für häufige Gegenstände und die Demo „Einfache Leute“ dazu.
- **Gegenstand in drei Schritten:** Foto, Name (mit Vorschlägen aus den Vorlagen und dem Stück), Ort antippen (die zuletzt benutzten Orte als große Knöpfe). Ein Foto allein genügt. „+ Nächster am selben Ort“ behält Ort und Person – ein Requisitentisch ist so in einem Zug erfasst.
- **Am Gegenstand:** Stelle am Ort, zu wem (auch mehrere Personen), Zustand (präpariert, beklebt …), Sicherheit (Waffe, Knall/Pyro, Glas …), Menge, Markierung, Behälter („liegt in …“), Zuständig, Verbrauch/Reserve/Defekt, Pflege, Verbleib. Bildunterschrift je Foto.
- **Drei Ansichten:** **Nach Ort** (oben „Verbrauch“, am Requisitentisch nach Person gegliedert, Inhalt von Behältern eingerückt), **Ablauf** (Vor der Vorstellung, Vorstellung bzw. Teile und Pausen, Nach der Vorstellung, Abbau – jeder Schritt mit Zeit und Auslöser, z. B. „ca. 35′ · Einruf → 2× Lichtzeichen“) und **Personen**. Dazu der Filter **Sicherheit**. Sicherheit und Defekt immer mit Symbol und Text.
- **Ablauf abhaken:** „Vorstellung heute beginnen“ und jeden Schritt mit großem Haken abhaken – im Ansichtsmodus. Erledigte Abschnitte werden blass, der erste offene ist aufgeklappt. Gleicher Durchgang wie „Vor der Vorstellung“ und das PDF-Protokoll.
- **Keine Pause als Standard.** „+ Pause“ fügt Pause und zweiten Teil ein, die Teile heißen dann „Teil 1“, „Teil 2“. Pause entfernen führt die Teile wieder zu „Vorstellung“ zusammen. „+ Abbau“ für die letzte Vorstellung.
- **Orte:** Haus-Orte gelten für alle Stücke, dazu eigene Orte je Stück (mit Foto, Notiz, Bildunterschrift). „Raster anlegen“ (z. B. A–F × 1–4 = 24 Orte) und „Nummerierte Orte“ („Stuhl n“ 1–6). Ein gelöschter Ort bleibt am Gegenstand lesbar und zeigt „Ort entfernt“.
- **Waffe markiert?** Die App bietet die Schritte „… aus dem Waffenschrank holen“ und „… im Waffenschrank einschließen“ an.
- **Einrichtung · Requisite** über der Liste: „Allgemein · Wichtig“ (pinker Rahmen), Dauer, Übersichtsfoto, Personen, Orte des Stücks.
- **PDF-Kapitel Requisite:** Sicherheit, Personen, Ablauf als Tabelle mit Kästchen und Seitenverweis, Verbrauch als Einkaufszettel, Gegenstände nach Ort (mit Ortsfoto) oder nach Person. Dateiname z. B. `Einfache_Leute_Requisite_2026-10-19.pdf`.
- **Abgleich:** Requisite-Gegenstände, ihre Fotos und die Haus-Daten gehen nur an Geräte mit Requisite – per Paket und live. Ein Paket mit Requisite-Inhalt hat **Format 3**; Doku VT 2.4.4 lehnt es mit „bitte zuerst aktualisieren“ ab. Pakete ohne Requisite bleiben Format 2 und für ältere Geräte lesbar. **Alle Geräte, die Requisite-Pakete bekommen, zuerst auf 2.5.0 aktualisieren.**
- „Speicher aufräumen“ behält Übersichts-, Orts- und Vorlagenfotos.
- Abteilungsleiste mit vier Abteilungen: auf dem Smartphone Kurznamen L / T / B / R.
- Rotlicht: graue Hinweistexte minimal heller (Kontrast 4,1 : 1 statt 3,99 : 1).
- **Automatischer Test neu aufgebaut:** `test/test_dokuvt.py`, 31 Prüfungen (Grundfunktionen und Requisite, dazu ein DOM-Vergleich mit 2.4.4 für Geräte ohne Requisite).

## 2.4.4 – 17.10.2026

Aufbau und 2. Phase (Einleuchten, Soundcheck, Einrichten) sind in jeder Abteilung klar zu unterscheiden.

- **Farben weiter auseinander:** Aufbau kräftig und dunkel, 2. Phase hell und blass – Licht Rot ↔ Lachs, Ton Blau ↔ Himmelblau, Bühne Schiefergrau ↔ Hellgrau. Der Kontrast zwischen den Phasen ist etwa doppelt so groß wie vorher.
- **Liste und Kacheln:** Karten der 2. Phase sind ganz hell hinterlegt und hell umrandet, Aufbau-Karten bleiben neutral. Der Farbstreifen links ist breiter.
- **Große Bilder:** Kopfzeile bei Aufbau dunkel mit weißer Schrift, bei der 2. Phase hell mit dunkler Schrift; beide kräftiger als bisher (vorher 50 % abgeschwächt).
- Gilt für Dunkel und Hell; Kamera-Rahmen und PDF-Bänder ziehen mit. Rotlicht bleibt bei Schraffur (Aufbau) und Füllung (2. Phase).
- Neuer Test: Aufbau und 2. Phase müssen je Abteilung mindestens 3,5 : 1 auseinanderliegen (2.4.3: 2,1 : 1 bei Licht).

## 2.4.3 – 16.10.2026

Sicherheit für die Daten – nach der Code-Review: Abgleich über mehrere Geräte, Papierkorb, gleichzeitiges Arbeiten. Kein Datenbank-Update, Paketformat bleibt 2, alle älteren Dateien bleiben lesbar.

- **„Nur Änderungen“ gibt jetzt alles weiter:** Was ein Gerät von einem anderen bekommen hat, geht im nächsten Sync-Paket mit. Vorher fehlten solche Daten beim dritten Gerät (z. B. iPad → iPhone → Pixel), obwohl der Status „Synchron“ zeigte. Grundlage ist eine lokale Eingangszeit je Datensatz (`rx`). Der Stand eines Pakets ist jetzt der Moment des Einsammelns, nicht des Teilens. **Nach dem Update einmal „Komplett“ senden**, damit eventuelle alte Lücken geschlossen sind.
- **Papierkorb bleibt vollständig:** „Speicher aufräumen“ behält die Fotos von Veranstaltungen im Papierkorb (vorher endete „Wiederherstellen“ danach ohne Bilder) und fragt vorher mit Anzahl nach.
- **Wiederherstellen bringt genau zurück, was mit der Veranstaltung gelöscht wurde:** Jeder Löschvorgang bekommt eine Kennung. Ein Eintrag, den ein anderes Gerät inzwischen einzeln gelöscht hat, bleibt gelöscht. Für Löschungen aus 2.4.2 gilt die bisherige Zeitregel.
- **Nichts geht beim schnellen Speichern verloren:** Schnelles Abhaken in „Vor der Vorstellung“ und mehrere Live-Änderungen kurz hintereinander werden alle gespeichert (vorher blieb manchmal nur die letzte).
- **Bearbeiten während des Live-Abgleichs:** Der Eintrag speichert nur, was im Formular geändert wurde. Felder und Fotos, die währenddessen vom anderen Gerät kommen, bleiben erhalten. (Folge: Ein schon doppelt vorhandener Kreis wird beim Bearbeiten eines anderen Feldes nicht mehr automatisch zusammengeführt – dafür weiter „⋯ → zusammenführen“.)
- **Falsch gestellte Geräteuhr:** Eine eigene Änderung gilt immer als neuer als der Wert, den das Gerät gerade anzeigt – auch wenn ein anderes Gerät mit vorgehender Uhr ihn geschrieben hat.
- **Sicherheit beim Import:** Backups, Sync-Pakete und Live-Daten werden geprüft (Kennungen, Feldnamen, Zeitstempel, Größe); ungültige Datensätze werden übersprungen. Kennungen werden in der Oberfläche zusätzlich maskiert – eine präparierte Datei kann kein Skript mehr ausführen. Bilddaten müssen ein JPEG sein.
- **Speichern wirklich atomar:** Schlägt ein einzelner Schreibvorgang fehl, wird nichts gespeichert (vorher wurde der Rest still übernommen). Auch der Arbeitsspeicher der App wird dann zurückgesetzt.
- **PDF:** Ein beschädigtes Foto bricht das PDF nicht mehr ab; an seiner Stelle steht „Bild beschädigt“.
- **Live-Abgleich robuster:** Viele Bilder und gleichzeitiges Speichern bringen die Übertragung nicht mehr zum Stehen.
- **Doppelte Einträge zusammenführen** betrifft nur die Abteilungen, die das Gerät zeigt (vorher auch ausgeblendete, deren Änderung dann nie weiterging).
- Import aus der alten Lichtdoku-App: Ein als JPEG bezeichnetes Bild, das keines ist, wird umgewandelt statt abgewiesen.
- Einstellungen → Info: Hinweis auf die entfernte Suche („/“) gestrichen.
- **Automatischer Test neu:** `test/test_dokuvt.py` (34 Prüfungen, ohne pytest lauffähig). Gegen 2.4.2 schlagen 15 davon fehl.

## 2.4.2 – 16.10.2026

Gelöschte Veranstaltungen lassen sich wiederherstellen.

- **Ausgangslage:** Wird eine Veranstaltung gelöscht, gibt der Abgleich das Löschen an die anderen Geräte weiter (so ist es gewollt). Ein Backup ließ sich danach nicht mehr einspielen: Beim Zusammenführen gewinnt immer das jüngere Löschen – die Meldung lautete „0 neue und 0 zusammengeführte Datensätze“. Die Daten waren aber nie weg.
- **Papierkorb** auf der Startseite (unten, sobald etwas gelöscht ist): gelöschte Veranstaltungen mit Datum, Einträgen und Fotos; „Wiederherstellen“ bringt sie mit allem zurück, was zusammen mit ihr gelöscht wurde. Früher einzeln gelöschte Einträge bleiben gelöscht. Nach dem nächsten Abgleich ist die Veranstaltung auch auf den anderen Geräten wieder da.
- **Backup einer gelöschten Veranstaltung importieren:** Die App erkennt das und fragt „Gelöschte Veranstaltung wiederherstellen?“ – auch für Dateien der alten Lichtdoku-App.
- Der Löschen-Dialog weist auf den Papierkorb hin.

## 2.4.1 – 16.10.2026

Fehlerbehebung: Die App blieb beim Start in einem schwarzen Bild hängen.

- **Ursache:** 2.3.0 hat die Datenbank auf Version 2 erweitert. Ein solches Datenbank-Update muss warten, bis jede andere offene Doku VT-Instanz die Datenbank freigibt. Auf iPad/iPhone (und teils Android) wird eine App im Hintergrund aber eingefroren und gibt sie nie frei – der Start wartete endlos, ohne Meldung.
- **Behebung:** Die Datenbank wird jetzt **ohne Versionsnummer** geöffnet, es gibt kein Datenbank-Update mehr. Durchgänge der Vorstellungs-Checkliste liegen im vorhandenen Speicher „meta“ (Schlüssel „run:<id>“). Datenbanken aus 2.3.0/2.4.0 (mit eigenem Speicher „runs“) werden weiter gelesen – nichts geht verloren.
- **Nie mehr schwarz:** Beim Start steht sofort „Doku VT wird gestartet …“. Antwortet der Datenspeicher nach 5 Sekunden nicht, erscheint ein Hinweis (anderes Fenster schließen) mit „Neu laden“. Ein Fehler beim Start wird mit Meldung angezeigt.

## 2.4.0 – 16.10.2026

Überarbeitung nach der ersten Durchsicht: übersichtlicher, leichter lesbar, in allen Abteilungen gleich aufgebaut.

- **PDF ohne leere Seiten:** Einträge ohne Fotos (oft Ton und Bühne) stehen jetzt zu mehreren auf einer Seite, im selben Infoblock wie auf den Foto-Seiten. Die Reihenfolge bleibt erhalten. Beispiel Garland: 60 statt 76 Seiten.
- **PDF-Inhaltsverzeichnis lesbar:** einspaltig über die volle Breite, je Abteilung eine Kopfzeile mit Spaltennamen und Kapitelseite. Bühne zeigt Position, Element und Ort, Ton Kanal, Quelle und Mikrofon – nichts mehr abgeschnitten.
- **PDF-Kapitel je Abteilung gleich:** Kapitelseite mit „Allgemein“, „Vor der Vorstellung“ (Kästchen zum Abhaken auf Papier) und – je nach Abteilung – Beleuchterzüge bzw. Bühnen-Ablauf (mit Kästchen und Seitenverweis) und Positionen als Tabelle. Die bisher fast leere Trennseite entfällt.
- **Bühne: Reihenfolge „von vorne nach hinten und von unten nach oben“.** Liste, Checkliste und PDF sortieren zuerst nach Bereich (Vorbühne → Portal → Haupt-/Seitenbühne → Hinterbühne), darin nach Ebene (Unterbühne → Boden → Oben). Die Bühnen-Liste ist nach Bereich gegliedert. Der Merksatz ist entfallen.
- **Einrichtung einheitlich:** „Einrichtung · Licht“, „Einrichtung · Ton“, „Einrichtung · Bühne“ – jeweils mit „Allgemein“ (neu auch für Bühne). Ablauf ruhiger (Foto-Knopf rechts statt Textverweis), Positionen als kompakte Tabelle, eingeklappt; leere Beleuchterzüge erscheinen bei Bühne nicht mehr.
- **„Vor der Vorstellung“ direkt in der Veranstaltung:** oben über der Liste, bei Ton und Bühne von selbst aufgeklappt. „Vorstellung heute beginnen“ und gleich abhaken – auch im Ansichtsmodus. Alle Durchgänge und das PDF-Protokoll wie bisher.
- **Klare Namen:** Die Aufbau-Haken an den Einträgen heißen jetzt „Abhaken“ (vorher ebenfalls „Checkliste“).
- **Rotlicht lesbar:** In der Ansicht „Große Bilder“ liegt keine Schraffur mehr hinter Kreis/Kanal/Position (Aufbau nur noch als schraffierte Linie). Graue und gedimmte Texte sind heller (Kontrast mindestens 4:1).
- **Eingabefelder einheitlich:** Feldnamen überall in derselben Schrift, kürzere Namen (Ton: „Kanal“, „Quelle“; Bühne: „Position“, „Element“, „Höhe / Marke“), Platzhalter werden nicht mehr abgeschnitten.
- **Sortierung Hauptfeld:** erst Nummern, dann Namen (Ton: 1, 2, 11 … Aux 1, Aux 2 … Video 1).

## 2.3.0 – 16.10.2026

Etappe 4: Vorstellungs-Checkliste – vor jeder Vorstellung abhaken, mit Protokoll.

- **Vorstellungs-Checkliste** je Veranstaltung (Knopf mit Haken-Symbol in der Kopfzeile, auch im Menü der Veranstaltung): Punkte je Abteilung, z. B. „Funkakkus voll“, „Notbeleuchtung geprüft“. Bei Bühne erscheinen zusätzlich die Schritte aus dem **Ablauf** (Grundeinrichtung, Pausenumbau, Ende) automatisch als Punkte.
- **„Neue Vorstellung“** legt einen Durchgang mit Datum an. Abhaken geht **auch im Ansichtsmodus** (großer Haken, 48 px); jeder Haken zeigt Uhrzeit und Gerät. Fortschritt je Abteilung und gesamt; offene Punkte sind pink markiert. Frühere Durchgänge bleiben zum Nachschlagen erhalten. Löschen und Punkte bearbeiten nur im Bearbeitungsmodus.
- **Abgleich ohne Verlust:** Jeder Haken ist ein eigenes Feld mit Zeitstempel. Haken von mehreren Geräten (z. B. Licht auf dem iPad, Ton auf dem Pixel) werden zusammengeführt. Ein Gerät schickt nur die Haken seiner Abteilungen.
- **Punkte bearbeiten:** je Abteilung anlegen, umsortieren, entfernen; „Als Hausvorlage speichern“ – neue Veranstaltungen bekommen diese Punkte automatisch (nur für die gewählten Abteilungen). Ohne Hausvorlage gibt es sinnvolle Beispielpunkte. Duplizieren übernimmt die Punkte.
- **PDF-Protokoll** eines Durchgangs (herunterladen/teilen): Zusammenfassung, Punkte je Abteilung mit Haken, Uhrzeit, Gerät, offene Punkte hervorgehoben und am Ende aufgelistet.
- Datenbank Version 2 (neuer Speicher „runs“). Bestehende Daten bleiben unverändert; das Update läuft beim ersten Start automatisch.
- PDF: Überschriften im Inhaltsverzeichnis werden nicht mehr abgeschnitten.
- Demo „Der Haifisch“ mit Beispielpunkten der Vorstellungs-Checkliste.

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
