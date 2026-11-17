# WRN structured calendar contract v2 — R4 · 2026-11-17

Private review candidate. No publication or scheduled run is implied.

## Routes and eligibility

All four routes are JSON arrays of verified schema-v2 rows. events.json and events-feed.json are legacy scheduled-only projections, excluding all cancelled/deleted rows. events-v2.json and events-v2-feed.json are the full v2 routes with retained dated tombstones. The v2 feed carries up to 2000 scheduled rows plus all retained tombstones; its archive carries all eligible rows. calendar-status.json describes the configured 120-day window, source results, full-v2 counts and revision, with separate legacy counts and route declarations. Consumers using v2 must not fall back remotely to legacy routes after a v2 failure. Local snapshot filenames may retain legacy names only when bound to exact v2 bytes.

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

Explicit and inferred tombstones are retained in BOTH v2 routes (never in legacy projections) for at least 30 days and through the original scheduled occurrence date plus 30 days. Disappearance becomes deleted, not an assertion of cancellation, only after a complete successful source snapshot; eventRemovalReason records the reason. Network errors, repeated/truncated pages, the page cap and any parser rejection make that source partial and forbid absence-based deletions. A failed source keeps its last verified rows and original eventCheckedAt. All-source failure publishes no new generation; a pending transaction is recovered first.

## Dates and series

Timed eventStart/eventEnd are explicit RFC3339 instants, normalized UTC. Unknown end remains empty. pubDate is actual publisher publication time if available, otherwise empty; it is NEVER an event-start fallback. No invented noon, midnight or time zone.

eventAllDay:true uses civil eventStartDate/startDate/eventDate and optional EXCLUSIVE eventEndDate/endDate in YYYY-MM-DD. eventStart repeats the date-only value for old adapters. eventTimePrecision is date or datetime. eventTimezone/timeZone is provided only when known, with eventTimezoneInferred if inferred from a separately verified venue. Civil-day eligibility uses the known zone; unknown zones are not silently treated as UTC midnight.

Only explicit concrete occurrences are imported. Clients never expand RRULEs. Gancio pagination requests actual child occurrences from the official upcoming API. Ambiguous ranges longer than seven days are quarantined pending review, not certified as continuously ongoing exhibitions. Radar rule-only series and multi-date arrays without stable per-date native IDs are quarantined rather than keyed by array position.

IKUWO starts are taken from the organiser's machine-readable time datetime attributes; unknown machine-readable ends remain empty. Zinn sessions use canonical individual panel paths and eventParentEvent; the current organiser homepage date must match the panel-page year. These are sessions within ONE fair, not separate fairs. The America/Los_Angeles zone is explicitly marked inferred from the verified San Francisco venue.

## Workflow boundary

Proposed dedicated hourly schedule: minute 23 UTC. The job checks out current main when it starts and shares wrn-main-write serialization. Full news refresh calls the same calendar updater with failure isolation; fast news preserves calendar bytes. The news checkpoint no longer loads or overwrites events and never interprets calendar RSS publication dates.

Only calendar outputs and the events/calendarV2 sections of feed-status.json change. events describes legacy projection counts/bytes; calendarV2 describes the full v2 routes. Existing news timestamps/revisions are preserved. New source response hashes and URLs are logged in calendar-status.json. No paid service, secret, additional artifact storage or TLS/bot workaround is introduced.

Independent review is still required. Private original-response probes and replay tests are not proof of an active scheduled GitHub run or live publication. The public feed still held five old rows at the recorded 16 November check.



## Transactional publication and current-batch validation

Replay and live parser rejection have identical completeness rules: any rejected row makes the source partial and forbids absence-based deletion.

Publisher validation includes tombstones from BOTH the previous published snapshot and the current incoming batch. A newly observed stale active alias cannot override a new cancellation merely because its local capture revision is later. A strictly later publisher-confirmed active update may reinstate; if necessary the pipeline emits a strictly later material revision and persists it in the source cache before consumer deduplication.

Outputs are one recoverable generation of eight files: calendar-source-cache.json, events-v2.json, events-v2-feed.json, events.json, events-feed.json, calendar-status.json, feed-status.json when present, and calendar-generation.json. Prior state is read from events-v2.json first; legacy is only an initial migration input. A durable backup and .calendar-transaction.json journal are written before any production-file replacement. Ordinary write errors restore exact prior bytes; an interrupted process leaves the journal for recovery before further publication. calendar-generation.json is written last and binds hashes of the four calendar data/status/cache files. Consumers need not fetch this pipeline publication certificate.

The full news workflow immediately invokes --recover-only after the calendar step, before rebuilding news status. BOTH commit paths invoke --verify-generation before staging any files. Pending journals, mixed hashes and mismatched status revision/counts block publication even if event counts are unchanged. A recoverable calendar failure therefore preserves the old calendar and lets news continue. If recovery itself cannot restore/verify files, the gate fails closed; no claim is made that news can safely commit through an unrecoverable filesystem failure.

Journal/backup files are never staged. Crash tests include per-file ordinary exceptions, BaseException simulation and actual child-process os._exit termination with recovery in a separate process. These prove tested process-interruption paths, not power-loss or hardware durability.


Distinct native IDs within a single publisher are not merged merely because title, start and place match. The exact-place heuristic is cross-publisher only; an explicit canonical origin or the same occurrence ID can still prove identity. Replacing/removing one native ID must not cancel a different native occurrence merely through shared display fields.

A valid batch that cancels/removes the last active event is published with zero active rows and its retained tombstones. Last-good retention for partial sources and the all-source-failure abort provide the failure safeguard; zero active rows alone is not treated as a failure.

The generation certificate also binds the calendar-specific feed-status fields (revision, counts, bytes, source state and last successful fetch), while allowing unrelated news metadata to advance.


## Shared material-revision precision

All new/changed material revisions use UTC with exactly three fractional digits (whole milliseconds). Candidate and prior local material timestamps are compared at millisecond resolution. A semantic change uses next = max(candidate_ms, prior_ms + 1). The same rule applies to local tombstones and publisher-validated alias-group cancellation/reactivation. An unchanged already-normalized recheck preserves identical material bytes. Legacy microsecond material values are compared at the same millisecond resolution JavaScript Date.parse uses, so an apparent sub-millisecond difference never reverses a cancellation.

Publisher eventUpdated/updatedAt values are NOT rewritten to manufacture millisecond precision. Actual publisher precision remains intact. Publisher validation and local material sequencing are separate: a later verified publisher update receives a strictly later JS-comparable local material revision. Publisher-only consumer fallback comparisons use JavaScript-compatible resolution and cancellation wins unresolved ties.

When alias validation confirms a cancellation over a merely later-captured stale active copy, its winning material revision must also be strictly later in the alias group. Winning revisions and verified aliases persist in the source cache so unchanged rescans neither regress nor keep bumping revisions.

The dedicated workflow also triggers on main pushes touching update_calendar.py, calendar-sources.json or its own workflow file. None of the eight generated output paths matches these filters; its data self-commits do not trigger another calendar run. The hourly minute-23 schedule remains.

## Old-client and offline limits

Versioned routes prevent fresh legacy consumers from receiving tombstones as upcoming events. Server projections cannot evict existing offline event caches or already saved reminders in old clients. The actual old reminder function still emits a saved reminder in the synthetic probe. No offline eviction, native/device, live/publication or blanket old-client safety claim follows from this repair. A zero-active generation remains valid: legacy routes become empty while v2 retains dated tombstones.
