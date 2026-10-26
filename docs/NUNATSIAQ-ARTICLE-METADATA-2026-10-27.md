# Reviewed Nunatsiaq article metadata correction

Original: https://nunatsiaq.com/stories/article/new-taloyoak-high-school-unveiled-with-public-ceremony_inuk/

Checked27October2026 against DATA base `0cfa1b00868d7f7adfce95440cbbd03507862e41`. The archived row has an `A-14811.95.gif` notice/advertising asset as its lead image and `en` as its language. Its other image candidates also include advertising.

The publisher page explicitly identifies `https://cdn.nunatsiaq.com/wp-content/uploads/2026/10/Pangniq-school-1_inuk-1200x630.jpeg` as `og:image`. The captioned article photographs are the Pangniq-school1/2 images. Adsanity elements inside the article use `wp-post-image` too, so that class is not evidence of editorial relevance. The current RSS item contains Inuktitut syllabics and an Inuktitut category; the page explicitly links to a separate English version. Its site-wide HTML language is nevertheless `en`.

Original HTML SHA256: `6df4243588ca187b6dde14267713d1750f0a04883b906cbed7e67a73f414d34f`.
Publisher RSS SHA256: `b4b37cbde761e07a3aca3d7cee2947674f2369c9f992a175498c06c712de5d36`.

The existing scraper retains a supplied image and consults OpenGraph only when no image is present. Complete retained articles can also bypass page enrichment. The wrong existing image therefore does not repair itself merely because the current publisher OpenGraph value is correct. The language is assigned from the English feed profile rather than the individual article.

The correction is bound to exact publisher, HTTPS host/path and reviewed title. It sets `iu`, replaces an existing unrestricted media admission with the verified article images and leaves body, author, date, identity and policies unchanged. It does not add images to unillustrated or metadata-only/withdrawn rows. Checkpoint processing covers complete retained articles as well as new/enriched ones. A Nunatsiaq-only candidate filter excludes Adsanity containers and advertising links while allowing editorial GIFs and leaving other publishers unchanged.

Validation:29tests pass across reviewed metadata, source-detail retention, news retention, import policy and reviewed publisher aliases. The saved real publisher HTML reproduces correct OpenGraph, the English site-language trap, two editorial image candidates after filtering and unchanged body/author/date/identity. This is one article review, not a quality assessment of all266Website images. No full pipeline run, Website mutation, new media permission or publication is included.
