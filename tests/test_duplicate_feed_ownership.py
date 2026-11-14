from copy import deepcopy
import ast
from pathlib import Path
import pytest
from duplicate_feed_ownership import duplicate_ownership_skip

URL = 'https://libcom.org/news/feed'
CONFIG = [{'name': 'A', 'url': URL}, {'name': 'B', 'url': URL}]
ROW = {'link': 'https://libcom.org/article/example', 'quelleName': 'A', 'title': 'unchanged', 'content': 'exact original body', 'contentComplete': True}

@pytest.mark.parametrize('changes', [{}, {'importMode': 'metadata-only', 'contentComplete': False}, {'status': 'withdrawn', 'content': ''}])
def test_duplicate_delivery_never_mutates_owned_body_or_restriction(changes):
    row = dict(ROW, **changes); before = deepcopy(row); config = deepcopy(CONFIG)
    assert duplicate_ownership_skip(row, 'B', config, row['link'])
    assert row == before and config == CONFIG

@pytest.mark.parametrize('config', [
    [{'name':'A','url':URL}, {'name':'B','url':URL+'/other'}],
    [{'name':'B','url':URL}], [{'name':'A','url':URL}],
    CONFIG+[{'name':'A','url':URL+'/other'}],
    [{'name':'A','url':URL,'feedUrl':URL+'/other'}, {'name':'B','url':URL}],
    [{'name':'A','requestUrl':URL}, {'name':'B','requestUrl':URL}],
])
def test_unproven_feed_ownership_is_not_skipped(config):
    assert not duplicate_ownership_skip(ROW,'B',config,ROW['link'])


def test_other_link_same_owner_and_missing_existing_are_not_skipped():
    assert not duplicate_ownership_skip(ROW,'B',CONFIG,ROW['link']+'/different')
    assert not duplicate_ownership_skip(ROW,'A',CONFIG,ROW['link'])
    assert not duplicate_ownership_skip(None,'B',CONFIG,ROW['link'])


def test_hook_precedes_metadata_and_body_extraction_without_capture_changes():
    text=(Path(__file__).resolve().parents[1]/'aggregate.py').read_text()
    hook=text.index('if not is_radar and duplicate_ownership_skip(')
    assert hook < text.index('if feed.get("importMode") == "metadata-only":',hook)
    assert hook < text.index('existing_article = archiv_dict.get(link)',hook)
    tree=ast.parse(text)
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and any(isinstance(c,ast.Call) and isinstance(c.func,ast.Name) and c.func.id=='duplicate_ownership_skip' for c in ast.walk(n.test)))
    assert isinstance(node.body[-1],ast.Continue)
    assert len(node.body)==2
