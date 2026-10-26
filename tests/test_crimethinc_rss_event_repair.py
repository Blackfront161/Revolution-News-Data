import ast
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from reviewed_article_metadata import repair_reviewed_article_metadata
from build_source_archive import build_source_archives

ROOT = Path(__file__).resolve().parents[1]
ROWS = json.loads((ROOT / 'tests/fixtures/crimethinc_mistyped_news.json').read_text(encoding='utf8'))


@pytest.mark.parametrize('original', ROWS, ids=[r['link'].split('/')[-1] for r in ROWS])
def test_five_verified_news_urls_recover_without_changing_other_metadata(original):
    row = dict(deepcopy(original), content='Retained complete article body',
               author='Retained author', id='stable-id', contentComplete=True,
               importMode='metadata-only', image='', images=[])
    row['eventStart'] = row['eventEnd'] = row['pubDate']
    before = deepcopy(row)
    repair_reviewed_article_metadata(row)
    assert row['type'] == 'article'
    assert all(k not in row for k in ['sourceType', 'eventStart', 'eventEnd'])
    assert row['language'] == 'en' and row['languages'] == ['en']
    for k in set(before) - {'type', 'sourceType', 'eventStart', 'eventEnd', 'language', 'languages'}:
        assert row[k] == before[k]
    assert repair_reviewed_article_metadata(deepcopy(row)) == row


@pytest.mark.parametrize('changes', [
    {'quelleName': 'CrimethInc. (Events)'}, {'quelleName': 'Other'},
    {'kontinent': 'Radar'}, {'categories': ['Radar']},
    {'type': 'event', 'sourceType': 'radar-api'},
    {'link': ROWS[0]['link'].replace('crimethinc.com', 'foreign.example')},
    {'link': ROWS[0]['link'].replace('https://', 'http://')},
    {'link': ROWS[0]['link'] + '?other=1'},
    {'link': ROWS[0]['link'].replace('crimethinc.com', 'user@crimethinc.com')},
    {'link': 'https://crimethinc.com/2026/10/27/unreviewed-new-item'},
    {'eventStart': '2026-11-01T10:00:00Z'},
    {'eventEnd': '2026-11-01T12:00:00Z'},
])
def test_other_news_real_events_and_distinct_event_dates_are_untouched(changes):
    row = dict(deepcopy(ROWS[0]), **changes)
    assert repair_reviewed_article_metadata(deepcopy(row)) == row


def test_reviewed_article_language_does_not_relabel_a_translation_or_agenda():
    tree = ast.parse((ROOT / 'aggregate.py').read_text(encoding='utf8'))
    configured = next(ast.literal_eval(n.value) for n in tree.body
                      if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name)
                      and t.id == 'quellen' for t in n.targets))
    agenda = next(f for f in configured['Radar'] if f['name'] == 'CrimethInc. (Events)')
    assert agenda == {'name':'CrimethInc. (Events)',
                      'url':'https://morss.it/https://crimethinc.com/categories/events/feed'}
    translated = dict(ROWS[0], link=ROWS[0]['link'].replace('://crimethinc.com', '://fr.crimethinc.com'),
                      type='article', language='fr', languages=['fr'])
    assert repair_reviewed_article_metadata(deepcopy(translated)) == translated
    news = dict(ROWS[0], type='article')
    assert repair_reviewed_article_metadata(news)['languages'] == ['en']


def test_actual_aggregate_shared_url_guard_prevents_the_original_overwrite():
    tree = ast.parse((ROOT / 'aggregate.py').read_text(encoding='utf8'))
    # Replay the actual shared-URL lookup and agenda assignment, not a second
    # implementation of the guard. Exclude network/scraping and publication.
    statements = next(n.body for n in ast.walk(tree) if isinstance(n, ast.Try)
                      and any(isinstance(s, ast.Assign) and any(isinstance(t, ast.Name)
                              and t.id == 'existing_article' for t in s.targets) for s in n.body))
    index = next(i for i, s in enumerate(statements) if isinstance(s, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'existing_article' for t in s.targets))
    lookup, guard = statements[index:index+2]
    original_event_branch = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                                and isinstance(n.test, ast.Name) and n.test.id == 'is_radar'
                                and any(isinstance(x, ast.Constant) and x.value == 'rss-event'
                                        for x in ast.walk(n)))
    def replay(row, protected):
        statements = [lookup] + ([guard] if protected else []) + [original_event_branch]
        loop = ast.For(target=ast.Name(id='link', ctx=ast.Store()),
                       iter=ast.List(elts=[ast.Constant(value=row['link'])], ctx=ast.Load()),
                       body=statements, orelse=[])
        ns = {'archiv_dict': {row['link']: row}, 'is_radar': True,
              'title': 'Agenda title', 'event_start': '2026-10-28T12:00:00Z', 'radar_count': 0}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[loop], type_ignores=[])),
                     'aggregate-shared-url-replay', 'exec'), ns)
        return row
    news = repair_reviewed_article_metadata(deepcopy(ROWS[0]))
    assert replay(deepcopy(news), False)['type'] == 'event'  # original failure
    assert replay(deepcopy(news), True) == news
    radar = dict(news, kontinent='Radar', type='event')
    assert replay(radar, True)['sourceType'] == 'rss-event'
    assert radar['eventStart'] == '2026-10-28T12:00:00Z'


def test_real_checkpoint_hook_and_source_archive_keep_all_five_repaired_rows():
    tree = ast.parse((ROOT / 'aggregate.py').read_text(encoding='utf8'))
    repair = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == 'repair_overbroad_archive_categories')
    ns = {'repair_reviewed_article_metadata': repair_reviewed_article_metadata,
          'TOPIC_CATEGORY_PATTERNS': {}}
    exec(compile(ast.Module(body=[repair], type_ignores=[]), 'aggregate-checkpoint-repair', 'exec'), ns)
    repaired = [ns['repair_overbroad_archive_categories'](deepcopy(x)) for x in ROWS]
    manifest, chunks = build_source_archives(repaired, repaired, previous_articles=ROWS,
                                            generated_at=datetime(2026, 10, 27, tzinfo=timezone.utc))
    assert manifest['itemCount'] == 5
    published = [x for rows in chunks.values() for x in rows]
    assert len(published) == 5 and all(x['type'] == 'article' for x in published)
    assert {x['link'] for x in published} == {x['link'] for x in ROWS}
