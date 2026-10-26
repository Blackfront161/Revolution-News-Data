import ast
from copy import deepcopy
from pathlib import Path
from urllib.parse import urljoin, urlparse

from reviewed_article_metadata import (
    NUNATSIAQ_SCHOOL_PATH, NUNATSIAQ_SCHOOL_TITLE,
    NUNATSIAQ_SCHOOL_IMAGE, NUNATSIAQ_SCHOOL_SECOND_IMAGE,
    repair_reviewed_article_metadata,
)


def article(**changes):
    return dict({
        'quelleName': 'Nunatsiaq News',
        'link': 'https://nunatsiaq.com' + NUNATSIAQ_SCHOOL_PATH,
        'title': NUNATSIAQ_SCHOOL_TITLE,
        'id': 'stable-id', 'content': 'unchanged body', 'author': 'unchanged author',
        'pubDate': '2026-10-26T13:30:16Z',
        'image': 'https://cdn.nunatsiaq.com/wp-content/uploads/2026/10/A-14811.95.gif?cache-bust=1',
        'images': ['https://cdn.nunatsiaq.com/wp-content/uploads/2026/10/A-14811.95.gif'],
        'language': 'en', 'languages': ['en'],
    }, **changes)


def test_reviewed_original_image_and_inuktitut_replace_only_wrong_metadata():
    row = article()
    before = deepcopy(row)
    repair_reviewed_article_metadata(row)
    assert row['language'] == 'iu' and row['languages'] == ['iu']
    assert row['image'] == NUNATSIAQ_SCHOOL_IMAGE
    assert row['images'] == [NUNATSIAQ_SCHOOL_IMAGE, NUNATSIAQ_SCHOOL_SECOND_IMAGE]
    for key in set(before) - {'image', 'images', 'language', 'languages'}:
        assert row[key] == before[key]
    assert repair_reviewed_article_metadata(deepcopy(row)) == row


def test_exact_identity_guards_do_not_relabel_other_sources_or_english_version():
    for changes in [
        {'quelleName': 'Other publisher'}, {'title': 'Other title'},
        {'link': 'https://foreign.example' + NUNATSIAQ_SCHOOL_PATH},
        {'link': 'https://nunatsiaq.com/stories/article/another_inuk/'},
        {'link': 'https://nunatsiaq.com/stories/article/taloyoaks-new-pangniq-high-school-unveiled-with-public-ceremony/'},
    ]:
        row = article(**changes)
        assert repair_reviewed_article_metadata(deepcopy(row)) == row


def test_metadata_only_withdrawn_and_unillustrated_rows_gain_no_media():
    for changes in [
        {'importMode': 'metadata-only', 'image': '', 'images': []},
        {'status': 'withdrawn', 'image': '', 'images': []},
        {'deleted': True, 'image': '', 'images': []},
        {'image': '', 'images': []},
    ]:
        row = article(**changes)
        repaired = repair_reviewed_article_metadata(row)
        assert repaired['image'] == '' and repaired['images'] == []
        assert repaired['language'] == 'iu'


def test_existing_checkpoint_path_repairs_complete_retained_articles():
    source = Path(__file__).resolve().parents[1] / 'aggregate.py'
    tree = ast.parse(source.read_text(encoding='utf8'))
    repair = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'repair_overbroad_archive_categories')
    ns = {'repair_reviewed_article_metadata': repair_reviewed_article_metadata, 'TOPIC_CATEGORY_PATTERNS': {}}
    exec(compile(ast.Module(body=[repair], type_ignores=[]), str(source), 'exec'), ns)
    row = article(contentComplete=True)
    repaired = ns['repair_overbroad_archive_categories'](row)
    assert repaired['language'] == 'iu' and repaired['image'] == NUNATSIAQ_SCHOOL_IMAGE
    checkpoint = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'save_checkpoint')
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'repair_overbroad_archive_categories' for n in ast.walk(checkpoint))


def test_nunatsiaq_advertising_containers_do_not_enter_article_image_candidates():
    from bs4 import BeautifulSoup
    source = Path(__file__).resolve().parents[1] / 'aggregate.py'
    tree = ast.parse(source.read_text(encoding='utf8'))
    names = {'clean_image_url', 'collect_image_urls'}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    ns = {'urljoin': urljoin, 'urlparse': urlparse,
          'safe_lower': lambda x: str(x or '').lower(), 'safe_text': lambda x: str(x or ''),
          'LAYOUT_FILES': ['logo', 'banner'], 'NON_IMAGE_MEDIA_EXTENSIONS': ('.mp4',)}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), ns)
    html = '''<article><div class="adsanity-373x331"><a><img width="373" height="331" src="/ad.gif"></a></div>
    <a href="https://nunatsiaq.com/ads/notice/"><img src="/advertisement.jpg"></a>
    <figure><img width="1200" height="800" src="/school.jpeg"></figure>
    <figure><img src="/editorial-animation.gif"></figure></article>'''
    result = ns['collect_image_urls'](BeautifulSoup(html, 'html.parser'), 'https://nunatsiaq.com/story/')
    assert result == ['https://nunatsiaq.com/school.jpeg', 'https://nunatsiaq.com/editorial-animation.gif']
    # The publisher-specific rule must not silently filter another publisher.
    other = ns['collect_image_urls'](BeautifulSoup(html, 'html.parser'), 'https://example.org/story/')
    assert 'https://example.org/ad.gif' in other
