# Autonome Quellen: Aufnahmeumfang und Primärbelege

Vom Nutzer beauftragt: zusätzliche autonome und antifaschistische Quellen prüfen
und geeignete Quellen aufnehmen. Recherche am 30. September 2026, Paketabschluss
am 1. Oktober (Asia/Singapore). Aktuelle Datenbasis: `33509ac` von `origin/main`.
Der App-, Website- und Next-Code wird in diesem Datenpaket nicht verändert.

| Quelle | Aufnahme | Direkt beobachtet / Selbstauskunft | Offene Punkte |
| --- | --- | --- | --- |
| Autonome Antifa Freiburg | Verzeichnis, kein automatischer Artikelimport | Homepage nennt diese Eigenbezeichnung; Meldung vom 30.09.2026 sichtbar. RSS-Artikelkanal erreichbar (HTTP 200, XML), jüngster dort beobachteter Artikel vom 26.04.2026. Meldungs- und Artikelkanal nicht verwechselt. | Verantwortliche Einzelpersonen, Finanzierung und allgemeine Medienrechte unbekannt. Beiträge mit Personenbezug und Mobilisierungen einzeln prüfen. |
| antifa-frankfurt.org | Verzeichnis, kein automatischer Artikelimport | Eigenbeschreibung: neues Redaktionskollektiv, antifaschistisches Portal für Frankfurt/Rhein-Main. Homepage und RSS erreichbar; jüngster sichtbarer Beitrag vom 14.06.2026. | Kein Nachweis eines laufenden täglichen Newsfeeds. Impressum verlangt für weitere Verwertung Zustimmung; personenbezogene Beiträge benötigen Einzelprüfung. |
| Untergrund-Blättle | RSS nur für Überschrift, Autor, Datum und Originalverweis | Impressum nennt UB-Redaktions-Kollektiv und kritischen Journalismus im Großraum Zürich. Offizielles RSS-Verzeichnis verlinkt `aktuelle_artikel.rss`; XML erreichbar (HTTP 200), aktuelle Beiträge vom 30.09.2026 sichtbar. | Texte laut Impressum nur bedingt frei; Fremdtexte sind ausgenommen. Keine pauschale Erlaubnis für Bilder, Audio oder Video. Politische Einordnung nicht aus dem Namen abgeleitet. |

Primärbelege:

- Freiburg: https://autonome-antifa.org/ und https://autonome-antifa.org/spip.php?page=backend
- Frankfurt: https://www.antifa-frankfurt.org/20-jahre-sind-nicht-genug/,
  https://www.antifa-frankfurt.org/impressum/ und https://www.antifa-frankfurt.org/feed/
- UB: https://www.xn--untergrund-blttle-2qb.ch/impressum/,
  https://www.xn--untergrund-blttle-2qb.ch/rss/ und
  https://www.xn--untergrund-blttle-2qb.ch/rss/aktuelle_artikel.rss

Dies sind Quellenbeobachtungen und Selbstauskünfte, keine Bestätigung aller
Artikelbehauptungen. Rechts-/Persönlichkeitsrisiken begründen die begrenzte
Aufnahme; kein Qualitätsrang oder Verifizierungsabzeichen wird vergeben.
Korrektur- und Löschhinweise erfolgen über die auf den Originalseiten genannten
Kontakte. Bei Widerruf Quelle deaktivieren und betroffene Projektionen korrigieren.
Wien bleibt wegen ungeklärter Erreichbarkeit pending; Enough14D bleibt wegen der
zuletzt beobachteten Beiträge aus 2023 ein Archivkandidat. Vorhandene Quellen
Antifa Bern, Antifa Infoblatt, Barrikade, Montreal Antifasciste und Kontrapolis
werden nicht dupliziert.

## Technische Durchsetzung

`multilingual-source-registry.json` enthält die drei Identitäten additiv.
Nur UB hat Status `approved` und RSS-Adapter, zusätzlich `importMode: metadata-only`.
Die beiden Verzeichniseinträge zählen nicht als aktive Feeds. Die Aufnahme enthält
keinen Fremdvolltext und keine neuen Bilder, Audios oder Videos.

Der tatsächliche Aggregatorzweig verarbeitet eingeschränkte Quellen vor jeder
Body-/Bildextraktion und vor dem Seitenscraping. Er erzeugt ausschließlich einen
selbst formulierten WRN-Hinweis zum Original. Feed-Volltexte, Zusammenfassungen,
Enclosures und Bilder gelangen nicht ins Nachrichtenarchiv. Fremde Domains,
HTTP-Links und URLs mit Zugangsdaten werden abgewiesen. Erneute Verarbeitung
bereinigt auch ein schon vorhandenes eingeschränktes Linkobjekt.

Der additive Merge erhält vorhandene Feed-Identitäten; ein Feedwechsel benötigt
die ausdrückliche Registry-Aktion `replace_feed`. Die App erhält eine eigene
Schema-3-Projektion; ihre Legacy-Aggregation wird dadurch nicht aktiviert.

## Veröffentlichung

Dieses Paket ist lokal. Kein schreibender Workflow wurde gestartet, kein Feed
nach main veröffentlicht und kein Artikel redaktionell bestätigt. Veröffentlichung
über den normalen Daten-PR mit Qualitätsgate, anschließend Update News.
