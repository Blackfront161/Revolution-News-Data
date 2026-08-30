# WRN Exa Discovery Prototype

Dieser Prototyp benutzt Exa **nur als ergänzende Recherche-Schicht**. Er ersetzt
den bestehenden RSS-/Feed-Aggregator nicht und schreibt absichtlich nicht direkt
in `news.json`.

## Was der Lauf macht

1. Vier semantische Suchprofile aus `exa-queries.json` werden ausgeführt.
2. Exa liefert maximal acht aktuelle Treffer pro Profil.
3. URLs, die bereits in `news.json` vorkommen, werden entfernt.
4. Doppelte Treffer zwischen den Suchprofilen werden zusammengeführt.
5. Übrig gebliebene Kandidaten landen in `exa-discovery.json`.
6. Die gemeldeten Exa-Kosten des Laufs werden mitgespeichert.

Damit ist das Ergebnis zunächst eine **Review Queue**. Erst wenn die Trefferqualität
stabil ist, sollte eine automatische Übernahme in den normalen WRN-Feed gebaut
werden.

## Einrichtung

Im GitHub-Repository unter **Settings → Secrets and variables → Actions** ein
Repository Secret namens `EXA_API_KEY` anlegen. Ohne Secret beendet sich der
Workflow erfolgreich, führt aber keine kostenpflichtige Suche aus.

Der Schlüssel gehört ausschließlich in GitHub Secrets und niemals in JavaScript,
`config.js`, `news.json` oder andere öffentlich ausgelieferte Dateien.

## Kostenbremse

Der geplante Lauf startet alle acht Stunden. Bei vier Suchprofilen sind das
ungefähr 360 Search-Requests pro 30 Tage. Mit maximal acht Resultaten pro Query
bleibt das bewusst deutlich unter einer aggressiven Monitoring-Frequenz.

Der Workflow stoppt außerdem, wenn Exa für einen einzelnen Lauf mehr als
1 US-Dollar meldet.

## Lokal testen

```bash
python exa_discovery.py --dry-run
python -m unittest tests.test_exa_discovery
```

Live-Suche:

```bash
EXA_API_KEY="..." python exa_discovery.py
```

## Nächster Integrationsschritt

Nach einigen Testläufen kann `exa-discovery.json` als Quelle für eine redaktionelle
Freigabe im bestehenden WRN Editorial Review dienen. Danach wäre eine zweite Stufe
möglich, in der bestätigte Exa-Kandidaten in die bestehende Normalisierung und
Deduplizierung von `aggregate.py` übergeben werden.
