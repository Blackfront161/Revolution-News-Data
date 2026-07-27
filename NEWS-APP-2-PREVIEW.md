# News App 2 – isolierte Vorschau

Diese Vorschau entwickelt World Revolution News parallel zur veröffentlichten App weiter. Sie ersetzt keine bestehende Datei, registriert keinen Service Worker und verändert weder `index.html` noch die produktiven Cloudflare Worker.

## Lokal testen

```powershell
node scripts/serve_news_app_2.js
```

Danach `http://127.0.0.1:8765/next.html` öffnen.

Die lokale Vorschau verwendet öffentliche Daten aus dem Repository. Übersetzungsanfragen von `127.0.0.1` können vom produktiven Worker wegen dessen Origin-Schutz abgelehnt werden. Das ist beabsichtigt; die produktive Origin-Liste wird für diese Vorschau nicht gelockert.

## Bereits umgesetzt

- getrennte Navigation für Start, Für mich, Entdecken, Medien und Gespeichert
- zehn aktuelle, nach Quellen durchmischte Artikel als Standardansicht
- höchstens zwei Beiträge derselben Quelle unter den ersten zehn
- lokale Interessenwahl nach Regionen und Themen
- Suche und Filter mit bis zu 40 Treffern nach aktiver Auswahl
- Video-, Podcast- und Radio-Einstiege
- kompatible gespeicherte Artikel über den bestehenden Schlüssel `wrn_bookmarks`
- Übersetzen direkt in der Artikelübersicht für Titel und Einleitung
- Artikelansicht mit Übersetzen, Speichern und Original öffnen
- neun angebotene Oberflächensprachen
- mobile Vollbild-Artikelansicht und mindestens 44 × 44 Pixel große Bedienflächen

## Sichere Einführung

1. Vorschau auf diesem Branch weiter testen.
2. Fehlende Spezialbereiche schrittweise direkt einbauen; bis dahin öffnen sie die klassische App.
3. Erst nach Regressionstests einen optionalen, deaktivierten Feature-Schalter in die Haupt-App aufnehmen.
4. Kleine freiwillige Testgruppe aktivieren und Rückmeldungen auswerten.
5. Erst danach eine neue Android-Version bauen. Die aktuelle Play-Store-App bleibt bis dahin unverändert.

## Noch nicht produktiv geschaltet

- eigener Offline-Cache für die neue Oberfläche
- vollständige neue Ansichten für Termine, Lexikon, politische Gefangene und Entwicklungen
- produktive Freischaltung des neuen Designs
- Änderung an Google Play, GitHub Pages oder Cloudflare
