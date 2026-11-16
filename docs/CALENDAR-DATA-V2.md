# WRN structured calendar contract v2 — 2026-11-16

Private review candidate. No publication or scheduled run is implied.

## Routes and eligibility

events.json and events-feed.json remain JSON arrays. calendar-status.json describes the configured 120-day window, source results and a content revision. Both routes contain only verified v2 rows. The feed carries up to 2000 scheduled rows plus all retained tombstones; the archive carries all eligible rows.

Upcoming eligibility requires eventSchemaVersion === 2 and eventTimeVerified === true. Cached v1/RSS rows with publication-date guesses or ambiguous series ranges must be quarantined as historical/unverified, not unioned into verified upcoming events. calendar-status declares minimumEventSchemaVersion:2, legacyUpcomingPolicy:quarantine-v1 and authoritativeCompleteSnapshot:false. Overall absence is NEVER a consumer deletion signal.

calendar-source-cache.json is a pipeline-only per-source history before federation deduplication. Consumers must not load it as another event feed.

## Identity

eventOccurrenceId is the primary stable identity: source registry id + native occurrence id. It does not include mutable start time or title. eventUuid and eventApiId repeat that namespaced identity for older adapters. eventSeriesId is separate and optional. Gancio child rows have their own native IDs; parentId never generates extra dates. link is the original event page, not a calendar listing.

eventAliases lists verified occurrence identities of exact federated duplicates. Duplicate matching uses explicit canonical remote event identity or exact title + UTC start + explicit venue/address. No global title-only match. Different occurrences sharing a link remain distinct. No invented equivalence between old v1 UUIDs and new real series occurrences; migration uses explicit schema quarantine instead.

## Material revisions and status

eventStatus is scheduled, cancelled or deleted, with matching cancelled/deleted booleans. eventStatusInferred is true if scheduled is merely implied by an upcoming listing. Unknown/unsupported states are quarantined; postponed is not falsely labelled cancelled.

eventUpdated / updatedAt are actual publisher modification timestamps, otherwise empty. eventCheckedAt is a successful retrieval timestamp. eventRecordUpdatedAt is a LOCAL MATERIAL record revision: it stays unchanged when semantic event data is unchanged, including repeated cancellation checks. calendarGenerationAt is snapshot provenance, not a publisher edit.

Consumer merge order for trusted v2 rows:
1. A strictly later eventRecordUpdatedAt material revision supersedes an older row.
2. With equal or unavailable material revisions, cancellation/deletion wins over active, independent of input order.
3. Where material revisions are unavailable, compare actual publisher eventUpdated/updatedAt if both are known. Tied/unknown revisions favour cancellation/deletion.
4. eventCheckedAt alone NEVER reinstates a cancelled/deleted row.

Pipeline validation before emitting a new active material revision:
- Explicit cancellation/deletion needs a strictly later publisher modification to reinstate.
- An internal missing-from-complete-upcoming-snapshot tombstone may be withdrawn after that SAME native occurrence genuinely reappears in a later successful snapshot; eventReinstatedFromSnapshot marks this distinct case.
- An unchanged recheck never bumps eventRecordUpdatedAt. Per-source histories preserve suppressed federation aliases across deduplication.

Explicit and inferred tombstones are retained in BOTH routes for at least 30 days and through the original scheduled occurrence date plus 30 days. Disappearance becomes deleted, not an assertion of cancellation, only after a complete successful source snapshot; eventRemovalReason records the reason. Network errors, repeated/truncated pages, the page cap and any parser rejection make that source partial and forbid absence-based deletions. A failed source keeps its last verified rows and original eventCheckedAt. All-source failure writes no published files.

## Dates and series

Timed eventStart/eventEnd are explicit RFC3339 instants, normalized UTC. Unknown end remains empty. pubDate is actual publisher publication time if available, otherwise empty; it is NEVER an event-start fallback. No invented noon, midnight or time zone.

eventAllDay:true uses civil eventStartDate/startDate/eventDate and optional EXCLUSIVE eventEndDate/endDate in YYYY-MM-DD. eventStart repeats the date-only value for old adapters. eventTimePrecision is date or datetime. eventTimezone/timeZone is provided only when known, with eventTimezoneInferred if inferred from a separately verified venue. Civil-day eligibility uses the known zone; unknown zones are not silently treated as UTC midnight.

Only explicit concrete occurrences are imported. Clients never expand RRULEs. Gancio pagination requests actual child occurrences from the official upcoming API. Ambiguous ranges longer than seven days are quarantined pending review, not certified as continuously ongoing exhibitions. Radar rule-only series and multi-date arrays without stable per-date native IDs are quarantined rather than keyed by array position.

IKUWO starts are taken from the organiser's machine-readable time datetime attributes; unknown machine-readable ends remain empty. Zinn sessions use canonical individual panel paths and eventParentEvent; the current organiser homepage date must match the panel-page year. These are sessions within ONE fair, not separate fairs. The America/Los_Angeles zone is explicitly marked inferred from the verified San Francisco venue.

## Workflow boundary

Proposed dedicated hourly schedule: minute 23 UTC. The job checks out current main when it starts and shares wrn-main-write serialization. Full news refresh calls the same calendar updater with failure isolation; fast news preserves calendar bytes. The news checkpoint no longer loads or overwrites events and never interprets calendar RSS publication dates.

Only calendar outputs and the events section of feed-status.json change. Existing news timestamps/revisions are preserved. New source response hashes and URLs are logged in calendar-status.json. No paid service, secret, additional artifact storage or TLS/bot workaround is introduced.

Independent review is still required. Private original-response probes and replay tests are not proof of an active scheduled GitHub run or live publication. The public feed still held five old rows at the recorded 16 November check.
