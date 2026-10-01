"""Offline contracts for the canonical podcast collector and RDL identity batch."""
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import aggregate_podcasts as collector
from podcast_content_policy import RULES, MODE, metadata_only, project_episode, episode_key

ROOT = Path(__file__).resolve().parents[1]


class PodcastContentPolicyTests(unittest.TestCase):
    def test_existing_catalog_ids_and_restriction(self):
        sources = json.loads((ROOT/'podcast-sources.json').read_text(encoding='utf-8'))
        self.assertEqual(len(sources),len({row['id'] for row in sources}))
        endpoint = next(row for row in sources if row['id']==RULES['endpointId'])
        self.assertEqual(endpoint['canonicalSourceId'],RULES['canonicalSourceId'])
        self.assertEqual(endpoint['episodeIdNamespace'],'None')
        rows = json.loads((ROOT/'podcasts.json').read_text(encoding='utf-8'))
        restricted=[row for row in rows if row['id'] in RULES['restrictedEpisodeIds']]
        self.assertEqual(len(restricted),28)
        for row in restricted:
            self.assertEqual(row['sourceId'],RULES['canonicalSourceId'])
            self.assertEqual(row['contentPolicy'],MODE)
            self.assertFalse(row['audioUrl'] or row['artwork'] or row['description'])

    def test_projection_removes_all_media_aliases(self):
        row=project_episode({'id':RULES['restrictedEpisodeIds'][0],'audioUrl':'audio','candidates':['audio'],
                             'description':'Foreign text','transcript':'Foreign transcript','image':'cover',
                             'episodeUrl':'https://rdl.de/beitrag/test','contentPolicy':'playable'})
        self.assertEqual(row['contentPolicy'],MODE)
        self.assertEqual(row['episodeUrl'],'https://rdl.de/beitrag/test')
        self.assertFalse({'candidates','transcript','image'} & row.keys())
        self.assertFalse(metadata_only({},sources=[{'contentPolicy':MODE,'feedUrl':'invalid'}]))

    def test_metadata_rows_have_distinct_dedup_keys(self):
        rows=[project_episode({'id':identifier}) for identifier in RULES['restrictedEpisodeIds'][:2]]
        self.assertNotEqual(episode_key(rows[0]),episode_key(rows[1]))

    def test_collector_keeps_original_guid_namespace_without_audio(self):
        class Response:
            content=b'<rss version="2.0"><channel><title>RDL</title><item><title>Politik</title><guid>test-guid</guid><link>https://rdl.de/beitrag/test</link><description>Foreign text</description></item></channel></rss>'
            def raise_for_status(self): pass
        source={'id':RULES['endpointId'],'canonicalSourceId':RULES['canonicalSourceId'],
                'episodeIdNamespace':'None','name':'Radio Dreyeckland','language':'de',
                'feedUrl':RULES['feedUrls'][0],'contentPolicy':MODE,'pageAudioFallback':True}
        with patch.object(collector,'discover_feeds',return_value=[]), patch.object(collector.session,'get',return_value=Response()), patch.object(collector,'find_audio_on_page',side_effect=AssertionError('Forbidden media page lookup')):
            rows,feed,errors=collector.source_entries(source)
        self.assertEqual(len(rows),1,errors)
        self.assertEqual(rows[0]['id'],hashlib.sha256(b'None|test-guid').hexdigest()[:24])
        self.assertEqual(rows[0]['sourceId'],RULES['canonicalSourceId'])
        self.assertFalse(rows[0]['audioUrl'] or rows[0]['description'])


if __name__=='__main__': unittest.main()
