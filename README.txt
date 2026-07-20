WORLD REVOLUTION NEWS – HOTFIX 1.7.21a

URSACHE

Der Workflow verwies auf:

    tests/test_origin_safety.js
    tests/test_repository_hardening.py
    scripts/wrn-safe-push.sh

Mindestens der Ordner tests wurde beim Hochladen nicht ins Repository
übernommen. Deshalb konnte Node die Testdatei nicht finden.

BEHOBEN

- Die entscheidenden Origin-Sicherheits- und Workflow-Tests sind direkt
  in apply-origin-safety.yml eingebettet.
- Der Workflow hängt nicht mehr von den Dateien unter tests/ ab.
- wrn-safe-push.sh liegt im Hauptverzeichnis.
- harden_wrn_repository.py erzeugt künftig ebenfalls Verweise auf die
  root-level Datei wrn-safe-push.sh.
- Vor dem Lauf prüft der Workflow verständlich, ob alle Pflichtdateien
  vorhanden sind.
- Die separaten Testdateien liegen zusätzlich im Hauptverzeichnis und
  können dort manuell ausgeführt werden.

HOCHLADEN

Den gesamten ZIP-Inhalt ins Hauptverzeichnis laden.

Ersetzen:

    .github/workflows/apply-origin-safety.yml
    harden_wrn_repository.py

Neu hinzufügen:

    wrn-safe-push.sh
    test_origin_safety.js
    test_repository_hardening.py

Die alten Dateien unter tests/ und scripts/ müssen nicht gelöscht werden.
Der neue Workflow benötigt sie nicht mehr.

COMMIT

Fix 1.7.21 origin safety test paths

DANACH

GitHub
→ Actions
→ Apply 1.7.21 origin safety
→ Run workflow

ERWARTETE SCHRITTE

- Benötigte Sicherheitsdateien prüfen
- Aktuelle Reparaturseiten und Workflows absichern
- JavaScript-Syntax prüfen
- Origin-Sicherheit direkt testen
- Workflow-Härtung direkt testen
- Service-Worker-Scope statisch prüfen
- App-Validator ausführen
- Änderungen speichern
