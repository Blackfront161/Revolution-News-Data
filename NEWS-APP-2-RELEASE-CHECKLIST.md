# News App 2 – Release-Checkliste 2.0.0

Stand: 29. Juli 2026

Branch: `agent/news-app-2-preview`

Vorschau: `next.html?preview=8`

## Produktion und Rückfall

- [x] `index.html` startet News App 2.
- [x] `next.html` führt kontrolliert zur produktiven App.
- [x] Die klassische Oberfläche bleibt unter `classic.html` erhalten.
- [x] Produktions- und Vorschau-Service-Worker bleiben getrennt.
- [x] Google Play wird erst mit dem abschließend geprüften AAB aktualisiert.

## Funktionsabgleich

Die mobil lesbare Fassung liegt unter
`news-app-2-release-checklist.html`.

Statusbedeutung:

- **Bestanden:** lokal geprüft und ohne bekannten Fehler.
- **Integriert:** vorhanden; ein externer Online- oder Gerätetest ist noch nötig.
- **Offen:** muss vor dem Play-Store-Upload erledigt werden.

| Bereich | RC1 |
|---|---|
| Startseite mit zehn durchmischten Meldungen | Bestanden |
| „In 5 Minuten“ mit fünf Meldungen | Integriert; Übersetzungs-End-to-End-Test offen |
| Suche, 7/30 Tage und Gesamtarchiv | Bestanden |
| Regionen und redaktionell gruppierte Themen | Bestanden |
| Sprache, Herkunft, Format, Quelle, Sortierung | Bestanden |
| Karten-, Kompakt- und Schlagzeilenansicht | Bestanden |
| Persönlicher Feed | Bestanden |
| Quellen folgen oder ausblenden | Bestanden |
| Gefangene und Entwicklungen beobachten | Bestanden |
| Artikel öffnen, Original, Übersetzen, Vergleich | Integriert; Übersetzungs-End-to-End-Test offen |
| Zusammenfassung kurz/standard/ausführlich | Bestanden |
| Gerätestimme | Bestanden |
| Natürliche Podcast-Stimme | Integriert; Online-End-to-End-Test offen |
| Teilen, später lesen, gelesen, Lesefortschritt | Bestanden |
| Zine-Auswahl, Gestaltung und PDF/Druck | Bestanden |
| Video, Original-Podcasts, erzeugte Podcasts, Radio | Bestanden; neue Podcast-Erzeugung extern prüfen |
| Audio-Warteschlange, Favoriten, Weiterhören, Timer | Bestanden |
| Termine, Archiv, Filter, Umkreis, Karte, Route, ICS | Bestanden |
| Lexikon und Quellen | Bestanden |
| Gefangenen-Solidarität: 12 Profile, davon 7 aus Europa | Bestanden |
| Starthilfe, Sprachauswahl, Übersetzungsvergleich und Quellen-Reiter | Bestanden; HTTPS-Endtest der Briefübersetzung folgt |
| Entwicklungen mit Mehrquellenabgleich | Integriert; Beta wie vorgesehen |
| Quellenprofile und Quellenprüfung | Bestanden |
| Redaktionelle Prüfliste | Bestanden |
| Systemstatus und lokale Datenverwaltung | Bestanden |
| Spenden und Projektinformationen | Bestanden |

## Bedienung und Darstellung

- [x] Mobile Ansicht bei 390 × 844 Pixel ohne horizontalen Überlauf.
- [x] Desktop-Ansicht bei 1440 × 900 Pixel ohne horizontalen Überlauf.
- [x] Untere Navigation bleibt beim Scrollen positionsstabil.
- [x] Artikelbilder werden mit korrektem Seitenverhältnis und ohne Beschnitt dargestellt.
- [x] „Artikel öffnen“ und „Übersetzen“ verwenden dieselbe Form und Höhe.
- [x] Aktiver Übersetzungsstern entspricht der rot-schwarzen Gestaltung.
- [x] Aktive Medienreiter sind rot mit schwarzer Schrift.
- [x] Zine ist als eigener Medienreiter vorhanden.
- [x] Schriftvergrößerung bis 200 Prozent bleibt ohne horizontalen Überlauf bedienbar.
- [x] OLED, gedämpft, hell, System und hoher Kontrast sind verfügbar.
- [x] Die neuen RC1-Funktionen sind in allen neun App-Sprachen beschriftet.
- [x] Medien starten nie automatisch.
- [x] Die visuelle Android-Smartphone-Vorschau wurde vom Nutzer geprüft.

## Technische Prüfungen

- [x] JavaScript-Syntaxprüfung.
- [x] News-App-2 Core-, Specialty-, Media- und Release-Vertragstests.
- [x] Artikelaktionen, Teilen, Podcast und gemeinsamer Übersetzungsclient.
- [x] Asset-, CSP- und Vorschau-Isolationsprüfung.
- [x] Whitespace-/Patchprüfung.
- [x] Sichere externe Quellenlinks ohne Referrer-Weitergabe.
- [x] Produktiver Service Worker und Cache-Aktualisierung.
- [x] Feed-Zeitbudget, atomare Prüfpunkte und gemeinsame Veröffentlichung von
  `news-feed.json`, `events-feed.json` und `feed-status.json`.
- [x] Produktiver Feed-Status vom 28. Juli 2026 meldet Erfolg.
- [x] Sieben zusätzliche Animal-Liberation-RSS-Quellen geprüft und registriert.

## Noch vor dem Play-Store-Upload

- [ ] Briefübersetzung mit gewählter Zielsprache auf der freigegebenen
  produktiven HTTPS-Adresse prüfen.
- [ ] Nach erfolgreichen GitHub-Prüfungen das signierte AAB exakt aus dem
  freigegebenen Hauptbranch bauen.
- [ ] Signatur, R8/Minifizierung, enthaltenen Webstand, SHA-256 und Versionscode
  10 im Buildbericht prüfen.
- [ ] AAB zunächst in Google Play hochladen und Installation sowie
  Offline-Neustart auf Android testen.

## Bewusst nicht Teil dieses Releases

- alternative soziale Medien
- ein späterer Briefing-Verlauf mit Export, Import und Rückmeldungen
- weitere Zukunftsideen, die noch nicht Bestandteil der bisherigen Live-App waren

## Freigabeentscheidung

Die Web-App ist bereit. Der Play-Store-Upload folgt erst nach bestandenem
AAB-Bericht und anschließendem Android-Gerätetest.
