import json,unittest
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]

class RecoveredRadioCatalog(unittest.TestCase):
 def test_verified_official_candidates_reach_both_catalogs(self):
  proof=json.loads((ROOT/'docs/LIVE-RADIO-RECOVERY-2026-10-15.json').read_text(encoding='utf-8'))
  source=json.loads((ROOT/'radio-sources.json').read_text(encoding='utf-8'));runtime=json.loads((ROOT/'radio-stations.json').read_text(encoding='utf-8'))
  self.assertEqual({s['id'] for s in source},{s['id'] for s in runtime});self.assertGreaterEqual(len(runtime),28)
  self.assertEqual(len(proof['newVerifiedHttpsBindings']),10)
  for sid,evidence in proof['newVerifiedHttpsBindings'].items():
   self.assertEqual(evidence['status'],200);self.assertTrue(evidence['contentType'].startswith(('audio/','application/ogg')))
   self.assertEqual(urlsplit(evidence['url']).scheme,'https');self.assertFalse(urlsplit(evidence['url']).username);self.assertTrue(evidence['officialEvidenceUrl'].startswith('https://'))
   for catalog in [source,runtime]:self.assertIn(evidence['url'],next(s for s in catalog if s['id']==sid)['streamCandidates'])
  for row in proof['unresolved']:self.assertIn(row['id'],{s['id'] for s in runtime},'unresolved station is retained as an original link')
  self.assertFalse(proof['playbackTested']);self.assertFalse(proof['audioSaved'])

 def test_existing_zurich_station_survives_public_refresh(self):
  for name in ['radio-sources.json','radio-stations.json']:
   rows=json.loads((ROOT/name).read_text(encoding='utf-8'))
   self.assertEqual(len(rows),29);self.assertEqual(len({s['id'] for s in rows}),29)
   zurich=next(s for s in rows if s['id']=='radio-lora-zurich')
   self.assertEqual(zurich['country'],'CH');self.assertIn('https://stream.lora.ch/lora.mp3',zurich['streamCandidates'])
   self.assertIn('keine eigene Rundfunk-Weiterverbreitung',zurich['rightsReview'])
   self.assertNotEqual(zurich['website'],next(s for s in rows if s['id']=='lora')['website'])

if __name__=='__main__':unittest.main()
