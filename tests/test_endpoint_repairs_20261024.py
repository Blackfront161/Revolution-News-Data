import unittest
from source_endpoint_repairs import REPAIRS, reviewed_source, request_url
from build_sources_registry import normalize_record

class EndpointRepairs(unittest.TestCase):
    def test_partial_run_does_not_count_unchanged_observation_twice(self):
        from source_recovery import apply_history
        raw = {'name':'Offline','url':'https://example.org/feed','status':'error',
               'httpStatus':404,'lastChecked':'2026-10-24T00:00:00+00:00'}
        first, history, _ = apply_history([raw], {})
        second, next_history, _ = apply_history(first, history)
        self.assertEqual(first, second)
        self.assertEqual(history['sources'], next_history['sources'])
    def test_reviewed_alias_preserves_identity_and_restricts_import(self):
        for old,(new,home,language) in REPAIRS.items():
            source={'name':'Example','url':'https://'+old+'/','importMode':'fulltext'}
            repaired=reviewed_source(source)
            self.assertEqual(repaired['url'],source['url'])
            self.assertEqual(request_url(source),new)
            self.assertEqual(repaired['importMode'],'metadata-only')
            self.assertEqual(repaired['homepage'],home)
            self.assertEqual(source['importMode'],'fulltext')
            record=normalize_record(source,origin='test',inherited_category='News')
            self.assertEqual(record['requestUrl'],new)
            self.assertEqual(record['url'],source['url'])
    def test_unreviewed_urls_are_not_rewritten(self):
        for url in ['https://evil.example/feed/','https://perspektive-online.de/other/',
                    'https://perspektive-online.de/feed/?new=1',
                    'https://perspektive-online.de:bad/feed/',
                    'https://user@perspektive-online.de/feed/',
                    'https://perspektive-online.de/feed/#other']:
            self.assertEqual(reviewed_source({'url':url}),{'url':url})

if __name__=='__main__': unittest.main()

