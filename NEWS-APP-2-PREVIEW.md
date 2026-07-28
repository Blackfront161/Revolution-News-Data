# News App 2 – isolierte Vorschau

Diese Vorschau entwickelt World Revolution News parallel zur veröffentlichten App weiter. Sie ersetzt keine bestehende Einstiegsdatei und verändert weder `index.html` noch die produktiven Cloudflare Worker. Ihr eigener Service Worker gilt ausschließlich für den Pfad `next.html` und verwendet getrennt benannte Caches.

## Lokal testen

```powershell
node scripts/serve_news_app_2.js
```

Danach `http://127.0.0.1:8765/next.html` öffnen.

Für einen Test auf einem Smartphone im selben privaten WLAN:

```powershell
node scripts/serve_news_app_2.js --host 0.0.0.0
```

Das Skript gibt anschließend die passenden WLAN-Adressen für das Smartphone aus. Eine Windows-Firewall-Freigabe nur für private Netzwerke erteilen.

Die lokale Vorschau verwendet öffentliche Daten aus dem Repository. Übersetzungsanfragen von `127.0.0.1` können vom produktiven Worker wegen dessen Origin-Schutz abgelehnt werden. Das ist beabsichtigt; die produktive Origin-Liste wird für diese Vorschau nicht gelockert.

## Bereits umgesetzt

- getrennte Navigation für Start, Für mich, Entdecken, Medien und Gespeichert
- zehn aktuelle, nach Quellen durchmischte Artikel als Standardansicht
- höchstens zwei Beiträge derselben Quelle unter den ersten zehn
- lokale Interessenwahl nach Regionen und Themen
- Suche und Filter mit schrittweisem Nachladen
- nativer Medienbereich mit getrennten Ansichten für aktuelle und informative Videos, Original-Podcasts, erzeugte Podcasts und Live-Radio
- Podcast-Suche sowie Filter nach Region und den Kategorien Politik, Gesellschaft und Kultur
- datensparsames Audio: Podcasts und Radios starten niemals automatisch; defekte Streams verweisen auf die Originalseite
- kompatible gespeicherte Artikel über den bestehenden Schlüssel `wrn_bookmarks`
- Übersetzen direkt in der Artikelübersicht für Titel und Einleitung
- Artikelansicht mit kompakter Werkzeugleiste für Zusammenfassen, Übersetzungsvergleich, kostenlose Gerätestimme, Zine, Lesestatus und Teilen
- Originalquelle als ruhiger Link im Artikel statt als großer Aktionsbutton
- am Artikelende bis zu fünf weitere Meldungen derselben Quelle; der aktuell geöffnete Artikel ist links cyan markiert
- neun angebotene Oberflächensprachen
- mobile Vollbild-Artikelansicht und mindestens 44 × 44 Pixel große Bedienflächen
- sinnorientiertes Hamburger-Menü ohne doppelte Navigation: Farbdarstellung, Schriftgröße und Artikeldichte sowie getrennte Bereiche für Projekt und Diagnose
- dreistufiger, vollständig lokaler Briefing-Assistent für Themen/Regionen, Sprache/Länge und Vorlesen
- automatische Übersetzung der fünf Start-Kurzmeldungen in die App-Sprache; bereits übersetzte Meldungen werden lokal wiederverwendet
- responsive Bilder ohne Abschneiden: vollständige Darstellung im Desktop-Rahmen und auf Smartphones oberhalb des Artikels
- vollständige Einleitungen in der Nachrichtenübersicht ohne harte Zeilenbegrenzung
- klar getrennte Bereiche für Themen-/Regionsmarkierungen und Artikelaktionen
- Nachrichtenarchiv mit den Zeiträumen aktuell, 7 Tage, 30 Tage und alle Artikel
- Regionen als einheitliches Filterraster und Themen in vier redaktionellen Ressorts statt einer unstrukturierten Gesamtliste
- erweiterte lokale Feed-Einrichtung für Regionen, Themen, bevorzugte oder ausgeblendete Quellen, beobachtete Gefangene und Entwicklungen, App-Sprache und Briefing-Länge
- kompaktere Entdecken- und Medienauswahl mit redaktionell geordneten Themen
- Zine-Werkstatt im Medienbereich mit gemeinsamer lokaler Artikelliste, Gestaltung sowie Druck-/PDF-Ausgabe
- Termine mit Suche, Länderfilter, Enddatum-Logik, Archiv und zusammengefassten Wiederholungen
- Lexikon mit mehreren Unterbereichen, Suche, 100+ Begriffen, Quellen und Downloads
- Gefangenen-Solidarität mit verifizierten Profilen, zugehörigen Nachrichten und privater Briefwerkstatt
- „Entwicklungen · Beta“ mit strengem Mehrquellenabgleich, sichtbarer Verbindungsbegründung und lokaler Beobachtungsliste
- eigener Offline-Cache mit netzwerkbevorzugten Updates für JavaScript, CSS und Daten

## Sichere Einführung

1. Vorschau auf diesem Branch weiter testen.
2. Medienbereiche und weitere Detailfunktionen schrittweise direkt einbauen.
3. Erst nach Regressionstests einen optionalen, deaktivierten Feature-Schalter in die Haupt-App aufnehmen.
4. Kleine freiwillige Testgruppe aktivieren und Rückmeldungen auswerten.
5. Erst danach eine neue Android-Version bauen. Die aktuelle Play-Store-App bleibt bis dahin unverändert.

## Noch nicht produktiv geschaltet

- produktive Freischaltung des neuen Designs
- Änderung an Google Play, GitHub Pages oder Cloudflare

## Noch nicht aus der bisherigen App übernommen

- serverseitig erzeugte MP3-Podcasts mit natürlichen Azure-Stimmen direkt aus einem Artikel; die kostenlose Gerätestimme ist bereits vorhanden
- der erweiterte Briefing-Verlauf mit Export, Import und Rückmeldungen
- vollständige Quellen-/Archivprüfung innerhalb der neuen Oberfläche; die bestehenden Diagnose-Seiten sind bereits verlinkt

Die lokale Smartphone-Vorschau bleibt absichtlich von den produktiven
Übersetzungs-Origins getrennt. Automatische Übersetzungen werden in einer
freigegebenen App- oder Web-Origin ausgeführt und anschließend lokal
wiederverwendet; die Live-Worker werden für LAN-Adressen nicht geöffnet.
