# World Revolution News – Betrieb

## Aktive Schreibworkflows

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

1. Änderungen lokal oder auf einem separaten Branch einspielen.
2. `WRN Quality Gate` abwarten.
3. Erst danach `Update News` oder `Update Podcasts` manuell starten.
4. `Repair Audio` nur bei Änderungen an Audioquellen ausführen.

Nie zwei schreibende Workflows gleichzeitig starten.

## Release-Regel

Neue Releases werden nicht mehr durch einmalige selbstverändernde
Apply-Workflows installiert. Änderungen werden zuerst gegen eine vollständige
Repository-Kopie getestet und anschließend als normaler Commit eingespielt.

## Aggregator-Sicherheit

`aggregate.py` verarbeitet jeden Feed-Eintrag innerhalb einer eigenen
Fehlergrenze. Fehlerhafte Titel, Autor:innenfelder, Datumswerte oder
Enclosures dürfen nicht den vollständigen Lauf abbrechen.

Fehler werden nach `aggregate-errors.json` geschrieben.

## Generierte Podcasts

`generated-podcasts.json` muss immer gültiges JSON und eine Liste enthalten.
Der Service Worker besitzt einen eigenen Fallback für diese Datei.

## Geschichten und Briefing 2

- Story-Clustering erfolgt lokal im Browser.
- Beobachtungsbegriffe liegen unter `wrn_story_watchlist_v1`.
- Briefing-Verlauf und Briefing-2-Modus bleiben lokal.
- Es werden dafür keine Nutzerkonten oder zusätzlichen Serverdaten benötigt.

## Abhängigkeiten

Normale Datenworkflows sollen `requirements-wrn.lock.txt` verwenden.
Versionsänderungen erfolgen nur bewusst in einem eigenen Wartungscommit.
