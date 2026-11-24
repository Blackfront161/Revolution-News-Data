# WRN-Social-Media-Pilot vom 25. November 2026

## Vorschau ausführen

Die Vorschau liegt in einer eigenen E:-Arbeitskopie des öffentlichen Data-Repositories auf Basis von `6532fe1`. `WRN Social Media Preview` läuft zur Prüfung des Social-Media-Änderungsvorschlags und steht nach dessen Übernahme auch manuell zur Verfügung. Der Job Summary zeigt die Entwürfe mit ihren Prüfcodes. Auf einem Standardrunner im öffentlichen Repository benötigt der Job nur `contents: read`. [GitHub Actions](https://github.com/Blackfront161/Revolution-News-Data/actions) · [Manuelle Workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow) · [Standardrunner](https://docs.github.com/en/billing/concepts/product-billing/github-actions#included-compute-usage-and-storage)

Mit Node.js 24 aus der Arbeitskopie ausführen.

```powershell
node scripts/social-preview/preview.mjs
node scripts/social-preview/preview.mjs --feed live --check-links
npm ci --ignore-scripts --no-audit --no-fund --prefix scripts/social-preview
node --test 'scripts/social-preview/*.test.mjs'
```

`snapshot` verwendet die drei gespeicherten Metadatensätze aus dem Feed. `live` liest den öffentlichen Feed und bricht bei einem fehlenden oder mehrdeutigen Treffer ab. `--feed <Datei>` nimmt einen lokalen Feed. Die Redaktion kann mit `--selection <Datei>` eine eigene Auswahl von bis zu drei Original-URLs samt kurzen englischen Texten und optional einer von ihr geprüften Sprachfassung testen. Englische und zusätzliche lokale Fassung stehen im selben Beitrag. Der Feed liefert Quellenname und Datum. Texte und Anhänge der Originale bleiben außerhalb des Posts. [Öffentlicher WRN-Feed](https://blackfront161.github.io/Revolution-News-Data/news-feed.json)

`--check-links` bestätigt die WRN-Domain und den Seiteninhalt per HTTP. Für eine spezifische Artikelseite, einen Kalender- oder Atlas-Eintrag kann die Redaktion `target.url` und einen eindeutigen `target.marker` hinterlegen. Ein Umweg auf eine allgemeine Seite oder eine Antwort ohne den erwarteten Inhalt führt auf die geprüfte Startseite. Ziele, deren relevanter Inhalt erst im Browser rendert, brauchen eine separate redaktionelle Navigationsprüfung. Für die drei ausgewählten Meldungen ließ sich kein direkt öffnender WRN-Artikelleser bestätigen. Deshalb trägt jeder Entwurf den getesteten Startseiten-Link.

## Entwürfe für Mastodon und Bluesky

**Basta** · Mastodon 287/500 · Bluesky 288/300

> Basta maps 25 November demonstrations and events across France against violence targeting women and gender minorities.
>
> Basta recense les mobilisations du 25 novembre en France contre les violences visant les femmes et les minorités de genre.
>
> Source: Basta (FR)
>
> https://solinaridao.com/

[Original von Basta](https://basta.media/25-novembre-carte-des-mobilisations-contre-violences-faites-aux-femmes)

**WoMin** · Mastodon 219/500 · Bluesky 220/300

> In Memirlosho, Kenya, women are pooling savings and organising together to support their households and community. WoMin reports on how their savings groups work.
>
> Source: WoMin African Alliance
>
> https://solinaridao.com/

[Original von WoMin](https://womin.africa/practising-solidarity-economy-womens-collective-action-and-community-finance-in-memirlosho/)

**Freedom News** · Mastodon 198/500 · Bluesky 199/300

> Freedom News reports that a court halted sanctions against Autistici/Inventati, an Italian collective that provides independent digital infrastructure.
>
> Source: Freedom News
>
> https://solinaridao.com/

[Original von Freedom News](https://freedompress.org.uk/2026/11/24/court-halts-sanctions-against-autistici-inventati/)

## Geschützter Versand als manueller Pilot

Der Probelauf überprüft beide offiziellen Schnittstellen mit simulierten Antworten. `WRN Social Media Publish` ist für manuelle Einzelversendungen von `main` eingerichtet. Die bestehende GitHub-Pages-Konfiguration veröffentlicht den Feed von `main`, deshalb bleibt die Übernahme des Änderungsvorschlags ein eigener Schritt. Der Versandweg arbeitet nach der Übernahme wie folgt.

1. `WRN Social Media Preview` auf `main` mit `feed=live` starten. Einen passenden Entwurf und seinen Prüfcode aus dem Job Summary übernehmen. Sind Einträge aus dem aktuellen Feed gerollt, die Auswahl in `selection.json` redaktionell aktualisieren und neu prüfen.
2. Auf `WRN Social Media Publish` genau eine Plattform, die Entwurfsnummer und den Prüfcode wählen. Der erste Job prüft Text und Ziel gegen den aktuellen Feed und zeigt den Text im Job Summary. `Blackfront161` prüft diesen Job Summary und gibt den wartenden Versandjob manuell über **Review deployments** frei. Der Versandjob prüft den Code und Link erneut. Eine Inhalts- oder Linkänderung führt zu einem Abbruch vor dem Senden.
3. Nach dem Lauf den Zustellstatus im Job Summary und den Beitrag im gewählten Profil prüfen. Ein unklarer Zustellstatus bleibt dauerhaft reserviert.

**Geschützte Einstellungen.** `wrn-social-production` ist auf `main` beschränkt und verlangt die Freigabe durch `Blackfront161`. Der automatische Administrator-Bypass ist deaktiviert. Für die Zustellablage auf dem eigenen, gegen Löschen und Force-Push geschützten Zweig `wrn-social-delivery` erhält allein der Versandjob `contents: write` über `GITHUB_TOKEN`. Die Ablage enthält ausschließlich Zustellstatus und öffentliche Beitrags-IDs. [Environment](https://github.com/Blackfront161/Revolution-News-Data/settings/environments) · [Zustellzweig](https://github.com/Blackfront161/Revolution-News-Data/tree/wrn-social-delivery)

- **Mastodon.** Einen eigenen Benutzer-Token mit `write:statuses` und `profile` direkt bei Mastodon erstellen und in `wrn-social-production` als `WRN_MASTODON_TOKEN` eingeben. Der Job prüft Konto-ID `117672173722272702`, Profil `BlackfrontWRN` und das aktuelle Zeichenlimit. [Mastodon-Anwendungen](https://mastodon.social/settings/applications) · [Mastodon-Scopes](https://docs.joinmastodon.org/api/oauth-scopes/)
- **Bluesky.** Kurz vor dem Versand in dieser Arbeitskopie `npm ci --ignore-scripts --no-audit --no-fund --prefix scripts/social-preview` und danach `node scripts/social-preview/authorize-bluesky.mjs` ausführen. Den angezeigten Autorisierungslink im eigenen Browser öffnen und bei Bluesky für `wrnblackfront.bsky.social` die Berechtigung `atproto repo:app.bsky.feed.post?action=create` bestätigen. Das Hilfsskript überträgt die Sitzung direkt in das GitHub-Environment-Secret `WRN_BLUESKY_OAUTH_SESSION`. Sitzungsdaten bleiben im Speicher und im geschützten Secret. Kurzlebige Pilot-Sitzungen bei Ablauf erneut autorisieren. Eine dauerhafte Sitzung mit Speicherung rotierender Tokens ist für einen späteren geplanten Versand separat einzurichten. [Offizielles OAuth-SDK](https://atproto.com/guides/oauth-cli-tutorial) · [Granulare Schreibrechte](https://atproto.com/specs/permission#repo)

Die Zustelllogik reserviert jede kanonische Original-URL je Plattform dauerhaft vor dem Senden. Ein erfolgreicher Versand wird mit der Beitrags-ID bestätigt. Bei unklarem Ergebnis bleibt die Reservierung `pending` auch nach einem Neustart erhalten. Vor jeder manuellen Korrektur das jeweilige öffentliche Konto gegen den freigegebenen Text prüfen. Mastodons Idempotenzschlüssel für die Anfrage gilt laut API nur bis zu einer Stunde. Bluesky erhält einen stabilen AT-Protocol-Record-Key. [Mastodon-Idempotenz](https://docs.joinmastodon.org/methods/statuses/#create) · [AT-Protocol-Record-Keys](https://atproto.com/specs/record-key)

## Reddit-Pilot

**Ziel für einen manuellen Textbeitrag ist r/laborhistory.** Die veröffentlichte Regelübersicht verlangt historische Themen und untersagt nicht genehmigte Eigenwerbung. Der Entwurf enthält die WRN-Zugehörigkeit und verzichtet auf einen Projektlink. r/AskHistory und r/solotravel schließen KI-generierte Beiträge aus, r/travel setzt ein striktes Eigenwerbeverbot durch. Der direkte anonyme Reddit-Abruf lieferte HTTP 403. Für die Prüfung war die öffentlich indexierte Regelfassung von Reddit zugänglich. Die Regeln unmittelbar vor dem manuellen Posten im eigenen Reddit-Konto gegenlesen. [r/laborhistory](https://www.reddit.com/r/laborhistory/) · [r/AskHistory](https://www.reddit.com/r/AskHistory/) · [r/solotravel](https://www.reddit.com/r/solotravel/wiki/completerules/) · [r/travel-Moderatorteam](https://www.reddit.com/r/travel/comments/1w484mz/removed/)

Die Atlas-Reise „Arbeitszeit und politische Gleichberechtigung“ enthält die Stationen Melbourne 1856 und Neuseeland 1893. Der öffentliche Atlas-Datensatz bestätigt beide Stationen. Die historischen Eckdaten stützen das National Museum of Australia und NZ History. [Veröffentlichte Atlas-Reisen](https://solinaridao.com/atlas-edition/web-932-environment-ad596a1c/data/routes.json) · [Achtstundentag in Melbourne](https://www.nma.gov.au/defining-moments/resources/eight-hour-day) · [Wahlrecht in Neuseeland](https://nzhistory.govt.nz/politics/womens-suffrage)

**What gave Melbourne’s eight-hour campaign its leverage in 1856?**

> I’m part of World Revolution News. This question came up while working on a historical atlas route about working time and voting rights.
>
> In 1856, Melbourne stonemasons walked off the job and won an eight-hour day. The route also looks at New Zealand in 1893, where years of petitioning preceded women winning the right to vote in parliamentary elections. I’m curious about the leverage each campaign had. How much did Melbourne’s building boom and the stonemasons’ bargaining position matter, and how quickly did the gains reach workers outside that trade? If you’ve studied either campaign, what source helped you understand who was able to organise and who was left out?
