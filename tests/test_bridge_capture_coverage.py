"""Private fail-closed bootstrap coverage tests; no publication or network."""
import copy
import unittest
from datetime import datetime, timedelta, timezone
from build_source_archive import validate_capture_archive_coverage as validate
from news_archive_capture import merge_capture_rows, HISTORY


class CaptureCoverageTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 14, tzinfo=timezone.utc)
        self.old = dict(link='https://example.org/old', title='Old article',
                        quelleName='Example', pubDate=self.now.isoformat(),
                        content='Complete original body ' * 300 + 'END', contentComplete=True)

    def check(self, capture, previous=None, policies=None):
        return validate(capture, [self.old] if previous is None else previous,
                        [] if policies is None else policies, self.now)

    def test_news_only_seed_reentry_rejected(self):
        other = dict(self.old, link='https://example.org/new', title='Other')
        seed = merge_capture_rows([], [other], [], now=self.now)
        partial = dict(self.old, content=self.old['content'][:1200], contentComplete=False)
        replay = merge_capture_rows(seed, [partial], [], now=self.now)
        with self.assertRaisesRegex(ValueError, 'downgraded to partial'):
            self.check(replay)

    def test_missing_seed_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing'):
            self.check([])

    def test_union_seed_passes_and_blocks_partial_reentry(self):
        seed = merge_capture_rows([self.old], [], [], now=self.now)
        self.check(seed)
        with self.assertRaisesRegex(ValueError, 'changed to partial'):
            merge_capture_rows(seed, [dict(self.old, content='excerpt', contentComplete=False)], [], now=self.now)

    def test_new_complete_revision_requires_validated_history(self):
        new = dict(self.old, content='New complete body ' * 400)
        with self.assertRaisesRegex(ValueError, 'lacks verified'):
            self.check([new])
        revised = merge_capture_rows([self.old], [new], [], now=self.now)
        original = copy.deepcopy(revised)
        self.check(revised)
        self.assertEqual(revised, original)
        revised[0][HISTORY][0]['bodySha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.check(revised)

    def test_wrong_identity_and_future_history_rejected(self):
        with self.assertRaisesRegex(ValueError, 'mismatched'):
            self.check([dict(self.old, quelleName='Other')])
        revised = merge_capture_rows([self.old], [dict(self.old, content='New body')], [], now=self.now)
        revised[0][HISTORY][0]['capturedAt'] = (self.now + timedelta(days=1)).isoformat()
        with self.assertRaises(ValueError):
            self.check(revised)

    def test_withdrawal_and_metadata_pass_without_history(self):
        for fields in [dict(status='withdrawn'), dict(importMode='metadata-only')]:
            capture = merge_capture_rows([self.old], [dict(self.old, **fields)], [], now=self.now)
            self.check(capture)
            self.assertNotIn(HISTORY, capture[0])
            self.assertNotIn('Complete original', capture[0]['content'])

    def test_current_source_restriction_and_expiry(self):
        self.check([], policies=[dict(name='Example', importMode='disabled')])
        self.check([], policies=[dict(name='Example', importMode='metadata-only', homepage='https://example.org')])
        self.check([], previous=[dict(self.old, pubDate=(self.now-timedelta(days=31)).isoformat())])
        with self.assertRaises(ValueError):
            self.check([], policies=[dict(name='Example', status='disabled')])

    def test_exact_body_with_false_complete_not_promoted(self):
        with self.assertRaisesRegex(ValueError, 'downgraded'):
            self.check([dict(self.old, contentComplete=False)])

    def test_projected_whitespace_and_duplicates(self):
        self.check([dict(self.old, content='  '+self.old['content']+'\n')])
        with self.assertRaisesRegex(ValueError, 'Ambiguous previous'):
            self.check([self.old], previous=[self.old, dict(self.old, quelleName='Other')])


def test_cli_missing_archive_seed_fails_before_any_write():
    from test_v1_bridge import BridgeTests
    fixture = BridgeTests()
    fixture.setUp()
    try:
        capture = fixture.read('news-archive-capture.json')
        missing = next(r['link'] for r in fixture.all_active() if r.get('contentComplete') is True)
        fixture.put('news-archive-capture.json', [r for r in capture if r['link'] != missing])
        before = fixture.snapshot()
        with unittest.TestCase().assertRaisesRegex(ValueError, 'Capture missing'):
            fixture.run_builder()
        assert fixture.snapshot() == before
    finally:
        fixture.doCleanups()


class ClassificationSyncTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        from news_archive_capture import capture_news_archive
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'capture.json'
        self.now = datetime.now(timezone.utc)
        self.row = dict(link='https://example.org/a', title='Exact article',
                        quelleName='Example', pubDate=self.now.isoformat(),
                        content='Full exact body', contentComplete=True,
                        categories=['Europe'], primaryRegion='Europe', primaryTopic='Movement News',
                        secondaryTopics=[], classificationConfidence=0.3,
                        classificationMethod='old', editorialReview=True,
                        editorialReviewReasons=['old'])
        self.other = dict(self.row, link='https://example.org/outside', title='Outside index')
        capture_news_archive([self.row, self.other], self.path, [], allow_initialize=True)

    def sync(self, rows, policies=None):
        from news_archive_capture import sync_capture_classification
        return sync_capture_classification(rows, self.path, [] if policies is None else policies)

    def test_only_classifier_fields_update_and_idempotence(self):
        from news_archive_capture import capture_news_archive, read_capture, public_capture_rows
        updated = dict(self.row, content='A newer full body')
        capture_news_archive([updated], self.path, [])
        before = read_capture(self.path)
        history = next(r[HISTORY] for r in before if r['link'] == updated['link'])
        current = dict(updated, classificationConfidence=0.9, classificationMethod='new',
                       editorialReview=False, editorialReviewReasons=[])
        result = self.sync([current])
        actual = next(r for r in result if r['link'] == current['link'])
        self.assertEqual(actual[HISTORY], history)
        self.assertEqual(public_capture_rows([actual])[0], current)
        self.assertEqual(next(r for r in result if r['link'] == self.other['link']), self.other)
        raw = self.path.read_bytes()
        self.sync([current])
        self.assertEqual(self.path.read_bytes(), raw)

    def test_non_classifier_changes_fail_before_write(self):
        changes = {'link': 'https://example.org/other', 'title': 'Other', 'quelleName': 'Other',
                   'pubDate': (self.now + timedelta(seconds=1)).isoformat(),
                   'content': 'Other body', 'contentComplete': False, 'webFeedTruncated': True,
                   'author': 'Unexpected', 'importMode': 'metadata-only', 'rightsReview': 'other',
                   'image': 'https://example.org/image.jpg'}
        before = self.path.read_bytes()
        for field, value in changes.items():
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.sync([dict(self.row, **{field: value})])
            self.assertEqual(self.path.read_bytes(), before)
        # JSON bool and numeric flags must not compare equal by Python coercion.
        with self.assertRaises(ValueError):
            self.sync([dict(self.row, contentComplete=1)])
        self.assertEqual(self.path.read_bytes(), before)

    def test_policy_restrictions_cannot_be_bypassed(self):
        before = self.path.read_bytes()
        for policy in [dict(name='Example', importMode='disabled'),
                       dict(name='Example', importMode='metadata-only', homepage='https://example.org')]:
            with self.assertRaises(ValueError): self.sync([self.row], [policy])
            self.assertEqual(self.path.read_bytes(), before)

    def test_metadata_policy_classification_has_priority(self):
        from news_archive_capture import capture_news_archive, public_capture_rows
        from source_import_policy import restrict_existing_article
        policy = dict(name='Example', status='approved', importMode='metadata-only',
                      homepage='https://example.org', categories=['Europe', 'Movement News'])
        admitted = restrict_existing_article(self.row, [policy])
        capture_news_archive([admitted], self.path, [policy])
        classified = dict(admitted, classificationConfidence=0.99,
                          classificationMethod='classifier', editorialReview=False,
                          editorialReviewReasons=[], primaryTopic='No War')
        result = self.sync([classified], [policy])
        actual = next(r for r in result if r['link'] == admitted['link'])
        self.assertEqual(public_capture_rows([actual])[0], restrict_existing_article(classified, [policy]))
        self.assertFalse(actual['contentComplete'])
        self.assertNotEqual(actual['content'], self.row['content'])

    def test_duplicate_invalid_and_provenance_inputs_fail_atomically(self):
        before = self.path.read_bytes()
        cases = [[self.row, self.row], [dict(self.row, editorialReview='yes')],
                 [dict(self.row, classificationConfidence=float('nan'))],
                 [dict(self.row, categories='Europe')], [dict(self.row, capturePreviousRevisions=[])]]
        missing = dict(self.row); missing.pop('classificationMethod'); cases.append([missing])
        for rows in cases:
            with self.assertRaises(ValueError): self.sync(rows)
            self.assertEqual(self.path.read_bytes(), before)

    def test_classification_growth_keeps_capture_byte_limit(self):
        from unittest.mock import patch
        before = self.path.read_bytes()
        changed = dict(self.row, editorialReviewReasons=['x' * 2000])
        with patch('news_archive_capture.MAX_CAPTURE_BYTES', len(before) + 50):
            with self.assertRaisesRegex(ValueError, 'byte limit'):
                self.sync([changed])
        self.assertEqual(self.path.read_bytes(), before)

    def test_no_implicit_bootstrap(self):
        self.path.unlink()
        with self.assertRaisesRegex(ValueError, 'explicit bootstrap'): self.sync([self.row])
        self.assertFalse(self.path.exists())


def test_classification_survives_builder_and_verify():
    from test_v1_bridge import BridgeTests
    from news_archive_capture import sync_capture_classification, CLASSIFICATION_FIELDS
    fixture = BridgeTests(); fixture.setUp()
    try:
        rows = fixture.read('news.json')
        for row in rows:
            row.update(categories=['Europe', 'Labor Struggles'], primaryRegion='Europe',
                       primaryTopic='Labor Struggles', secondaryTopics=[], classificationConfidence=0.91,
                       classificationMethod='post-aggregation-classifier', editorialReview=False,
                       editorialReviewReasons=[])
        fixture.put('news.json', rows)
        sync_capture_classification(rows, fixture.root / 'news-archive-capture.json', [])
        from build_web_feeds import prepare
        fixture.put('news-feed.json', prepare(rows[:500], limit=500, content_limit=4500, preserve_order=True))
        fixture.run_builder(); fixture.run_builder(verify=True)
        for name, actual in [('news', fixture.read('news.json')),
                             ('quick', fixture.read('news-feed.json')),
                             ('archive', fixture.all_active())]:
            by_link = {row['link']: row for row in actual}
            for original in rows:
                if original['link'] not in by_link: continue
                assert all(by_link[original['link']].get(field) == original[field]
                           for field in CLASSIFICATION_FIELDS), (name, original['link'])
    finally:
        fixture.doCleanups()


def test_classification_sync_workflow_order():
    from pathlib import Path
    workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/update.yml').read_text()
    assert workflow.index('python reclassify_news_categories.py') < workflow.index('sync_capture_classification(')
    assert workflow.index('sync_capture_classification(') < workflow.index('WRN_FEED_TARGETS="news,events,status"')
