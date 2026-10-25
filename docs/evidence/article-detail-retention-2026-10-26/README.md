# Full source details survive quick-feed rollover

Base: `24f34c0224ccdeee3683b813850325142db41c3f`.

PR56 retained a full source body only while its article remained selected in the
500-row quick feed. A subsequent ordinary build shortened the same article to
1,400 characters after it left that selection, although current `news.json`
still contained the original complete body. The two reported Infolibre articles
therefore fell from 12,330 and 36,419 characters to 1,400 each.

The builder now also retains a previously complete source-detail row when its
nonempty source name, title and HTTPS URL and its complete body exactly match
the current canonical article. Metadata-only, incomplete or truncated rows
cannot authorize retention. Newly restricted source policies still apply first.
Historical-only rows without a current canonical body retain the existing excerpt
behavior; the 30-day expiry also remains in force. This is delivery continuity,
not a new publisher rights admission or permission to republish on the website.

A source JSON package is limited to 4 MiB including UTF-8 encoding, separators and
the final LF. Exceeding this limit fails the build before archive files are
written; it never silently shortens a previously delivered body to fit.

## Restoring already regressed data

The accepted PR56 merge `cd3ed1f61cdbf960b876bc0cbd865ca28aa29444` supplies
the historical complete delivery evidence. Only rows whose identity and body
exactly match a current complete canonical article were used to seed the build.
No excerpt was inferred or promoted to a full text. Current source policies and
the current archive reference timestamp/coverage were retained.

`retention-build-proof.json` records the result: 46 previously delivered full
bodies restored in 21 source packages, including the two reported Greek texts.
All restored bodies have recorded SHA256 values. Existing quick-feed rows,
routes, archive manifest, current `news.json`, source policies and status files
remain unchanged. The largest resulting source package is 1,681,188 bytes.

The restored JSON files were read back as previous-build inputs and built again
with an empty quick selection: all 523 current complete rows, including small
complete articles, stayed identical. Separately the regression suite invokes
the actual CLI main twice with serialized inputs and outputs, removing the
article from the quick feed between calls.

Validation: 17 tests passed across `test_article_source_details.py`,
`test_source_import_policy.py` and `test_source_archive.py`. Tests also cover
changed identity/body, invalid URLs, incomplete previous data, new source
restrictions, 30-day expiry, and the exact UTF-8 package capacity boundary.

No App code, AAB, website pointer, rights policy, emulator or device operation
is part of this change. Independent review and post-publication checks remain
required before describing this candidate as live.
