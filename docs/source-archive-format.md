# Private v1 compatibility bridge: delivery and retention

**Not activated. This is a temporary transition candidate, not the final reader-first
archive rollout.** Production still requires a reviewed seed, a fresh successful
non-publishing aggregation, quota/recovery readiness, a stable main/workflow window,
and the client checks listed below. Do not replace the published data with the test
fixtures. The permanent upgraded-reader release gates remain in force.

## Unchanged contracts and bounds

The manifest remains schema version 1, with one source entry per source and a
30-day window measured against build time. Every source package and individual
article response remains a v1 JSON array and at most 4 MiB (4,194,304 bytes).
`news.json` remains bounded to 2,000 articles and `news-feed.json` to 500 articles.
No source admission, completeness, identity or withdrawal check is relaxed.
The seven previously reviewed HTTP identities still require their exact source,
stored title hash and timezone-aware publication instant before HTTPS mapping;
this does not authorize other URLs or sources.

## Capture before bounded retention

`news_archive_capture.py` merges the current classified news into
`news-archive-capture.json` **before** the aggregator discards incomplete rows or
applies the 2,000-row cap. The next aggregation loads this capture first. A row
leaving the bounded index therefore does not lose its original complete body.
The capture is not a consumer endpoint contract and internal history fields are
never copied into quick/source/bounded consumer rows.

Capture is strict, bounded JSON: 64 MiB, 30,000 rows, at most 128 prior full
revisions per identity, no duplicate JSON keys/NaN, no guessed identities or
implicit missing-file bootstrap. New complete revisions retain the previous
complete revision internally; incompatible partial revisions fail explicitly.
Metadata-only rules erase body/history, and withdrawals retain a bounded tombstone
instead of permitting a body to be resurrected. Unknown policy is an error.

An initial capture must be explicitly seeded from the union of all validated
current source archives and bounded canonical news, under current policy, in an
isolated copy. A news-only seed is insufficient: an old complete archive article
that re-enters RSS would otherwise be mistaken for a new incomplete record. This does not recover text absent from both current canonical
news and previous archives. The separately prepared historical restorations are
not silently included or activated by this bridge. A read-only coverage gate
before fetching and again before output writes checks that every still-admitted
previous full body is represented in Capture, or by a valid current complete
revision with exact prior-history provenance/digest, or an explicit restriction.
A news-only seed or full-to-partial re-entry fails before output changes.

## Oversize sources, existing inline texts protected

An under-limit source keeps its existing inline full-body package. If a source
would overflow, its active index uses a distinct `-bridge-v1` source ID, avoiding
overwrite of an older full-list cache identity. **Every already published inline
complete body remains inline in the new active index**, subject only to a real
current revision, expiry or authoritative restriction. New or previously excerpted
complete bodies may be separated into immutable one-article arrays:

```
news-archive/bridge-detail-<sha256>.json
```

The digest covers exact compact UTF-8 JSON plus final LF. An index card has
`contentComplete: false`, `webFeedTruncated: true`, the original cleaned text
length, a matching `detailPath`, and an absolute `detailUrl` on the existing
GitHub Pages data origin. There is deliberately **no `detailRevision`**: legacy
readers must take their v1 array path, not the newer v2 path. No `details/`
subdirectory is produced. Quick-feed cards intentionally carry only `detailPath`,
not a forced absolute URL, so both current readers choose the successful feed
mirror. Source-index cards require the absolute compatibility URL.

The previous source URL is retained as a hash-bound compatibility package for
its already-known article identities. Previously delivered full texts stay full;
previous excerpts are not inflated into a newly oversized compatibility file.
Both active and compatibility packages reflect current policy, withdrawals and
expiry. If protected inline bodies plus new cards no longer fit, the build stops;
it does not externalize those protected bodies, remove articles or raise limits.
This is a bounded transition, not a guarantee of unlimited legacy-client growth.

## Strict reconstruction and publication

Previous indexes, details and compatibility packages are validated before writes.
Detail hash, link, title, source, publication date, length, excerpt and absolute
URL must match. Source-ID collisions, conflicting URL identities, unexpected files,
symlinks, missing/corrupt details and incompatible v2 directories fail closed.
Restrictions on current capture rows and previous indexes propagate to every
output in the same generation, including the actual `news.json` fallback file.

`--verify-only` reconstructs and checks exact capture, manifest, source/detail,
compatibility, quick-feed and bounded-news bytes plus status bindings, without
writing. `--verify-only --require-fresh` additionally requires a real successful
recent aggregation: matching run/fetch time, ordered non-future publication times,
and age under one hour. Rebuilding a stale snapshot cannot make it publishable.
Local multi-file writes are not filesystem-transactional; the complete validated
set must be committed/published together.

Both news workflows pin current main when their job actually starts. The bridge
push helper requires a clean tree and exactly one allowlisted data commit directly
on that pinned base. It revalidates, then uses an exact explicit
`--force-with-lease=refs/heads/main:<base>` as a server-side compare-and-swap only
**after proving that this update is fast-forward**. There is no rebase, unrestricted
force, output recomputation from stale input, or automatic retry. An uncertain
push is read back before deciding whether it happened. Old queued/running workflows
must be drained before activation; they cannot be retroactively protected.

## Legacy client results and honest limitations

Exact Code41 function probes demonstrate v1 detail arrays online, correct quick-feed
mirror rebasing, current bounded-news fallback, and metadata-only refusal. Existing
inline source texts remain readable from a mirror-loaded or cached source index
without a new detail request. These are function/data-contract tests, **not a full
real-browser or native-release acceptance**.

For a newly externalized body, the old source-view reader uses the absolute Pages
URL and cannot switch that detail request to Raw. If Pages is down and the article
has already left `news.json`, its excerpt/original link remains but full-body
hydration fails. The quick-feed reader can rebase the same detail path to Raw.
Legacy detail caching is not proven durable across a cold offline restart; a new
sidecar body may need a network fetch again. A data-only field cannot add those
missing fallback/cache behaviors to the old executable. No existing inline full
text is deliberately degraded to create this trade-off.

The complete original Code41 UI asset set is unavailable in the cloud copy. A
real browser source/quick navigation, upgrade/cold-offline test and current Website
consumer check still need the actual application bundle or Ailyeen. No emulator,
ADB/device operation, signing, app release or public activation is part of these
private tests. Permanent reader rollout remains the durable solution.

## Recovery artifact and quota gate

Both prepared workflows validate and hash-bind the exact post-aggregation capture
and current source policy to their checked-out base, triggering workflow SHA,
run, attempt, job and aggregation outcome. Only failed aggregation/build/verification/push runs attempt the bounded
recovery-only upload at the end; an artifact ID and digest are required to claim
recovery succeeded. Recovery never turns a failed job into successful publication.
Successful data commits already retain capture, so successful runs upload no
extra artifact. A post-commit failure accepts only the same strict single allowed
data commit directly on the pinned base, with byte-exact Capture/Policy binding.

The recovery artifact has seven-day retention and is never automatically restored.
A failed aggregate can produce a valid partial checkpoint; the receipt makes no
freshness claim. A policy-nonconforming checkpoint is not uploaded, not silently
sanitized. Runner loss/cancellation and artifact quota remain best-effort failure
boundaries; the artifact cannot guarantee rescue after a runner is already gone.
No upload or storage allocation has occurred during this review. Available Actions
storage and expected recurring volume must be checked before activation; an upload
failure must not be bypassed to restart publication.

## Two observed producer re-entry defects

The fresh private run also found two bounded producer issues. One exact metadata-only
Perspektive Online URL/source/date/title variant gained U+00AD in a word. Only that
verified variant maps to its already-stored title; all other identities stay strict.
Two configured Libcom source names share exactly the same feed URL. An existing
article owned by one is no longer relabeled by the duplicate delivery through the
other: the incoming duplicate is skipped and counted, without changing the stored
row or admitting another body. Different feeds, missing/ambiguous configurations
and unrelated sources do not qualify. No publisher-wide alias or rights expansion
is introduced.
