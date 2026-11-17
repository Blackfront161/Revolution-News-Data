"""Bounded source capacity must preserve the legacy flat-array/full-body contract."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import pytest
import build_source_archive as builder

NOW = datetime(2026, 11, 17, 7, 11, 18, tzinfo=timezone.utc)
LIMIT = 8 * 1024 * 1024

def payload_size(rows):
    return len((json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf8"))

def full_of_size(target):
    row = dict(quelleName="Capacity source", title="Full UTF-8 article",
               link="https://example.org/capacity", pubDate=NOW.isoformat(),
               content="", contentComplete=True, language="de")
    overhead = payload_size([builder.projected_article(row, 1400, retain_body=True)])
    budget = target - overhead
    row["content"] = "界" * (budget // 3) + "x" * (budget % 3)
    assert payload_size([builder.projected_article(row, 1400, retain_body=True)]) == target
    return row

@pytest.mark.parametrize("offset", [-1, 0])
def test_actual_eight_mib_limit_preserves_exact_utf8_body_and_legacy_route(offset):
    assert builder.MAX_SOURCE_PACKAGE_BYTES == LIMIT
    full = full_of_size(LIMIT + offset)
    quick = dict(full, content=full["content"][:100] + " …", contentComplete=False,
                 webFeedTruncated=True, webFeedOriginalLength=len(full["content"]))
    manifest, chunks = builder.build_source_archives(
        [full], [quick], previous_articles=[full], generated_at=NOW)
    ident = builder.source_id(full["quelleName"])
    rows = chunks[ident]
    assert isinstance(rows, list) and len(rows) == 1
    assert payload_size(rows) == LIMIT + offset
    assert hashlib.sha256(rows[0]["content"].encode("utf8")).digest() == hashlib.sha256(full["content"].encode("utf8")).digest()
    assert rows[0]["contentComplete"] is True and not rows[0].get("webFeedTruncated")
    assert manifest["sources"][0]["path"] == "news-archive/" + ident + ".json"
    bound = builder.bind_quick_details([quick], chunks)[0]
    assert bound["detailPath"] == manifest["sources"][0]["path"]
    assert bound["content"] == quick["content"]

def test_one_utf8_byte_over_limit_still_fails_closed():
    full = full_of_size(LIMIT + 1)
    assert len(full["content"]) < LIMIT
    with pytest.raises(ValueError, match="8388608 bytes; refusing silent body truncation"):
        builder.build_source_archives([full], [], previous_articles=[full], generated_at=NOW)

def test_capacity_is_per_source_not_total_and_no_previous_body_lost():
    first = full_of_size(5 * 1024 * 1024)
    second = dict(first, quelleName="Second capacity source", link="https://example.org/second")
    manifest, chunks = builder.build_source_archives(
        [first, second], [], previous_articles=[first, second], generated_at=NOW)
    assert manifest["itemCount"] == 2 and len(chunks) == 2
    for rows in chunks.values():
        assert rows[0]["content"] == first["content"]
        assert rows[0]["contentComplete"] is True

def test_oversized_main_writes_no_manifest_chunks_or_quick_feed(tmp_path, monkeypatch):
    full = full_of_size(LIMIT + 1)
    # main's current clock determines its unchanged 30-day eligibility window.
    full["pubDate"] = datetime.now(timezone.utc).isoformat()
    news, quick, archive, manifest = (tmp_path/"news.json", tmp_path/"quick.json",
                                    tmp_path/"archive", tmp_path/"manifest.json")
    archive.mkdir()
    builder.write_payload(news, [full])
    builder.write_payload(quick, [])
    prior = archive/"prior.json"
    builder.write_payload(prior, [full])
    builder.write_payload(manifest, {"marker": "unchanged prior manifest"})
    before = {str(f): f.read_bytes() for f in [news, quick, prior, manifest]}
    monkeypatch.setattr(sys, "argv", ["build_source_archive.py", "--news", str(news),
        "--quick-feed", str(quick), "--output", str(archive), "--manifest", str(manifest)])
    with pytest.raises(ValueError, match="refusing silent body truncation"):
        builder.main()
    assert {str(f): f.read_bytes() for f in [news, quick, prior, manifest]} == before
    assert sorted(f.name for f in archive.iterdir()) == ["prior.json"]
