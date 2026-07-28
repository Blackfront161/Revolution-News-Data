# News App 2 – Release-Checkliste 2.0.0-rc.1

Stand: 28. Juli 2026

Branch: `agent/news-app-2-preview`

Vorschau: `next.html?preview=8`

## Schutz der bisherigen App

- [x] `index.html` ist unverändert.
- [x] `service-worker.js` ist unverändert.
- [x] RC1 verwendet ausschließlich `next.html` und `news-app-2-sw.js`.
- [x] Der Vorschau-Cache trägt einen eigenen Namen und eine eigene Version.
- [x] Es wurde nichts auf GitHub Pages, Cloudflare oder Google Play veröffentlicht.

## Funktionsabgleich

| Bereich | RC1 |
|---|---|
| Startseite mit zehn durchmischten Meldungen | vollständig |
| „In 5 Minuten“ mit fünf Meldungen | vollständig; Übersetzung auf freigegebener Origin |
| Suche, 7/30 Tage und Gesamtarchiv | vollständig |
| Regionen und redaktionell gruppierte Themen | vollständig |
| Sprache, Herkunft, Format, Quelle, Sortierung | vollständig |
| Karten-, Kompakt- und Schlagzeilenansicht | vollständig |
| Persönlicher Feed | vollständig |
| Quellen folgen oder ausblenden | vollständig |
| Gefangene und Entwicklungen beobachten | vollständig |
| Artikel öffnen, Original, Übersetzen, Vergleich | vollständig |
| Zusammenfassung kurz/standard/ausführlich | vollständig |
| Gerätestimme und natürliche Podcast-Stimme | vollständig; Online-Stimme auf freigegebener Origin |
| Teilen, später lesen, gelesen, Lesefortschritt | vollständig |
| Zine-Auswahl, Gestaltung und PDF/Druck | vollständig |
| Video, Original-Podcasts, erzeugte Podcasts, Radio | vollständig |
| Audio-Warteschlange, Favoriten, Weiterhören, Timer | vollständig |
| Termine, Archiv, Filter, Umkreis, Karte, Route, ICS | vollständig |
| Lexikon und Quellen | vollständig |
| Gefangenen-Solidarität und Briefwerkstatt | vollständig |
| Entwicklungen mit Mehrquellenabgleich | Beta wie bisher vorgesehen |
| Quellenprofile und Quellenprüfung | vollständig |
| Redaktionelle Prüfliste | vollständig |
| Systemstatus und lokale Datenverwaltung | vollständig |
| Spenden und Projektinformationen | vollständig |

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

## Technische Prüfungen

- [x] JavaScript-Syntaxprüfung.
- [x] News-App-2 Core-, Specialty-, Media- und Release-Vertragstests.
- [x] Artikelaktionen, Teilen, Podcast und gemeinsamer Übersetzungsclient.
- [x] Asset-, CSP- und Vorschau-Isolationsprüfung.
- [x] Whitespace-/Patchprüfung.
- [x] Keine Änderung an den beiden produktiven Einstiegsdateien.
- [x] Service Worker ist in der Vorschau aktiv.

## Verpflichtende Prüfungen vor Produktion

- [ ] RC1 auf einer nichtproduktiven, beim Übersetzungsdienst freigegebenen
  HTTPS-Origin bereitstellen.
- [ ] Dort je einen kurzen und einen langen Artikel in alle neun
  Oberflächensprachen übersetzen.
- [ ] Dort einen kurzen und einen vollständigen natürlichen Podcast erzeugen.
- [ ] Einen echten Smartphone-Test auf Android und iOS einschließlich
  Installation, Offline-Neustart, Teilen, Erinnerung, Audio-Unterbrechung und
  Wiederaufnahme durchführen.
- [ ] Nach einer bewusst getrennten Freigabe die produktiven Einstiegspunkte
  und den Android-Wrapper auf RC1 umstellen.
- [ ] Für das neue Android App Bundle R8/Minifizierung aktivieren und den
  Play-Console-Bericht erneut kontrollieren. Die gezeigte bisherige Version
  unterstützt zwar 16-KB-Speicherseiten, ist laut Play Console aber nur
  niedrig optimiert.

## Bewusst nicht Teil dieses Releases

- alternative soziale Medien
- ein späterer Briefing-Verlauf mit Export, Import und Rückmeldungen
- weitere Zukunftsideen, die noch nicht Bestandteil der bisherigen Live-App waren

## Freigabeentscheidung

RC1 ist als Code- und Oberflächenkandidat bereit. Die Produktionsfreigabe
bleibt absichtlich gesperrt, bis Übersetzung und natürliche Podcast-Erzeugung
auf einer freigegebenen Test-Origin sowie das neue Android App Bundle geprüft
wurden.
