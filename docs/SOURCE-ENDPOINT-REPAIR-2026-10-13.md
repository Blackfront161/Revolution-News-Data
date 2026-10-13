# Quellenreparatur, 13. Oktober 2026

Die gepflegten RSS-Adressen von Antifa.cz, Pramen, Wildcat und den polnischen,
türkischen und italienischen anarchistischen Bibliotheken sind korrigiert.
Alle sechs lieferten XML und zugelassene Metadaten; beide Antifa-Themenbereiche
nutzen dieselbe Konfiguration. Artikelkörper und Medien bleiben ausgeschlossen.
AGORA verwendet die bestätigte Betreiberhomepage www.agora.at.

Der echte, auf diese Quellen beschränkte schnelle Aggregator lief am
2026-10-13 02:41 UTC: 83 neue, 17 aktualisierte Metadateneinträge, sieben
Feedkonfigurationen mit Einträgen, null Eintragsfehler. Diese lokale Importprobe
ist kein Beleg für die Veröffentlichung aller Einträge im aktuellen Newsfeed.

Der technische Checker bestätigte anschließend alle sechs mit HTTP 200/ok.
Wildcat hatte zwischenzeitlich eine Zeitüberschreitung, die zweite Prüfung war
erfolgreich. Antifa.cz leitet den exakten HTTPS-Feed nach antifa-cz.net/feed.xml
weiter; die veröffentlichte Originaladresse und die Artikelverweise belegen
diesen Betreiberweg. Nur dieses exakte Adresspaar ist zugelassen. Andere
Domains, Pfade, Ports, HTTP oder Queryvarianten bleiben gesperrt. TLS bleibt aktiv.
Die Prüftimestamps aller unbetroffenen Quellen bleiben unverändert.

Fehler einer ausgemusterten Adresse sperren ihre geprüfte Ersatzadresse im
Schnelllauf nicht mehr. Metadatenquellen werden auch vom späteren Archiv-
Seitenabruf ausgeschlossen. Explizite Ports bleiben in Vergleichsschlüsseln.

Beide Nachrichtenworkflows erzeugen und veröffentlichen künftig auch das
Quellenregister. Zuvor wurde es im Quality Gate nur lokal erzeugt: korrigierte
Eingaben konnten deshalb weiterhin mit alten veröffentlichten Adressen erscheinen.

30 betroffene Import-, Recovery-, Aktivierungs- und Workflowtests sowie der
Appvalidator bestanden lokal. Die Pull-Request-Checks prüfen den tatsächlichen
veröffentlichten Änderungssatz zusätzlich. Noch gestörte andere Quellen erhalten
keine pauschale Freigabe; Metadatenrechte und Betreiberfehler sind getrennt.
