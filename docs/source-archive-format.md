# Source archive delivery and retention

The manifest stays at schema version 1. Each `sources[].path` is still a JSON
list containing every retained card for that source. The retention window is
measured against build time, not the bounded `news.json` index or the newest
publisher timestamp.

## Bounded delivery, without shortening admitted full texts

Source lists up to 4 MiB keep their existing shape. If a list would exceed that
limit, complete long article bodies move into immutable, one-article JSON lists:

```
news-archive/details/<sha256>.json
```

Externalized sources receive a distinct manifest `source.id` and index basename
ending in `-details-v2`. The explicit `legacyId` is the previous v1 identity.
This prevents older readers from overwriting their IDB, fetch-key and URL-keyed
full-text caches with a compact index. It does not authorize substitution of an
old body as a new revision.

The digest covers the exact UTF-8 bytes of compact JSON plus the final LF. The
index card has `contentComplete: false`, `webFeedTruncated: true`, the original
cleaned text length, and matching `detailPath`, `detailRevision`, and `detailUrl`.
The absolute URL is a compatibility fallback; upgraded readers should resolve
the path against the actual archive mirror first. A successful transport alone
is not proof that the returned body matches the card.

Each index and each individual detail must remain at most 4 MiB. A single
oversized article or an oversized card-only index fails explicitly. The builder
never truncates a full text merely to meet a byte limit. Increasing the number
of normal-sized complete articles therefore no longer forces all their bodies
into one source-sized response.

## Safe rebuilding

Previously admitted complete text remains complete for the 30-day window even
when it leaves `news.json`. Current canonical records override older revisions.
Incomplete records are not promoted to complete text. This change cannot
recover content that was already absent or truncated before the repair.

Previous index files and referenced details are checked before any outputs are
changed. Detail digest, article identity, publication date, length, and excerpt
must match. Missing or corrupt details stop the build rather than silently
turning the next archive generation into excerpts. Explicit article/source
withdrawals and metadata-only policy take precedence; a technical source pause
alone does not withdraw its retained articles.

Details are written before indexes. The existing publication workflow commits
the generated set together. Details that expire or are withdrawn are removed;
a stale index must fail visibly instead of reviving content. Multi-file local
writes are not a crash-atomic filesystem transaction.

## Reader and release requirements

Deploy compatible App and Website readers before enabling this builder in the
production data workflow. Readers must verify exact revision bytes and identity,
try approved archive mirrors, and cache verified details under revision-specific
keys. Cache quota/write failures must not replace a valid downloaded response
with stale data or an empty successful JSON list. A source may return to its
v1 identity only when the entire retained list fits
with its admitted complete bodies inline again. Old v1 datasets must not be
overwritten by the new excerpt-only index cache.

Regression suite:

```
python -m pip install -r requirements-test.txt
PYTHONPATH=. python -m pytest -q tests/test_durable_source_archives.py tests/test_article_source_details.py tests/test_source_archive.py tests/test_source_import_policy.py tests/test_news_retention.py
```

Test the staged reader with real browser persistence, a cold offline restart,
corrupt/missing revision responses, and quota failure before production rollout.
