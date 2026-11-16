"""Bound each delivery package without sacrificing a 30-day full text."""
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone

import pytest
import build_source_archive as b
import news_archive_capture as capture
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
    if not b.DETAIL_PATH.fullmatch(card.get('detailPath', '')):
        return card
    key = card['detailPath'].removeprefix('news-archive/').removesuffix('.json')
    rows = chunks[key]
    revision = b.DETAIL_PATH.fullmatch(card['detailPath'])[1]
    assert hashlib.sha256(b.payload_bytes(rows)).hexdigest() == revision
    assert card['detailUrl'] == b.PUBLIC_ARCHIVE_BASE + card['detailPath']
    assert 'detailRevision' not in card
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
        assert all(item['detailPath'].startswith('news-archive/bridge-detail-') for item in bound)
        assert all('detailUrl' not in item for item in bound)


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
    manifest, _ = b.build_source_archives([], [], generated_at=NOW)
    b.write_payload(tmp_path / 'news-archive-manifest.json', manifest)
    capture.capture_news_archive(rows, tmp_path / 'news-archive-capture.json', [], now=NOW, allow_initialize=True)
    return rows


def checkpoint(root, rows, *, policies=None, now=NOW, feed=None):
    policies = policies if policies is not None else json.loads((root/'multilingual-source-registry.json').read_text())['sources']
    capture.capture_news_archive(rows, root/'news-archive-capture.json', policies, now=now)
    b.write_payload(root/'news.json', rows)
    b.write_payload(root/'news-feed.json', feed if feed is not None else [quick(row) if len(row['content'])>4500 else dict(row) for row in rows])


def outputs(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*.json')
            if p.name not in ('news.json', 'multilingual-source-registry.json')}


def test_serialized_rollover_retains_every_full_body_then_expires(tmp_path, monkeypatch):
    rows = setup_cli(tmp_path, monkeypatch)
    b.main()
    unrelated = dict(article(99, 'Unrelated new article'), quelleName='Another source')
    checkpoint(tmp_path, [unrelated])
    b.main()
    actual = b.read_previous_archives(tmp_path / 'news-archive')
    assert {r['link']: r['content'] for r in actual if r['quelleName'] == NAME} == {r['link']: r['content'] for r in rows}
    assert unrelated in actual
    # Explicit expiry, not removal from the bounded current-news index.
    class Later(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW + timedelta(days=31)
    monkeypatch.setattr(b, 'datetime', Later)
    fresh = dict(article(100, 'New current article after rollover'), quelleName='Fresh source',
                 pubDate=(NOW + timedelta(days=31)).isoformat())
    checkpoint(tmp_path, [fresh], now=NOW + timedelta(days=31))
    b.main()
    assert b.read_previous_archives(tmp_path/'news-archive') == [fresh]
    assert json.loads((tmp_path / 'news-archive-manifest.json').read_text())['itemCount'] == 1
    expired_manifest, expired_chunks = b.build_source_archives([], [], previous_articles=actual,
                                                               generated_at=NOW + timedelta(days=31))
    assert expired_chunks == {} and expired_manifest['itemCount'] == 0


@pytest.mark.parametrize('broken', ['missing', 'invalid', 'hash', 'identity', 'bad-source', 'absolute-url'])
def test_corrupt_previous_data_refuses_all_output_changes(tmp_path, monkeypatch, broken):
    setup_cli(tmp_path, monkeypatch)
    b.main()
    archive = tmp_path / 'news-archive'
    index = archive / f'{b.detail_index_id(NAME)}.json'
    cards = json.loads(index.read_text())
    target = tmp_path / cards[0]['detailPath']
    if broken == 'missing':
        target.unlink()
    elif broken == 'invalid':
        target.write_text('{')
    elif broken == 'hash':
        target.write_bytes(target.read_bytes() + b' ')
    elif broken == 'identity':
        cards[0]['title'] = 'Wrong title'
        b.write_payload(index, cards)
    elif broken == 'absolute-url':
        cards[0]['detailUrl'] = 'https://unrelated.example/forged.json'
        b.write_payload(index, cards)
    else:
        cards[0]['quelleName'] = '\t\u00a0 '
        b.write_payload(index, cards)
    before = outputs(tmp_path)
    with pytest.raises(ValueError, match='refusing archive changes|Previous source count or identity mismatch'):
        b.main()
    assert outputs(tmp_path) == before


def test_current_changes_cannot_restore_stale_text(tmp_path, monkeypatch):
    rows = setup_cli(tmp_path, monkeypatch)
    b.main()
    rows[0]['content'] = 'A new, incomplete excerpt'
    rows[0]['contentComplete'] = False
    before = outputs(tmp_path)
    with pytest.raises(ValueError, match='changed to partial'):
        checkpoint(tmp_path, rows)
    assert outputs(tmp_path) == before
    found = {r['link']: r for r in b.read_previous_archives(tmp_path / 'news-archive')}
    assert found[rows[0]['link']]['content'] != rows[0]['content']
    assert found[rows[0]['link']]['contentComplete'] is True


def test_complete_revision_updates_archive_and_keeps_bound_prior_body(tmp_path, monkeypatch):
    rows=setup_cli(tmp_path,monkeypatch)
    b.main()
    original=rows[0]['content']
    rows[0]=dict(rows[0],content='New complete replacement revision. '*200)
    checkpoint(tmp_path,rows)
    b.main()
    found={r['link']:r for r in b.read_previous_archives(tmp_path/'news-archive')}
    assert found[rows[0]['link']]['content']==rows[0]['content'].strip()
    assert found[rows[0]['link']]['contentComplete'] is True
    stored={r['link']:r for r in capture.read_capture(tmp_path/'news-archive-capture.json')}
    history=stored[rows[0]['link']][capture.HISTORY]
    assert history[0]['body']==original
    assert history[0]['bodySha256']==hashlib.sha256(original.encode()).hexdigest()
    assert history[0]['title']==rows[0]['title'] and history[0]['pubDate']==rows[0]['pubDate']
    assert all(capture.HISTORY not in r for r in found.values())
    assert all(capture.HISTORY.encode() not in path.read_bytes()
               for path in (tmp_path/'news-archive').glob('*.json'))
    before=outputs(tmp_path)
    monkeypatch.setattr(sys,'argv',['build_source_archive.py','--verify-only'])
    b.main()
    assert outputs(tmp_path)==before


@pytest.mark.parametrize('mode', ['withdrawn', 'metadata-only', 'technical-pause'])
def test_policy_applies_to_retained_detail_files(tmp_path, monkeypatch, mode):
    rows = setup_cli(tmp_path, monkeypatch)
    b.main()
    unrelated = dict(article(99, 'Unrelated new article'), quelleName='Another source')
    policy = dict(name=NAME, homepage='https://example.org/', categories=['Global'], languages=['en'])
    if mode == 'withdrawn':
        policy['status'] = 'withdrawn'
    elif mode == 'metadata-only':
        policy.update(status='disabled', importMode='metadata-only')
    else:
        policy.update(status='disabled', enabled=False)
    b.write_payload(tmp_path / 'multilingual-source-registry.json', {'sources': [policy]})
    checkpoint(tmp_path, [unrelated])
    b.main()
    retained = [r for r in b.read_previous_archives(tmp_path / 'news-archive') if r['quelleName'] == NAME]
    if mode == 'technical-pause':
        assert {r['link']: r['content'] for r in retained} == {r['link']: r['content'] for r in rows}
    else:
        assert not list((tmp_path / 'news-archive').glob('bridge-detail-*.json'))
        assert all(r.get('contentComplete') is False for r in retained)
        if mode == 'withdrawn':
            assert not retained


def test_single_oversized_article_still_fails_without_touching_outputs(tmp_path, monkeypatch):
    setup_cli(tmp_path, monkeypatch)
    b.main()
    huge = article(99, 'λ' * (3 * 1024 * 1024))
    checkpoint(tmp_path, [huge])
    before = outputs(tmp_path)
    with pytest.raises(ValueError, match='refusing silent body truncation'):
        b.main()
    assert outputs(tmp_path) == before


def test_quick_feed_tombstone_wins_over_old_complete_body(tmp_path, monkeypatch):
    rows = setup_cli(tmp_path, monkeypatch)
    b.main()
    unrelated = dict(article(99, 'Unrelated new article'), quelleName='Another source')
    tombstone = dict(quick(rows[0]), status='withdrawn')
    checkpoint(tmp_path, [unrelated], feed=[tombstone])
    before = outputs(tmp_path)
    with pytest.raises(ValueError, match='Bound quick feed is empty'):
        b.main()
    assert outputs(tmp_path) == before
    # A live survivor permits publishing the withdrawal, never an empty feed.
    b.write_payload(tmp_path / 'news-feed.json', [tombstone, unrelated])
    b.main()
    retained = b.read_previous_archives(tmp_path / 'news-archive')
    assert rows[0]['link'] not in {r['link'] for r in retained}
    assert json.loads((tmp_path / 'news-feed.json').read_text()) == [unrelated]
    assert json.loads((tmp_path / 'feed-status.json').read_text())['news']['feedCount'] == 1


@pytest.mark.parametrize('field', ['detailUrl', 'detailPath'])
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
    unrelated = dict(article(99, 'Unrelated new article'), quelleName='Another source')
    checkpoint(tmp_path, [unrelated])
    index = tmp_path / 'news-archive' / f'{b.detail_index_id(NAME)}.json'
    cards = json.loads(index.read_text())
    previous_detail = tmp_path / cards[0]['detailPath']
    cards[0].update(restriction)
    b.write_payload(index, cards)
    b.main()
    found = {row['link']: row for row in b.read_previous_archives(tmp_path / 'news-archive')}
    assert not previous_detail.exists()
    stored={row['link']:row for row in capture.read_capture(tmp_path/'news-archive-capture.json')}
    # The versioned producer file cannot retain a revoked body either.
    target=stored.get(rows[0]['link'])
    assert target is None or ('λ' not in target.get('content','') and not target.get(capture.HISTORY))
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
    path = f'news-archive/bridge-detail-{revision}.json'
    (tmp_path / path).write_bytes(raw)
    cards[0].update(detailPath=path, detailUrl=b.PUBLIC_ARCHIVE_BASE + path)
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


def test_inline_body_inside_bridge_index_binds_to_the_bridge_path():
    rows = [article(i) for i in range(5)]
    short = article(99, 'x' * 1000)
    card = dict(short, content='x' * 500, contentComplete=False,
                webFeedTruncated=True, webFeedOriginalLength=1000)
    cards = [quick(row) for row in rows] + [card]
    _, chunks = b.build_source_archives(rows + [short], cards, generated_at=NOW)
    assert b.source_id(NAME) not in chunks
    index = chunks[b.detail_index_id(NAME)]
    assert next(row for row in index if row['link'] == short['link'])['content'] == short['content']
    bound = b.bind_quick_details([card], chunks)[0]
    assert bound['detailPath'] == f'news-archive/{b.detail_index_id(NAME)}.json'
    assert 'detailRevision' not in bound


def test_empty_canonical_news_refuses_all_output_changes(tmp_path, monkeypatch):
    setup_cli(tmp_path, monkeypatch)
    b.main()
    b.write_payload(tmp_path / 'news.json', [])
    before = outputs(tmp_path)
    with pytest.raises(ValueError, match='news.json is empty; refusing archive changes'):
        b.main()
    assert outputs(tmp_path) == before


@pytest.mark.parametrize('quick_mode', ['absent', 'unshortened', 'wrong-identity'])
def test_complete_current_body_does_not_depend_on_quick_feed_membership(quick_mode):
    row = article(body='Complete original text. ' * 120 + 'LAST PARAGRAPH')
    if quick_mode == 'absent':
        feed = []
    elif quick_mode == 'unshortened':
        feed = [dict(row)]
    else:
        feed = [dict(quick(row), title='Different article')]
    _, chunks = b.build_source_archives([row], feed, generated_at=NOW)
    full = chunks[b.source_id(NAME)][0]
    assert full['content'] == row['content'] and full['contentComplete'] is True
    # Retaining canonical text does not relax a consumer's identity binding.
    if feed:
        assert 'detailPath' not in b.bind_quick_details(feed, chunks)[0]


def test_canonical_revision_wins_without_reusing_previous_body():
    previous = article(body='OLD BODY ' * 1000)
    for change in ({'title': 'New title'}, {'quelleName': 'Different source'}):
        current = dict(previous, **change)
        with pytest.raises(ValueError,match='identity conflict'):
            b.build_source_archives([current], [], previous_articles=[previous], generated_at=NOW)
        assert previous['title']=='Article 0' and previous['quelleName']==NAME
    current=dict(previous,content='NEW BODY '*1000)
    captured=capture.merge_capture_rows([previous],[current],[],now=NOW)
    _,chunks=b.build_source_archives(captured,[],previous_articles=[previous],generated_at=NOW)
    found=next(row for rows in chunks.values() for row in rows if row['link']==current['link'])
    assert found['content']==current['content'].strip() and found['contentComplete'] is True
    assert found['title']==previous['title'] and found['quelleName']==previous['quelleName']
    assert captured[0][capture.HISTORY][0]['body']==previous['content']
    incomplete = dict(previous, content='CURRENT EXCERPT ' * 100, contentComplete=False)
    with pytest.raises(ValueError,match='changed to partial'):
        capture.merge_capture_rows([previous],[incomplete],[],now=NOW)
    assert incomplete['contentComplete'] is False and 'OLD BODY' not in incomplete['content']


@pytest.mark.parametrize('change', [
    {'contentComplete': 'true'}, {'contentComplete': 1}, {'contentComplete': False},
    {'webFeedTruncated': True}, {'webFeedTruncated': 'true'}, {'webFeedTruncated': 0},
    {'webFeedTruncated': None}, {'title': ''}, {'quelleName': ''}, {'content': ''},
    {'link': 'http://example.org/a'}, {'link': 'https://u:p@example.org/a'},
    {'link': 'https://example.org:invalid/a'}, {'link': 'https:///a'},
    {'content': ['not a body']}, {'title': 5}, {'link': 5},
    {'importMode': 'metadata-only'}, {'importMode': 'directory-only'},
    {'importMode': 'disabled'}, {'contentPolicy': 'metadata_and_links_only'},
    {'status': 'withdrawn'}, {'deleted': True},
])
def test_current_full_body_admission_rejects_invalid_or_restricted_records(change):
    assert b.can_retain_complete_body(dict(article(), **change)) is False


@pytest.mark.parametrize('restriction', [
    {'importMode': 'metadata-only'}, {'importMode': 'directory-only'},
    {'importMode': 'disabled'}, {'contentPolicy': 'metadata_and_links_only'},
    {'status': 'directory-only'}, {'status': 'withdrawn'},
])
@pytest.mark.parametrize('branch', ['current', 'quick-bound', 'previous'])
def test_restrictive_source_policy_cannot_be_bypassed_by_other_retention_branch(restriction, branch):
    row=article(body='protected body ' * 1000)
    policy=dict(name=NAME, homepage='https://example.org/', **restriction)
    news=[] if branch=='previous' else [row]
    feed=[quick(row)] if branch=='quick-bound' else []
    prior=[row] if branch=='previous' else []
    _,chunks=b.build_source_archives(news,feed,previous_articles=prior,
                                     source_policies=[policy],generated_at=NOW)
    assert all(r.get('contentComplete') is not True for rows in chunks.values() for r in rows)
    if restriction.get('status')=='withdrawn':assert chunks=={}


def test_technical_pause_does_not_withdraw_an_existing_canonical_body():
    row=article(body='retained body ' * 1000)
    _,chunks=b.build_source_archives([row],[],source_policies=[dict(name=NAME,status='disabled',enabled=False)],generated_at=NOW)
    assert chunks[b.source_id(NAME)][0]['content']==row['content'].strip()


def test_serialized_current_only_large_source_survives_rollover_without_quick_feed(tmp_path,monkeypatch):
    rows=setup_cli(tmp_path,monkeypatch)
    unrelated=dict(article(99,'unrelated current item'),quelleName='Other source')
    checkpoint(tmp_path, rows+[unrelated], feed=[unrelated])
    b.main()
    first=b.read_previous_archives(tmp_path/'news-archive')
    assert {r['link']:r['content'] for r in first if r['quelleName']==NAME}=={r['link']:r['content'] for r in rows}
    assert list((tmp_path/'news-archive').glob('bridge-detail-*.json'))
    checkpoint(tmp_path,[unrelated])
    b.main()
    after={r['link']:r for r in b.read_previous_archives(tmp_path/'news-archive')}
    assert all(after[r['link']]['content']==r['content'] and after[r['link']]['contentComplete'] is True for r in rows)
    assert all(p.stat().st_size<=b.MAX_SOURCE_PACKAGE_BYTES for p in (tmp_path/'news-archive').rglob('*.json'))


@pytest.mark.parametrize('restriction', [
    {'importMode': 'metadata-only'}, {'contentPolicy': 'metadata_and_links_only'},
    {'importMode': 'directory-only'}, {'importMode': 'disabled'}, {'status': 'directory-only'},
])
@pytest.mark.parametrize('location', ['row','source'])
def test_short_restricted_body_is_not_leaked_or_promoted_after_serialization(tmp_path,restriction,location):
    body='SHORT PROTECTED ORIGINAL'
    row=article(body=body)
    if location=='row':row.update(restriction)
    policies=[dict(name='  '+NAME.upper()+'  ',homepage='https://example.org/',**restriction)] if location=='source' else []
    _,chunks=b.build_source_archives([row],[],source_policies=policies,generated_at=NOW)
    assert body not in json.dumps(chunks)
    assert all(r.get('contentComplete') is False for rows in chunks.values() for r in rows)
    for identifier,rows in chunks.items():b.write_payload(tmp_path/f'{identifier}.json',rows)
    previous=b.read_previous_archives(tmp_path)
    # Metadata restrictions persist on the projected row, even without the
    # original contentPolicy field or source registry on the next build.
    _,again=b.build_source_archives([],[],previous_articles=previous,generated_at=NOW)
    assert body not in json.dumps(again)
    assert all(r.get('contentComplete') is False for rows in again.values() for r in rows)


@pytest.mark.parametrize('change',[{'link':'http://example.org/short'},
                                   {'webFeedTruncated':'false'},{'contentComplete':'true'}])
def test_short_unverified_record_is_not_labelled_complete(change):
    row=dict(article(body='Short unverified text'),**change)
    _,chunks=b.build_source_archives([row],[],generated_at=NOW)
    assert all(r.get('contentComplete') is False for rows in chunks.values() for r in rows)


@pytest.mark.parametrize('scope',['row','source'])
def test_unknown_import_policy_fails_before_outputs_instead_of_dropping_article(tmp_path,monkeypatch,scope):
    rows=setup_cli(tmp_path,monkeypatch);b.main()
    if scope=='row':
        rows[0]['importMode']='unknown-policy'
        b.write_payload(tmp_path/'news.json',rows)
    else:
        b.write_payload(tmp_path/'multilingual-source-registry.json',{'sources':[dict(name=NAME,importMode='unknown-policy')]})
    before=outputs(tmp_path)
    with pytest.raises(ValueError,match='Unknown .*import policy'):b.main()
    assert outputs(tmp_path)==before
