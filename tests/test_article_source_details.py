"""Source detail delivery must restore admitted text without cross-source/body escalation."""
from copy import deepcopy
from datetime import datetime, timezone
from build_source_archive import build_source_archives, bind_quick_details, source_id
from build_web_feeds import clean_text, shorten

NOW = datetime(2026, 10, 25, tzinfo=timezone.utc)
BODY = ('Αρχή παραγράφου με ελληνικό κείμενο.\n\n' * 170) + 'ΤΕΛΙΚΗ ΠΑΡΑΓΡΑΦΟΣ.'
FULL = dict(quelleName='Greek source', title='Ελληνικό άρθρο', link='https://example.org/article',
            pubDate='2026-10-24T12:00:00Z', content=BODY, contentComplete=True)

def quick(full=FULL):
    excerpt, cut = shorten(full['content'], 4500)
    return dict(full, content=excerpt, contentComplete=False, webFeedTruncated=cut,
                webFeedOriginalLength=len(clean_text(full['content'])))

def build(full, row):
    _, chunks = build_source_archives([full], [row], generated_at=NOW)
    return chunks, bind_quick_details([row], chunks)[0]

def test_complete_greek_body_reaches_last_paragraph_in_small_source_package():
    chunks, row = build(FULL, quick())
    assert row['detailPath'] == f'news-archive/{source_id(FULL["quelleName"])}.json'
    detail = chunks[source_id(FULL['quelleName'])][0]
    assert detail['content'] == BODY
    assert detail['content'].endswith('ΤΕΛΙΚΗ ΠΑΡΑΓΡΑΦΟΣ.')
    assert detail['contentComplete'] is True
    assert row['content'] == quick()['content'] and row['contentComplete'] is False

def test_wrong_identity_length_or_excerpt_never_gets_detail_route():
    for field, value in [('title', 'Another title'), ('quelleName', 'Other source'),
                         ('link', 'https://other.org/article'), ('webFeedOriginalLength', 1),
                         ('content', 'unrelated …')]:
        row = quick(); row[field] = value
        _, bound = build(FULL, row)
        assert 'detailPath' not in bound

def test_incomplete_and_metadata_only_bodies_stay_unadmitted():
    for change in [dict(contentComplete=False), dict(importMode='metadata-only')]:
        full = dict(FULL, **change)
        _, bound = build(full, quick())
        assert 'detailPath' not in bound
    _, bound = build(FULL, dict(quick(), importMode='metadata-only', detailPath='https://evil.org/data'))
    assert 'detailPath' not in bound

def test_archived_excerpt_is_not_promoted_to_complete_body():
    row = quick()
    _, chunks = build_source_archives([], [row], previous_articles=[FULL], generated_at=NOW)
    assert 'detailPath' not in bind_quick_details([row], chunks)[0]
    assert chunks[source_id(FULL['quelleName'])][0]['contentComplete'] is False

def test_existing_restricted_source_policy_removes_full_archive_body_and_route():
    policy = dict(name=FULL['quelleName'], status='approved', importMode='metadata-only',
                  homepage='https://example.org/', categories=['Global'], languages=['el'])
    _, chunks = build_source_archives([FULL], [quick()], source_policies=[policy], generated_at=NOW)
    detail = chunks[source_id(FULL['quelleName'])][0]
    assert BODY not in detail['content']
    assert detail['contentComplete'] is False
    assert 'detailPath' not in bind_quick_details([quick()], chunks)[0]

def test_source_payload_bytes_are_platform_independent(tmp_path):
    from build_source_archive import write_payload
    import json
    target = tmp_path / 'source.json'
    payload = [dict(content='Ελληνικά\n\nΤέλος', contentComplete=True)]
    write_payload(target, payload)
    assert target.read_bytes() == (json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf8')


def test_two_serialized_builds_keep_full_body_after_quick_feed_rollover(tmp_path, monkeypatch):
    import json
    import sys
    import build_source_archive as builder
    from datetime import timedelta
    current = dict(FULL, pubDate=datetime.now(timezone.utc).isoformat())
    news_path, quick_path = tmp_path / 'news.json', tmp_path / 'news-feed.json'
    manifest_path, archive = tmp_path / 'manifest.json', tmp_path / 'archive'
    builder.write_payload(news_path, [current])
    builder.write_payload(quick_path, [quick(current)])
    monkeypatch.setattr(sys, 'argv', ['build_source_archive.py', '--news', str(news_path),
                                      '--quick-feed', str(quick_path), '--manifest', str(manifest_path),
                                      '--output', str(archive)])
    builder.main()
    path = archive / f'{source_id(current["quelleName"])}.json'
    delivered = json.loads(path.read_text(encoding='utf-8'))
    assert delivered[0]['content'] == BODY and delivered[0]['contentComplete'] is True
    builder.write_payload(quick_path, [])
    builder.main()
    assert json.loads(path.read_text(encoding='utf-8')) == delivered
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert manifest['quickIndexCount'] == 0
    assert delivered[0]['content'].endswith('ΤΕΛΙΚΗ ΠΑΡΑΓΡΑΦΟΣ.')


def test_retention_requires_exact_current_identity_full_body_and_https():
    changes = [dict(title='Changed'), dict(quelleName='Other source'),
               dict(link='http://example.org/article'), dict(link='https://user:pass@example.org/article'),
               dict(content=BODY + 'Changed'), dict(contentComplete=False),
               dict(importMode='metadata-only'), dict(webFeedTruncated=True)]
    for change in changes:
        current = dict(FULL, **change)
        previous = dict(FULL)
        # Keep the link equal to test the URL guard independently of identity.
        if 'link' in change:
            previous['link'] = current['link']
        _, chunks = build_source_archives([current], [], previous_articles=[previous], generated_at=NOW)
        detail = next(row for rows in chunks.values() for row in rows if row['link'] == current['link'])
        assert detail['contentComplete'] is False
        assert len(detail['content']) == 1400


def test_old_excerpt_or_incomplete_row_never_authorizes_retention():
    for previous in [dict(FULL, content=BODY[:1400], contentComplete=False,
                          webFeedTruncated=True, webFeedOriginalLength=len(BODY)),
                     dict(FULL, contentComplete=False), dict(FULL, importMode='metadata-only')]:
        _, chunks = build_source_archives([FULL], [], previous_articles=[previous], generated_at=NOW)
        assert chunks[source_id(FULL['quelleName'])][0]['contentComplete'] is False


def test_new_restriction_overrides_previously_delivered_full_body():
    policy = dict(name=FULL['quelleName'], status='approved', importMode='metadata-only',
                  homepage='https://example.org/', categories=['Global'], languages=['el'])
    _, chunks = build_source_archives([FULL], [], previous_articles=[FULL], source_policies=[policy], generated_at=NOW)
    detail = chunks[source_id(FULL['quelleName'])][0]
    assert detail['importMode'] == 'metadata-only'
    assert detail['contentComplete'] is False
    assert BODY not in detail['content']


def test_retention_still_obeys_thirty_day_window():
    from datetime import timedelta
    manifest, chunks = build_source_archives([FULL], [], previous_articles=[FULL],
                                            generated_at=NOW + timedelta(days=31))
    assert chunks == {} and manifest['itemCount'] == 0


def test_package_capacity_counts_utf8_and_fails_instead_of_truncating(monkeypatch):
    import json
    import pytest
    import build_source_archive as builder
    size = len((json.dumps([builder.projected_article(FULL, 1400, retain_body=True)],
                           ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8'))
    monkeypatch.setattr(builder, 'MAX_SOURCE_PACKAGE_BYTES', size - 1)
    with pytest.raises(ValueError, match='refusing silent body truncation'):
        build_source_archives([FULL], [], previous_articles=[FULL], generated_at=NOW)
    monkeypatch.setattr(builder, 'MAX_SOURCE_PACKAGE_BYTES', size)
    _, chunks = build_source_archives([FULL], [], previous_articles=[FULL], generated_at=NOW)
    assert chunks[source_id(FULL['quelleName'])][0]['content'] == BODY
