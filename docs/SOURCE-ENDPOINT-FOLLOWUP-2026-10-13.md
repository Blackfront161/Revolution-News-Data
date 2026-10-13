# Weitere veraltete Feeds korrigiert

Die App-Arbeitskopie enthielt vier korrigierte Adressen, die Live-Datenpipeline
noch nicht: Black Agenda Report (rss.xml), Systemli (index.xml), Stop the War
(rss.xml) und Sprout Distro (rss.xml). Die vier vorhandenen Quellen übernehmen
diese Betreiberfeeds, beschränkt auf Metadaten und HTTPS-Originalverweise.
Neue Volltext- oder Medienrechte werden nicht vergeben.

Die erneute vollständige XML-Prüfung bestätigt 10/6/100/10 Feed-Einträge und
HTTP 200 bei allen vier URLs. TLS war aktiviert, die Körper wurden nicht
gespeichert. Einzelne vorherige TLS-/Timeoutversuche scheiterten; daraus wird
keine ununterbrochene Verfügbarkeit behauptet. Der technische Checker bestätigt
alle vier Feeds mit ok/200. Der echte beschränkte Schnelllauf übernimmt 20 neue
Metadateneinträge, ohne zusätzliche Artikel- oder Medienabrufe.

Systemli verwendet relative Artikelverweise. Der Parser hatte ohne die
tatsächliche Abrufadresse keine absolute HTTPS-Basis; die Metadatenregel wies
dadurch alle sechs Verweise ab. Schnell- und Reparaturlauf geben dem RSS-Parser
jetzt die tatsächliche Response-URL als Content-Location. Die bestehende
HTTPS-/Hostregel bleibt unverändert. Der gezielte echte Systemli-Lauf übernimmt
danach sechs weitere Metadateneinträge. Der Feed deklariert die Sprache de.

31 betroffene Import-, Recovery-, Aktivierungs- und Workflowtests sowie der
Appvalidator bestehen lokal. Ein Regressionstest prüft auch, dass relative
fremde Hosts weiterhin abgelehnt werden. Die zusätzlichen Änderungen werden
erst nach den vorhandenen Pull-Request-CI-Gates aktiviert. Alte Inhalte werden
dabei nicht als neu erschienen datiert.
