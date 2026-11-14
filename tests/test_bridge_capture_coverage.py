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
