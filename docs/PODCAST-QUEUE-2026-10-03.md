# Bestehende Datenschreibgruppe: wartende Läufe erhalten

Der geplante Podcastlauf [37100648981](https://github.com/Blackfront161/Revolution-News-Data/actions/runs/37100648981) vom 3.10., 05:41 UTC, wurde mit `cancelled` vor dem Start eines Jobs beendet (`jobs: []`). Er bestätigt deshalb weder den reparierten Publikationspfad noch eine erfolgreiche geplante Aktualisierung. Der direkte erfolgreiche Lauf 37085213675 bleibt separat belegt.

Alle acht Datenschreibworkflows teilen bereits die Gruppe `wrn-main-write`. `cancel-in-progress: false` schützt den laufenden Job; die bisherige Standardwarteschlange schützt zusätzliche wartende Jobs nicht. Eine spätere Einreihung kann den einzigen wartenden Lauf ersetzen. Das passt zur Beobachtung; die API liefert für diesen konkreten Abbruch keinen separaten Verursacher.

Der Kandidat ergänzt ausschließlich `queue: max` an diesen acht vorhandenen Gruppen. GitHub dokumentiert damit bis zu100 wartende Läufe; ein voller Puffer kann weitere Läufe weiterhin ablehnen. Der aktive Schreiber bleibt auf einen Lauf begrenzt. Keine Änderung an Zeitplänen, Berechtigungen, Aggregatoren, Rechteprüfung, Pfad-Allowlist oder Safe-Push. Die getrennte Quality-Gate-Gruppe bleibt unverändert.

Primärreferenzen: [GitHub-Concurrency](https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency), [Queue-Konfiguration](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency), [Einführung am7.5.2026](https://github.blog/changelog/2026-05-07-github-actions-concurrency-groups-now-allow-larger-queues/).

Die Syntax- und bestehenden Publikationstests prüfen den Quellkandidaten. Die unabhängige Prüfung sowie ein erfolgreicher geplanter Lauf nach Merge und öffentlicher Readback bleiben notwendig. Keine schedulerweite Erfolgsbehauptung aus lokalen Tests.
