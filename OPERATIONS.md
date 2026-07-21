# World Revolution News – Betrieb

## Aktive Schreibworkflows

Alle Workflows, die nach `main` schreiben, verwenden:

```yaml
concurrency:
  group: wrn-main-write
  cancel-in-progress: false
```

Ein Workflow darf niemals andere Dateien unter `.github/workflows/`
automatisch verändern oder committen.

## Empfohlene Reihenfolge

1. `Apply 1.7.23 aggregator hardening`
2. `WRN Quality Gate`
3. `Update News`
4. `Repair and verify audio`, nur wenn Audioquellen geändert wurden

Nie zwei schreibende Workflows gleichzeitig manuell starten.

## Aggregator-Sicherheit

`aggregate.py` verarbeitet jeden Feed-Eintrag innerhalb einer eigenen
Fehlergrenze. Fehlerhafte Titel, Autor:innenfelder, Datumswerte oder
Enclosures dürfen nicht den vollständigen Lauf abbrechen.

Fehler werden nach `aggregate-errors.json` geschrieben.

## Generierte Podcasts

`generated-podcasts.json` muss immer gültiges JSON und eine Liste enthalten.
Existiert eine ältere kompatible Datei, wird deren Inhalt übernommen.
Andernfalls wird eine leere Liste veröffentlicht, damit keine 404-Anfragen
entstehen.

## Repository-Hygiene

Automatisch entfernbar sind nur:

- versionierte `.pyc`/`.pyo`-Dateien
- Inhalte versionierter `__pycache__`-Ordner
- identische Workflow-Kopien im Hauptverzeichnis
- eine identische alte Kopie von `scripts/wrn-safe-push.sh`

Abweichende Kopien werden nur in `repository-cleanup-report.json` gemeldet.

## Wiederherstellung

Vor einer Änderung an `aggregate.py` erzeugt der Patcher:

```text
aggregate.py.pre-1723.bak
```

Diese lokale Sicherung wird durch `.gitignore` nicht versioniert.

## Abhängigkeiten

Normale Datenworkflows sollen `requirements-wrn.lock.txt` verwenden.
Versionsänderungen erfolgen nur bewusst in einem eigenen Wartungscommit.
