import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREE = ast.parse((ROOT / 'aggregate.py').read_text(encoding='utf-8'))

def eligibility():
    selected = [n for n in TREE.body if isinstance(n, ast.FunctionDef)
                and n.name in {'source_key', 'fast_source_is_eligible'}]
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {'safe_lower': lambda v: str(v or '').strip().lower()}
    exec(compile(module, 'aggregate.py', 'exec'), namespace)
    return namespace['fast_source_is_eligible']

def test_retired_endpoint_failure_does_not_block_reviewed_replacement():
    old = {'name': 'Pramen (BY)', 'url': 'https://pramen.io/feed/', 'ok': False,
           'detailedState': 'permanently_broken', 'consecutiveFailures': 10}
    check = eligibility()
    assert check({'name': old['name'], 'url': 'https://pramen.io/ru/feed/'},
                 {old['name'].lower(): old}, {})
    assert not check({'name': old['name'], 'url': old['url']},
                     {old['name'].lower(): old}, {})
    assert not check({'name': old['name'], 'url': 'https://pramen.io/ru/feed/'}, {},
                     {'https://pramen.io/ru/feed': old})

def test_restricted_sources_cannot_enter_archive_page_repair():
    blocks = [n for n in ast.walk(TREE) if isinstance(n, ast.If)
              and any(isinstance(x, ast.Name) and x.id == 'repair_candidates'
                      for statement in n.body for x in ast.walk(statement))]
    assert len(blocks) == 1
    condition = ast.Expression(body=blocks[0].test)
    state = {'aggregate_stopped_for_budget': False, 'is_radar': False, 'FAST_MODE': False,
             'tiefe_scrapes_gemacht': 0, 'MAX_NEUE_SCRAPES': 4}
    for mode, allowed in [('metadata-only', False), ('fulltext', True)]:
        assert eval(compile(condition, 'aggregate.py', 'eval'), {**state, 'feed': {'importMode': mode}}) is allowed

def test_reviewed_feed_redirect_is_exact_and_keeps_other_domains_blocked():
    from source_recovery import suspicious_redirect
    original = 'https://antifa.cz/feed.xml'
    assert not suspicious_redirect(original, 'https://antifa-cz.net/feed.xml')
    for final in ['https://antifa-cz.net/other.xml', 'https://antifa-cz.net/feed.xml?new=1',
                  'http://antifa-cz.net/feed.xml', 'https://antifa-cz.net:8443/feed.xml',
                  'https://evil.example/feed.xml']:
        assert suspicious_redirect(original, final)

def test_publication_refreshes_registry_from_current_inputs():
    for filename in ['update.yml', 'update-fast.yml']:
        text = (ROOT / '.github/workflows' / filename).read_text(encoding='utf-8')
        assert 'python build_sources_registry.py' in text
        assert any('git add' in line and 'sources-registry.json' in line for line in text.splitlines())

def test_relative_feed_links_use_verified_response_base_without_admitting_foreign_hosts():
    import feedparser
    from types import SimpleNamespace
    from source_import_policy import metadata_article
    node = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'fetch_fast_feed')
    body = b'<rss version="2.0"><channel><title>News</title><item><title>Public update</title><link>/posts/update/</link></item><item><title>Foreign</title><link>//unrelated.example/post</link></item></channel></rss>'
    response = SimpleNamespace(content=body, url='https://www.systemli.org/index.xml', raise_for_status=lambda: None)
    from source_endpoint_repairs import request_url
    scope = {'requests': SimpleNamespace(get=lambda *a, **k: response), 'HEADERS': {}, 'feedparser': feedparser, 'request_url': request_url}
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'aggregate.py', 'exec'), scope)
    feed = {'name':'Systemli','url':response.url,'homepage':'https://www.systemli.org/','importMode':'metadata-only','languages':['de']}
    entries = scope['fetch_fast_feed'](feed).entries
    assert entries[0].link == 'https://www.systemli.org/posts/update/'
    assert metadata_article(feed, entries[0], 'Europe')['link'] == entries[0].link
    assert metadata_article(feed, entries[1], 'Europe') is None
