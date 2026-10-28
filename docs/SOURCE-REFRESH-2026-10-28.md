# Source refresh, 28 October 2026

Review patch for Blackfront161/Revolution-News-Data, pinned main commit `342466da17fa6213e1abf83cb8328c1d0ceb1f61` (observed 2026-10-28T12:32:50Z). Not published by this preparation.

Ten approved, additive source profiles have public RSS feeds which returned HTTP 200 and parsed items on 28 October 2026. Admission retains only public headline/date/author/original HTTPS link. No new full-text, translation, image or media permission is granted by this configuration. Existing source identities and endpoint aliases remain intact. The existing metadataTopicOverrides field is preserved both in the generated block and its generator; the Karapatan /5561/ title-bound Anti-Rep & Prisons override remains effective after additive enrichment. Haïti Liberté is a mixed-language feed; `und` avoids assigning an unverified language to every article.

| Added publisher | Feed | Parsed/admitted metadata |
| --- | --- | --- |
| New Naratif | https://newnaratif.com/feed/ | 10/10 |
| Project Multatuli | https://projectmultatuli.org/feed/ | 10/10 |
| Prachatai English | https://prachataienglish.com/rss.xml | 10/10 |
| Afrique XXI | https://afriquexxi.info/?page=backend&lang=fr | 10/10 |
| Amandla! | https://www.amandla.org.za/feed/ | 10/10 |
| The Public Source | https://thepublicsource.org/feed | 50/50 |
| Daraj | https://daraj.media/feed/ | 10/10 |
| Haïti Liberté | https://haitiliberte.com/feed/ | 10/10 |
| Pikara Magazine | https://www.pikaramagazine.com/feed/ | 10/10 |
| La tinta | https://latinta.com.ar/feed/ | 10/10 |

Ill Will gains the publisher-discovered `https://illwill.com/feed.xml` transport (200, 16 parsed items). Radical Socialist gains `https://radicalsocialist.in/feed/` (200, 10 items), advertised by its current site. Only its exact old `index.php?format=feed&type=rss` configuration key is mapped. Other query strings, credentials, fragments and nonstandard ports remain unmatched. The old stable source URL is preserved. The returned Radical Socialist articles include older material (2025); their original publication dates remain unchanged. Its former hosting suspension is no longer the observed result.

The following replacements already exist on main and were reverified; they are not new changes: Lausan (10 items), Perspektive Online (10), Colorlines (10), Cultural Survival (10), Ni Una Menos (9), Portuguese Anarchist Library (25), Antifa Bern (100), Feminist Anti-War Resistance (10). DeSmog's existing feed also returned 200 with 10 items. All were parsed as RSS/Atom, not inferred from homepage reachability.

Remaining provider observations, 2026-10-28 12:26–12:33 UTC:

| Source | Actual observation | Disposition |
| --- | --- | --- |
| 269 Libération Animale | Current /feed/ returns 404; homepage 200 without an advertised feed | No false homepage-to-feed substitution; publisher must expose a feed or another reviewed adapter is needed |
| Tier im Fokus | Current tierimfokus.ch homepage 200, /feed/ 404, no advertised feed | Existing old address did not establish a usable feed; current homepage is not RSS |
| IWW | Homepage and configured /feed/ 403 | Access denied; no bypass attempted |
| Asylum Magazine | Homepage and /feed/ 403 | Access denied; no bypass attempted |
| Athens Indymedia | Configured /rss/ 429 | Rate limit; retain normal backoff |
| Anarkismo | Homepage and all three configured international/Africa/gender feeds 503 | Server failure; no functional substitute confirmed |
| Endnotes | /feed.xml redirects to www and returns 500; www homepage 200, no feed advertised | Homepage does not repair feed |
| A-Infos | Configured HTTP URL redirects to HTTPS; HTTPS fails UNABLE_TO_VERIFY_LEAF_SIGNATURE | Certificate-chain verification preserved |
| Earth First! | HTTP 200 and valid RSS with zero items | Reachable empty feed, not restored article ingestion |
| Thozhilalar Koodam | Homepage and /feed/ ENOTFOUND | DNS failure from this observation location, not proof of closure |
| Noblogs | 14 existing hostnames plus Abolition Media's www spelling return ENOTFOUND | DNS failure from this observation location, not proof of closure |

The 14 Noblogs hostnames are noticiasanarquistas, abolitionmedia, actforfree, antimilitarismus, boak, fajfa, fauda, frequenza, housingaction, fantifa, kitelineradio, palanghitam, rheinmetallentwaffnen and thefinalstrawradio, all under noblogs.org. No operator has been contacted and no source has been deleted or falsely marked repaired.

Validation: nine new standard-library unittest cases pass (additive uniqueness and identity preservation, metadata-only admission/foreign-host rejection, mixed-language handling, exact alias matching, Karapatan topic-override propagation and idempotent generation). Four existing source_import_policy tests also pass, including the actual aggregator AST branch which continues before any body scrape. All 140 parsed items from the ten new feeds pass the same-publisher metadata admission policy. Full Data CI and live aggregation have not been run in this preparation. Generated sources-registry.json/news artifacts must be built by the authoritative Data workflow after review; do not manually edit them.

Website boundary: Data requestUrl aliases work in both aggregator transport branches and are preserved by build_sources_registry.py. The Website v1 importer keeps the stable url identity and does not expose a cross-origin requestUrl. Do not weaken that strict schema in this source patch. Website source navigation may offer a separately labeled reviewed homepage. Data does not publish the Website directory/home/summary/images tuple: its canonical inputs are news-feed.json, feed-status.json and sources-registry.json on GitHub Pages. At 2026-10-28T12:43:42Z all three were 200 and byte-identical to this pinned commit (500 news, 462 sources; feed generated 08:20:18Z). wrn-website-content/current.json was 404 on Pages and immutable raw; the tree contains no such tuple. Website preparation must use its existing commit/hash-bound projection and publisher contract.
