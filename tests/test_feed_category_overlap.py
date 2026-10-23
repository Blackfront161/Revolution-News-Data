from collections import Counter
from build_web_feeds import balanced_news_rows, stable_key


def test_prior_category_overlap_cannot_repeat_asia_publisher_before_missing_ones():
    rows = []
    for index in range(8):
        for depth in range(3):
            rows.append({'title':f'Article {index} {depth}', 'content':'Public body',
                         'link':f'https://example.org/{index}/{depth}',
                         'quelleName':f'Publisher {index}',
                         'pubDate':f'2026-10-{24-depth:02d}T{23-index:02d}:00:00Z',
                         'categories':['Asia', 'Global'] if index < 2 else ['Asia']})
    output = balanced_news_rows(rows, limit=50)
    asia = [r for r in output if 'Asia' in r['categories']]
    assert len({r['quelleName'] for r in asia[:8]}) == 8
    assert Counter(map(stable_key, output)) == Counter(map(stable_key, rows))


def test_continent_only_story_does_not_consume_explicit_category_publisher_slot():
    rows = [{'title':f'Article {i}', 'content':'Public body',
             'link':f'https://example.org/{i}', 'quelleName':f'Publisher {i}',
             'pubDate':'2026-10-24T00:00:00Z', 'categories':['Asia']}
            for i in range(8)]
    rows.insert(0, {**rows[-1], 'link':'https://example.org/global',
                    'pubDate':'2026-10-25T00:00:00Z',
                    'categories':['Global'], 'kontinent':'Asia'})
    output = balanced_news_rows(rows, limit=50)
    asia = [r for r in output if 'Asia' in r['categories']]
    assert len({r['quelleName'] for r in asia[:8]}) == 8
