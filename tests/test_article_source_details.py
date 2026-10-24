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
