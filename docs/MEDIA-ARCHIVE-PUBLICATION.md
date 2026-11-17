# Coupled media source-archive publication repair

The media job runs build_source_archive.py, which writes source packages, the source manifest, news-feed.json detail bindings and feed-status.json news.bytes. Its output allowlist omitted the last two files. Run44040996533 created a local media commit then correctly failed the unchanged safe-push clean-tree guard on unstaged feed-status.json; it did not publish that commit.

Calendar-v2 delivery reserialized feed-status as indented JSON. The archive builder always writes compact JSON, so an otherwise unchanged status already becomes dirty. The actual saved calendar status is1602bytes; identical values compact to1328bytes. Thus calendar delivery can expose this pre-existing incomplete output contract. No exact replay of the discarded failed runner filesystem is claimed.

The correction stages both real builder outputs together with the existing media/archive outputs. Shared wrn-main-write concurrency, latest-main checkout and wrn-safe-push.sh remain unchanged. No reset, dirty-file ignore, commit drop, body truncation or manual data patch.

A narrow pre-commit gate compares to actual Git HEAD: news.json and all calendar arrays/cache/status/certificate stay unchanged; quick-feed rows retain content, identity and order while detail routes may be rebound; feed-status values may change only at news.bytes, which must match serialized news-feed bytes. Detail routes must bind exactly one admitted complete original source body, and any existing v2 generation certificate is verified. Existing media validation remains in place.

Ten targeted tests pass. Real local Git repositories reproduce the old failure for both format-only and changed-detail cases. The corrected output list commits both and passes the actual unchanged safe-push script through fetch/rebase/push to a separate local bare remote, with all bytes preserved. Other cases reject changed body/identity, extra status changes, unsafe/incomplete details, changed calendar files and a pre-existing mixed v2 certificate; valid v2 survives. These are synthetic controlled regressions, not the original runner filesystem or a live media publication.

App/Website trees and PR59 remain untouched. Independent exact candidate review, current-main comparison and CI precede regular merge. First real media job, botcommit, protected-input/status comparison and public output readback remain required before a live PASS.
