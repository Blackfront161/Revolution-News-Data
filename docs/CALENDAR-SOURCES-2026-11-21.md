# Calendar source expansion — 21 November 2026

This is a registry-only extension of the existing verified v2 pipeline. The63 existing source objects retain identical values and order. Add three distinct HTTPS Gancio sources; producer, parser, identity/material revisions, pagination, cancellation validation, privacy handling, deduplication and compatibility routes are unchanged. No generated datasets or test events belong in the PR.

## Verified additions

| Source | Publisher/context | Eligible observed occurrences | Primary verification |
|---|---|---:|---|
| calndr.de | Datenpunks e.V.; repair cafés, free software, digital rights and open culture |11|https://calndr.de/about |
| Bonn.jetzt | Editorially moderated regional community calendar for digital culture, science, arts and sustainability |88|https://bonn.jetzt/about |
| What's On Clonmel | Not-for-profit community guide; public culture, repair, sports and solidarity events |151|https://calendar.clonmel.town/about |

All three are listed in https://gancio.org/v2/instances . Direct machine-readable responses and publisher home/about HTML are hash-bound in the private review package. Every one of the250 eligible occurrence slugs is present in its public publisher homepage HTML. Stable native occurrence IDs are provided by the publishers; no recurrence expansion or date inference. A missing end remains unknown. Clonmel's seven ambiguous long ranges are rejected by the unchanged adapter, making its source partial and disabling absence-based removals.

## Current private verification

Fresh full66-source run from the pinned current baseline:3543 archived v2 rows =3539 scheduled +4 retained tombstones, compact v2 feed2004=2000active+4tombstones. New-source contribution250 groups after current federation dedup, all novel against baseline identity/alias sets; one additional existing-source occurrence also arrived, so the total251 increase must not be attributed wholly to these additions. Counts can change before a normal live publication. There were45ok/19partial/2failed sources. Infoates and Radar still timed out; neither was silently disabled or treated as cancellation.

All four prior deleted occurrence IDs, statuses and material revisions remain unchanged. Legacy routes contain active rows only; full v2 routes retain the four dated tombstones. The generation certificate verifies. All non-calendar feed-status fields are unchanged.

80 existing calendar regression tests PASS, including stable IDs, millisecond revisions, cancellation/reinstatement, aliases, source failures, pagination, legacy routing and recoverable publication. An initial isolated test setup lacked three unchanged dependency files; after adding those exact pinned main files the complete suite passes. No product defect or test skip is hidden by that setup error.

## Editorial/privacy scope

Candidate titles and venues were reviewed against the public listing snapshots. No identified confidential shelter/private-home or tactical deployment listing was admitted. The unchanged adapter imports no attendee/patient identities or full event descriptions, and performs no new geocoding or location inference. Publicly advertised support meetings on Clonmel use the listed public community/library venues; their public status is not a blanket guarantee that every future submission can never need editorial/privacy removal. Existing editorial/privacy rules remain applicable; this is not a new runtime privacy filter.

## Researched but not added

BlablaLinux returned a valid empty API list, so provides no current addition. CalendriGeek's current Gancio endpoint is404 while its public site now uses another event system; do not add it under the wrong adapter. Pelumpén returned43 eligible occurrences and is retained as a future regional candidate; this bounded revision prioritizes three fully reviewed publishers. Kink/adult and unrelated directory entries were not proposed.

Independent exact review and fresh main/CI comparison precede normal publication. The existing main code/config push trigger and hourly minute23UTC refresh supply future publisher updates automatically; the source list itself is not automatically expanded from the directory. Private snapshots here are not live publication proof. App/Website target trees, PR59 and devices/emulators remain untouched.
