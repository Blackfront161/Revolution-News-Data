"""Bound each delivery package without sacrificing a 30-day full text."""
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone

import pytest
import build_source_archive as b
from build_web_feeds import shorten, clean_text

NOW = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
NAME = 'LabourNet DE'


def article(index=0, body=None):
    return dict(quelleName=NAME, title=f'Article {index}', link=f'https://example.org/{index}',
                pubDate=(NOW - timedelta(hours=1)).isoformat(),
                content=body if body is not None else ('λ' * 600_000 + f'\nLAST {index}'),
                contentComplete=True)


def quick(row):
    excerpt, cut = shorten(row['content'], 4500)
    return dict(row, content=excerpt, contentComplete=False, webFeedTruncated=cut,
                webFeedOriginalLength=len(clean_text(row['content'])))


def resolved(chunks, card):
    if 'detailRevision' not in card:
        return card
    key = card['detailPath'].removeprefix('news-archive/').removesuffix('.json')
    rows = chunks[key]
    assert hashlib.sha256(b.payload_bytes(rows)).hexdigest() == card['detailRevision']
    assert card['detailRevision'] in card['detailPath']
    assert b.detail_matches(card, rows[0])
    return rows[0]


def test_more_than_eight_mib_is_split_losslessly_for_every_source():
    for name in (NAME, 'Another source'):
        rows = [dict(article(i), quelleName=name) for i in range(10)]
        assert len(b.payload_bytes(rows)) > 8 * 1024 * 1024
        manifest, chunks = b.build_source_archives(rows, [quick(r) for r in rows], generated_at=NOW)
        cards = chunks[b.detail_index_id(name)]
        assert manifest["sources"][0]["id"] == b.detail_index_id(name)
        assert manifest["sources"][0]["legacyId"] == b.source_id(name)
        assert manifest["sources"][0]["path"] == f"news-archive/{b.detail_index_id(name)}.json"
        assert b.detail_index_id(name) != b.source_id(name)
        assert manifest['schemaVersion'] == 1 and manifest['itemCount'] == len(rows)
        assert len(cards) == len(rows)
        assert all(len(b.payload_bytes(group)) <= 4 * 1024 * 1024 for group in chunks.values())
        assert [resolved(chunks, card)['content'] for card in cards] == [r['content'] for r in rows]
        bound = b.bind_quick_details([quick(r) for r in rows], chunks)
        assert all(item['detailPath'].startswith('news-archive/details/') for item in bound)
        assert all(item['detailUrl'] == b.PUBLIC_ARCHIVE_BASE + item['detailPath'] for item in bound)


def test_small_sources_keep_existing_v1_path_and_full_body():
    row = article(body=('text ' * 2000).strip())
    _, chunks = b.build_source_archives([row], [quick(row)], generated_at=NOW)
    assert list(chunks) == [b.source_id(NAME)]
    assert chunks[b.source_id(NAME)][0]['content'] == row['content']
    assert b.bind_quick_details([quick(row)], chunks)[0]['detailPath'] == f'news-archive/{b.source_id(NAME)}.json'


def setup_cli(tmp_path, monkeypatch):
    monkeypatch.setattr(b, 'ROOT', tmp_path)
    monkeypatch.setattr(sys, 'argv', ['build_source_archive.py'])
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW
    monkeypatch.setattr(b, 'datetime', Clock)
    b.write_payload(tmp_path / 'multilingual-source-registry.json', {'sources': []})
    b.write_payload(tmp_path / 'feed-status.json', {'news': {}})
    rows = [article(i) for i in range(5)]
    b.write_payload(tmp_path / 'news.json', rows)
    b.write_payload(tmp_path / 'news-feed.json', [quick(row) for row in rows])
    return rows


def outputs(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*.json')
            if p.name not in ('news.json', 'multilingual-source-registry.json')}


def test_serialized_rollover_retains_every_full_body_then_expires(tmp_path, monkeypatch):
    rows = setup_cli(tmp_path, monkeypatch)
    b.main()
    b.write_payload(tmp_path / 'news.json', [])
    b.write_payload(tmp_path / 'news-feed.json', [])
    b.main()
    actual = b.read_previous_archives(tmp_path / 'news-archive')
    assert {r['link']: r['content'] for r in actual} == {r['link']: r['content'] for r in rows}
    # Explicit expiry, not removal from the bounded current-news index.
    class Later(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW + timedelta(days=31)
    monkeypatch.setattr(b, 'datetime', Later)
    b.main()
    assert not list((tmp_path / 'news-archive').rglob('*.json'))
    assert json.loads((tmp_path / 'news-archive-manifest.json').read_text())['itemCount'] == 0


@pytest.mark.parametrize('broken', ['missing', 'invalid', 'hash', 'identity', 'bad-source'])
def test_corrupt_previous_data_refuses_all_output_changes(tmp_path, monkeypatch, broken):
    setup_cli(tmp_path, monkeypatch)
    b.main()
    archive = tmp_path / 'news-archive'
    index = archive / f'{b.detail_index_id(NAME)}.json'
    cards = json.loads(index.read_text())
    target = archive / 'details' / (cards[0]['detailRevision'] + '.json')
    if broken == 'missing':
        target.unlink()
    elif broken == 'invalid':
        target.write_text('{')
    elif broken == 'hash':
        target.write_bytes(target.read_bytes() + b' ')
    elif broken == 'identity':
        cards[0]['title'] = 'Wrong title'
        b.write_payload(index, cards)
    else:
        cards[0]['quelleName'] = '\t\u00a0 '
        b.write_payload(index, cards)
    before = outputs(tmp_path)
    with pytest.raises(ValueError, match='refusing archive changes'):
        b.main()
    assert outputs(tmp_path) == before


def test_current_changes_cannot_restore_stale_text(tmp_path, monkeypatch):
    rows = setup_cli(tmp_path, monkeypatch)
    b.main()
    rows[0]['content'] = 'A new, incomplete excerpt'
    rows[0]['contentComplete'] = False
    b.write_payload(tmp_path / 'news.json', rows)
    b.write_payload(tmp_path / 'news-feed.json', [])
    b.main()
    found = {r['link']: r for r in b.read_previous_archives(tmp_path / 'news-archive')}
    assert found[rows[0]['link']]['content'] == rows[0]['content']
    assert found[rows[0]['link']]['contentComplete'] is False


@pytest.mark.parametrize('mode', ['withdrawn', 'metadata-only', 'technical-pause'])
def test_policy_applies_to_retained_detail_files(tmp_path, monkeypatch, mode):
    rows = setup_cli(tmp_path, monkeypatch)
    b.main()
    b.write_payload(tmp_path / 'news.json', [])
    b.write_payload(tmp_path / 'news-feed.json', [])
    policy = dict(name=NAME, homepage='https://example.org/', categories=['Global'], languages=['en'])
    if mode == 'withdrawn':
        policy['status'] = 'withdrawn'
    elif mode == 'metadata-only':
        policy.update(status='disabled', importMode='metadata-only')
    else:
        policy.update(status='disabled', enabled=False)
    b.write_payload(tmp_path / 'multilingual-source-registry.json', {'sources': [policy]})
    b.main()
    retained = b.read_previous_archives(tmp_path / 'news-archive')
    if mode == 'technical-pause':
        assert {r['link']: r['content'] for r in retained} == {r['link']: r['content'] for r in rows}
    else:
        assert not list((tmp_path / 'news-archive' / 'details').glob('*.json'))
        assert all(r.get('contentComplete') is False for r in retained)
        if mode == 'withdrawn':
            assert not retained


def test_single_oversized_article_still_fails_without_touching_outputs(tmp_path, monkeypatch):
    setup_cli(tmp_path, monkeypatch)
    b.main()
    huge = article(99, 'λ' * (3 * 1024 * 1024))
    b.write_payload(tmp_path / 'news.json', [huge])
    b.write_payload(tmp_path / 'news-feed.json', [quick(huge)])
    before = outputs(tmp_path)
    with pytest.raises(ValueError, match='refusing silent body truncation'):
        b.main()
    assert outputs(tmp_path) == before


def test_quick_feed_tombstone_wins_over_old_complete_body(tmp_path, monkeypatch):
    rows = setup_cli(tmp_path, monkeypatch)
    b.main()
    b.write_payload(tmp_path / 'news.json', [])
    b.write_payload(tmp_path / 'news-feed.json', [dict(quick(rows[0]), status='withdrawn')])
    b.main()
    retained = b.read_previous_archives(tmp_path / 'news-archive')
    assert rows[0]['link'] not in {r['link'] for r in retained}
    assert json.loads((tmp_path / 'news-feed.json').read_text()) == []
    assert json.loads((tmp_path / 'feed-status.json').read_text())['news']['feedCount'] == 0


@pytest.mark.parametrize('field', ['detailRevision', 'detailPath'])
def test_incomplete_previous_detail_reference_is_never_demoted(tmp_path, monkeypatch, field):
    setup_cli(tmp_path, monkeypatch)
    b.main()
    index = tmp_path / 'news-archive' / f'{b.detail_index_id(NAME)}.json'
    cards = json.loads(index.read_text())
    del cards[0][field]
    b.write_payload(index, cards)
    before = outputs(tmp_path)
    with pytest.raises(ValueError, match='Invalid previous detail reference'):
        b.main()
    assert outputs(tmp_path) == before


@pytest.mark.parametrize('restriction', [{'deleted': True}, {'status': 'withdrawn'}, {'importMode': 'metadata-only'}])
def test_index_restriction_cannot_be_undone_by_hydration(tmp_path, monkeypatch, restriction):
    rows = setup_cli(tmp_path, monkeypatch)
    b.main()
    b.write_payload(tmp_path / 'news.json', [])
    b.write_payload(tmp_path / 'news-feed.json', [])
    index = tmp_path / 'news-archive' / f'{b.detail_index_id(NAME)}.json'
    cards = json.loads(index.read_text())
    previous_detail = tmp_path / cards[0]['detailPath']
    cards[0].update(restriction)
    b.write_payload(index, cards)
    b.main()
    found = {row['link']: row for row in b.read_previous_archives(tmp_path / 'news-archive')}
    assert not previous_detail.exists()
    if restriction.get('importMode') == 'metadata-only':
        assert found[rows[0]['link']]['contentComplete'] is False
        assert 'λ' not in found[rows[0]['link']]['content']
    else:
        assert rows[0]['link'] not in found


def test_row_level_metadata_only_drops_all_secondary_content_fields():
    row = dict(article(body='PROTECTED FULL BODY'), importMode='metadata-only',
               description='PROTECTED DESCRIPTION', summary='PROTECTED SUMMARY',
               contentBlocks=[{'text': 'PROTECTED BLOCK'}], imageUrl='https://example.org/private.jpg',
               image='https://example.org/private.jpg', images=['https://example.org/private.jpg'])
    cleaned = b.bind_quick_details([row], {})[0]
    assert 'PROTECTED' not in json.dumps(cleaned)
    assert all(key not in cleaned for key in ('description', 'summary', 'contentBlocks', 'imageUrl'))
    assert cleaned['contentComplete'] is False and cleaned['images'] == []


@pytest.mark.parametrize('date', [None, 'invalid', '2020-01-01T00:00:00Z'])
def test_detail_date_must_match_the_retained_index(tmp_path, monkeypatch, date):
    setup_cli(tmp_path, monkeypatch)
    b.main()
    index = tmp_path / 'news-archive' / f'{b.detail_index_id(NAME)}.json'
    cards = json.loads(index.read_text())
    old = tmp_path / cards[0]['detailPath']
    full = json.loads(old.read_text())
    full[0]['pubDate'] = date
    raw = b.payload_bytes(full)
    revision = hashlib.sha256(raw).hexdigest()
    path = f'news-archive/details/{revision}.json'
    (tmp_path / path).write_bytes(raw)
    cards[0].update(detailRevision=revision, detailPath=path, detailUrl=b.PUBLIC_ARCHIVE_BASE + path)
    b.write_payload(index, cards)
    before = outputs(tmp_path)
    with pytest.raises(ValueError, match='revision mismatch'):
        b.main()
    assert outputs(tmp_path) == before


def test_source_identity_returns_to_v1_only_with_full_inline_bodies():
    rows = [article(i) for i in range(5)]
    manifest, chunks = b.build_source_archives(rows, [quick(r) for r in rows], generated_at=NOW)
    cards = chunks[b.detail_index_id(NAME)]
    hydrated = [resolved(chunks, card) for card in cards]
    # Simulate expiry of four items. The remaining old body must be inline,
    # never a compact excerpt replacing an old v1 cache entry.
    kept = hydrated[:1]
    manifest, chunks = b.build_source_archives([], [], previous_articles=kept, generated_at=NOW)
    assert manifest['sources'][0]['id'] == b.source_id(NAME)
    assert list(chunks) == [b.source_id(NAME)]
    assert chunks[b.source_id(NAME)][0]['content'] == kept[0]['content']
    assert chunks[b.source_id(NAME)][0]['contentComplete'] is True


@pytest.mark.parametrize('bad_policy', [{}, {'name': ''}, {'name': 9}, {'importMode': 'metadata-only'}])
def test_malformed_source_policy_refuses_all_output_changes(tmp_path, monkeypatch, bad_policy):
    setup_cli(tmp_path, monkeypatch)
    b.main()
    b.write_payload(tmp_path / 'multilingual-source-registry.json', {'sources': [bad_policy]})
    before = outputs(tmp_path)
    with pytest.raises(ValueError, match='Invalid source policies'):
        b.main()
    assert outputs(tmp_path) == before
