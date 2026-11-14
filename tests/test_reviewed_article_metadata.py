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


SOFT_HYPHEN_ROW = {
    "link": "https://perspektive-online.net/2026/11/arrow-3-im-allgaeu-gefahr-fuer-die-trinkwasserversorgung/",
    "quelleName": "Perspektive Online (DE)",
    "pubDate": "Thu, 12 Nov 2026 12:30:27 +0000",
    "title": "Arrow 3 im Allgäu: Gefahr für die Trinkwasser\u00adversorgung?",
    "importMode": "metadata-only", "contentComplete": False,
    "content": "Existing exact metadata body \u00ad stays untouched.",
    "author": "unchanged", "image": "", "images": [],
}


def test_exact_reviewed_soft_hyphen_changes_only_title():
    before = deepcopy(SOFT_HYPHEN_ROW)
    result = repair_reviewed_article_metadata(deepcopy(before))
    assert result["title"] == "Arrow 3 im Allgäu: Gefahr für die Trinkwasserversorgung?"
    assert {k: v for k, v in result.items() if k != "title"} == {k: v for k, v in before.items() if k != "title"}
    assert repair_reviewed_article_metadata(deepcopy(result)) == result


def test_soft_hyphen_correction_rejects_every_unverified_variant():
    variants = [
        {"link": SOFT_HYPHEN_ROW["link"] + "?x=1"},
        {"link": SOFT_HYPHEN_ROW["link"].replace("https:", "http:")},
        {"quelleName": "Other source"},
        {"pubDate": "Thu, 12 Nov 2026 12:30:28 +0000"},
        {"pubDate": "2026-11-12T12:30:27Z"},
        {"title": SOFT_HYPHEN_ROW["title"] + " "},
        {"title": "Other \u00ad title"},
        {"importMode": "fulltext"}, {"importMode": None},
        {"contentComplete": True}, {"contentComplete": None}, {"contentComplete": 0},
    ]
    for changes in variants:
        row = dict(SOFT_HYPHEN_ROW, **changes)
        assert repair_reviewed_article_metadata(deepcopy(row)) == row
    for missing in ["link", "quelleName", "pubDate", "title", "importMode", "contentComplete"]:
        row = deepcopy(SOFT_HYPHEN_ROW)
        del row[missing]
        assert repair_reviewed_article_metadata(deepcopy(row)) == row


def test_reviewed_title_enters_strict_capture_without_relaxing_identity():
    from datetime import datetime, timezone
    import pytest
    from news_archive_capture import merge_capture_rows
    incoming = deepcopy(SOFT_HYPHEN_ROW)
    previous = deepcopy(incoming)
    previous['title'] = previous['title'].replace('\u00ad', '')
    policies = [{'name': previous['quelleName'], 'importMode': 'metadata-only'}]
    now = datetime(2026, 11, 14, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match='identity changed'):
        merge_capture_rows([previous], [incoming], policies, now=now)
    repaired = repair_reviewed_article_metadata(deepcopy(incoming))
    result = merge_capture_rows([previous], [repaired], policies, now=now)
    assert len(result) == 1 and result[0]['title'] == previous['title']
    for changes in [{'title': incoming['title'] + ' other'}, {'pubDate': 'Thu, 12 Nov 2026 12:31:27 +0000'}, {'quelleName': 'Other publisher'}]:
        unverified = repair_reviewed_article_metadata(dict(incoming, **changes))
        with pytest.raises(ValueError, match='identity changed'):
            merge_capture_rows([previous], [unverified], policies, now=now)
