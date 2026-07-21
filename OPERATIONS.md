# World Revolution News – Betrieb

## Aktive Workflows

Dauerhaft aktiv bleiben:

- `Update News`
- `Update Podcasts`
- `Merge Multilingual Sources`
- `Repair Audio`
- `WRN Quality Gate`
- `App prüfen`

Alle Workflows, die nach `main` schreiben, verwenden:

```yaml
concurrency:
  group: wrn-main-write
  cancel-in-progress: false
```

Ein Workflow darf niemals andere Dateien unter `.github/workflows/`
automatisch verändern oder committen.

## Empfohlene Reihenfolge

1. Änderungen lokal auf einem separaten Branch einspielen.
2. Pull Request öffnen.
3. `WRN Quality Gate` und `App prüfen` abwarten.
4. Erst bei grünen Prüfungen nach `main` mergen.
5. `Update News` oder `Update Podcasts` nur danach manuell starten.
6. `Repair Audio` nur bei Änderungen an Audioquellen ausführen.

Nie zwei schreibende Workflows gleichzeitig starten.

## Release-Regel

Neue Releases werden nicht durch einmalige selbstverändernde Apply-Workflows
installiert. Änderungen werden gegen eine vollständige aktuelle
Repository-Kopie getestet und als normaler Branch/Commit eingespielt.

## Aktueller Release 1.8.1

### Entwicklungen und Briefing 2

- Der sichtbare Reiter heißt „Entwicklungen“.
- Story-Clustering bleibt intern unter `WRNStories` kompatibel.
- Beobachtungsbegriffe liegen unter `wrn_story_watchlist_v1`.
- Briefing-Verlauf und Briefing-2-Modus bleiben lokal.

### Audio

Die sichtbare Hierarchie lautet:

1. Audio
2. Original-Podcasts / Erzeugte Podcasts / Live-Radio
3. Herkunftsfilter nur innerhalb von Original-Podcasts

Die Herkunftszuordnung wird durch `audio-region-core.js` normalisiert.
Radiosender dürfen mehrere `streamCandidates` besitzen.

### Sprachen

Unterstützt und auswählbar sind:

- Deutsch
- Englisch
- Spanisch
- Französisch
- Italienisch
- Portugiesisch
- Russisch
- Griechisch
- Türkisch

Keine dieser Sprachen wird als Beta behandelt.

### Quellenprüfung

- Ein echter permanenter HTTP-/DNS-Fehler darf als defekt erscheinen.
- Ein noch nicht ausgeführter Audio-Check erscheint als „Nicht geprüft“.
- Fehlende optionale Berichtdateien werden als Warnung behandelt.
- Radioeinträge werden mit `radio-stations.json` abgeglichen.

### Video-Hub

- Der Hub wertet nur bereits geladene Nachrichtendaten lokal aus.
- Externe Player werden erst nach einer bewussten Auswahl geladen.
- Es gibt keine automatische Wiedergabe.
- YouTube-Einbettungen verwenden `youtube-nocookie.com`.

## Aggregator-Sicherheit

`aggregate.py` verarbeitet jeden Feed-Eintrag innerhalb einer eigenen
Fehlergrenze. Fehlerhafte Einträge dürfen nicht den vollständigen Lauf
abbrechen. Fehler werden nach `aggregate-errors.json` geschrieben.

## Generierte Podcasts

`generated-podcasts.json` muss immer gültiges JSON und eine Liste enthalten.
Der Service Worker besitzt einen eigenen Fallback für diese Datei.

## Abhängigkeiten

Normale Datenworkflows sollen `requirements-wrn.lock.txt` verwenden.
Versionsänderungen erfolgen nur bewusst in einem eigenen Wartungscommit.
