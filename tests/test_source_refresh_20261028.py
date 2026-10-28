"""Restricted source admission and exact endpoint repairs, without network access."""
import ast
import copy
import json
from pathlib import Path
import tempfile
import unittest

from source_endpoint_repairs import reviewed_source, request_url
from source_import_policy import metadata_article
from build_sources_registry import normalize_record
import merge_multilingual_sources as merger

ROOT = Path(__file__).resolve().parents[1]
NEW_NAMES = {'New Naratif', 'Project Multatuli', 'Prachatai English', 'Afrique XXI',
             'Amandla!', 'The Public Source', 'Daraj', 'Haïti Liberté',
             'Pikara Magazine', 'La tinta'}


def merged_configuration():
    source = (ROOT / 'aggregate.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    mapping = ast.literal_eval(next(n.value for n in tree.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'quellen' for t in n.targets)))
    namespace = {'quellen': copy.deepcopy(mapping)}
    block = source[source.index(merger.START):source.index(merger.END)]
    exec(compile(block, 'reviewed-source-block', 'exec'), namespace)
    return mapping, namespace['quellen']


class SourceRefresh(unittest.TestCase):
    def test_ten_additions_are_unique_and_preserve_existing_endpoint_identities(self):
        original, merged = merged_configuration()
        rows = [r for group in merged.values() for r in group]
        for name in NEW_NAMES:
            self.assertEqual(sum(row['name'] == name for row in rows), 1, name)
        old_pairs = {(r['name'], r['url']) for group in original.values() for r in group}
        new_pairs = {(r['name'], r['url']) for r in rows}
        self.assertTrue(old_pairs <= new_pairs)

    def test_new_sources_admit_only_https_publisher_metadata(self):
        _, merged = merged_configuration()
        rows = [r for group in merged.values() for r in group if r['name'] in NEW_NAMES]
        for feed in rows:
            self.assertEqual(feed['importMode'], 'metadata-only')
            result = metadata_article(feed, {'title': 'Public headline',
                'link': feed['homepage'] + 'checked-story/', 'published': '2025-03-01',
                'summary': 'FOREIGN SUMMARY', 'content': [{'value': 'FOREIGN FULL TEXT'}],
                'image': 'https://foreign.example/image.jpg'}, feed['categories'][0])
            self.assertIsNotNone(result, feed['name'])
            self.assertEqual(result['pubDate'], '2025-03-01')
            self.assertFalse(result['contentComplete'])
            self.assertEqual(result['image'], '')
            self.assertEqual(result['images'], [])
            self.assertNotIn('FOREIGN', str(result))
            for link in ['https://foreign.example/story', feed['homepage'].replace('https:', 'http:') + 'story']:
                self.assertIsNone(metadata_article(feed, {'title': 'Other', 'link': link}, feed['categories'][0]))
            indexed = normalize_record(feed, origin='aggregate.py', inherited_category=feed['categories'][0])
            self.assertTrue(indexed['active'])
            self.assertEqual(indexed['importMode'], 'metadata-only')

    def test_mixed_language_publisher_does_not_assign_every_item_a_guessed_language(self):
        registry = json.loads((ROOT / 'multilingual-source-registry.json').read_text(encoding='utf-8'))
        haiti = next(r for r in registry['sources'] if r['name'] == 'Haïti Liberté')
        self.assertEqual(haiti['languages'][0], 'und')
        self.assertTrue({'fr', 'ht', 'en'} <= set(haiti['languages']))

    def test_ill_will_uses_publisher_feed_without_changing_source_identity(self):
        raw = {'name': 'Ill Will', 'url': 'https://illwill.com/feed'}
        reviewed = reviewed_source(raw)
        self.assertEqual(reviewed['url'], raw['url'])
        self.assertEqual(request_url(raw), 'https://illwill.com/feed.xml')
        self.assertEqual(reviewed['endpointReviewedAt'], '2026-10-28')
        self.assertEqual(reviewed['importMode'], 'metadata-only')
        indexed = normalize_record(raw, origin='aggregate.py', inherited_category='America')
        self.assertEqual(indexed['url'], raw['url'])
        self.assertEqual(indexed['requestUrl'], 'https://illwill.com/feed.xml')

    def test_radical_socialist_matches_only_reviewed_legacy_query(self):
        old = 'http://www.radicalsocialist.in/index.php?format=feed&type=rss'
        reviewed = reviewed_source({'name': 'Radical Socialist (India)', 'url': old})
        self.assertEqual(reviewed['url'], old)
        self.assertEqual(reviewed['requestUrl'], 'https://radicalsocialist.in/feed/')
        self.assertEqual(reviewed['homepage'], 'https://radicalsocialist.in/')
        self.assertEqual(reviewed['languages'], ['en'])
        self.assertEqual(reviewed['endpointReviewedAt'], '2026-10-28')
        indexed = normalize_record({'name': 'Radical Socialist (India)', 'url': old}, origin='aggregate.py', inherited_category='Asia')
        self.assertEqual(indexed['url'], old)
        self.assertEqual(indexed['requestUrl'], 'https://radicalsocialist.in/feed/')
        for url in [old + '&tracking=1', old + '#fragment', old.replace('type=rss', 'type=atom'),
                    old.replace('format=feed&type=rss', 'type=rss&format=feed'),
                    old.replace('radicalsocialist.in', 'evil.example'),
                    old.replace('www.radicalsocialist.in', 'user:pass@www.radicalsocialist.in'),
                    old.replace('www.radicalsocialist.in', 'www.radicalsocialist.in:8443')]:
            self.assertNotIn('requestUrl', reviewed_source({'url': url}), url)

    def test_queries_do_not_broaden_existing_transport_aliases_or_revalidate_old_reviews(self):
        raw = {'url': 'https://antifa-bern.ch/feed/'}
        self.assertEqual(reviewed_source(raw)['endpointReviewedAt'], '2026-10-24')
        self.assertNotIn('requestUrl', reviewed_source({'url': raw['url'] + '?unexpected=1'}))
        self.assertNotIn('requestUrl', reviewed_source({'url': 'https://illwill.com/feed?unexpected=1'}))
        self.assertNotIn('requestUrl', reviewed_source({'url': 'https://illwill.com/feed#fragment'}))

    def test_retired_endpoint_failure_does_not_disable_new_reviewed_transport(self):
        tree = ast.parse((ROOT / 'aggregate.py').read_text(encoding='utf-8'))
        selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name in {'source_key', 'fast_source_is_eligible'}]
        scope = {'safe_lower': lambda value: str(value or '').strip().lower()}
        exec(compile(ast.Module(body=selected, type_ignores=[]), 'aggregate.py', 'exec'), scope)
        eligible = scope['fast_source_is_eligible']
        for name, url in [('Ill Will', 'https://illwill.com/feed'),
                          ('Radical Socialist (India)', 'http://www.radicalsocialist.in/index.php?format=feed&type=rss')]:
            feed = reviewed_source({'name': name, 'url': url})
            failed = {'name': name, 'url': url, 'ok': False,
                      'detailedState': 'permanently_broken', 'consecutiveFailures': 10}
            by_url = {url.lower().rstrip('/'): failed}
            self.assertTrue(eligible(feed, {name.lower(): failed}, by_url))
            failed['requestUrl'] = feed['requestUrl']
            self.assertFalse(eligible(feed, {name.lower(): failed}, by_url))

    def test_existing_karapatan_topic_override_survives_additive_enrichment(self):
        original, merged = merged_configuration()
        existing = next(row for group in original.values() for row in group
                        if row['name'] == 'Karapatan (Human Rights)')
        expected = {'https://www.karapatan.org/5561/': {
            'title': 'Primer on Desaparecidos', 'topics': ['Anti-Rep & Prisons']}}
        self.assertEqual(existing['metadataTopicOverrides'], expected)
        current = next(row for group in merged.values() for row in group
                       if row['name'] == existing['name'])
        self.assertEqual(current['metadataTopicOverrides'], expected)
        # Exercise registry-to-existing-source propagation rather than relying
        # only on the older literal source table already carrying the value.
        for group in original.values():
            for row in group:
                if row['name'] == existing['name']:
                    row.pop('metadataTopicOverrides', None)
        namespace = {'quellen': original}
        source = (ROOT / 'aggregate.py').read_text(encoding='utf-8')
        block = source[source.index(merger.START):source.index(merger.END)]
        exec(compile(block, 'reviewed-topic-enrichment', 'exec'), namespace)
        enriched = next(row for group in namespace['quellen'].values() for row in group
                        if row['name'] == existing['name'])
        self.assertEqual(enriched.get('metadataTopicOverrides'), expected)
        article = metadata_article(enriched, {
            'title': 'Primer on Desaparecidos',
            'link': 'https://www.karapatan.org/5561/'}, 'Asia')
        self.assertEqual(article['primaryTopic'], 'Anti-Rep & Prisons')
        self.assertEqual(article['importMode'], 'metadata-only')

    def test_additive_merge_is_idempotent(self):
        registry = json.loads((ROOT / 'multilingual-source-registry.json').read_text(encoding='utf-8'))
        original_target = merger.AGGREGATE
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'aggregate.py'
            target.write_text((ROOT / 'aggregate.py').read_text(encoding='utf-8'), encoding='utf-8')
            merger.AGGREGATE = target
            try:
                before = target.read_bytes()
                self.assertFalse(merger.patch_aggregate(registry))
                self.assertEqual(target.read_bytes(), before)
            finally:
                merger.AGGREGATE = original_target


if __name__ == '__main__':
    unittest.main()
