"""Private transition tests. No network, publication or native operations."""
import copy
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_source_archive as archive
from build_web_feeds import prepare
from news_archive_capture import capture_news_archive
from news_retention import retain_current_sources


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "news-archive").mkdir()
        self.now = datetime.now(timezone.utc) - timedelta(seconds=2)
        self.rows = [self.row(i, large=i < 20) for i in range(2100)]
        self.seed(self.rows)

    def row(self, i, large=False):
        return {"quelleName": "Test Labour" if large else "Test Other",
                "title": f"Article {i}", "link": f"https://publisher.example/story/{i}",
                "pubDate": (self.now - timedelta(minutes=3000-i)).isoformat(),
                "content": (f"Original body {i}. " + "ä😀 line. " * 24000 + f" LAST-{i}") if large else f"Small full body {i}.",
                "contentComplete": True, "categories": ["Labor Struggles"], "kontinent": "Europe"}

    def put(self, name, value):
        archive.write_payload(self.root / name, value)

    def seed(self, rows):
        old = [rows[1], rows[3], rows[20]]
        manifest, chunks = archive.build_source_archives(old, [], generated_at=self.now,
            previous_tracking={"Test Labour": (self.now-timedelta(days=35)).isoformat(),
                               "Test Other": (self.now-timedelta(days=35)).isoformat()})
        for key, value in chunks.items(): self.put(f"news-archive/{key}.json", value)
        self.put("news-archive-manifest.json", manifest)
        self.put("multilingual-source-registry.json", {"sources": []})
        capture_news_archive(rows, self.root / "news-archive-capture.json", [], now=self.now, allow_initialize=True)
        bounded = retain_current_sources(rows, ["Test Labour", "Test Other"], now=self.now)
        self.put("news.json", bounded)
        chosen = [rows[0], *bounded[:499]]
        quick = prepare(chosen, limit=500, content_limit=4500, preserve_order=True)
        self.put("news-feed.json", quick)
        self.put("feed-status.json", {"ok": True, "generatedAt":self.now.isoformat(),
            "lastPublishedAt":self.now.isoformat(), "lastSuccessfulFetchAt":self.now.isoformat(),
            "publication":{"pending":False}, "news":{"feedCount":len(quick),
            "bytes":len(archive.payload_bytes(quick)), "newestArticleAt":archive.newest_article_at(quick)}})

    def run_builder(self, verify=False):
        with patch.object(archive, "ROOT", self.root), patch.object(sys, "argv", ["build_source_archive.py", *( ["--verify-only"] if verify else [])]):
            archive.main()

    def snapshot(self):
        return {str(p.relative_to(self.root)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob("*") if p.is_file()}

    def read(self, name): return json.loads((self.root/name).read_bytes())

    def all_active(self):
        return archive.read_previous_archives(self.root/"news-archive", archive.read_manifest(self.root/"news-archive-manifest.json"))

    def test_overflow_v1_exact_bodies_and_old_cache_identity(self):
        old_path = "news-archive/"+archive.source_id("Test Labour")+".json"
        original = (self.root/old_path).read_bytes()
        self.run_builder()
        manifest = self.read("news-archive-manifest.json")
        self.assertEqual(manifest["schemaVersion"], 1)
        source = next(s for s in manifest["sources"] if s["name"]=="Test Labour")
        self.assertEqual(source["id"], archive.detail_index_id("Test Labour"))
        self.assertEqual((self.root/old_path).read_bytes(), original)
        self.assertEqual(source["legacyPackageSha256"], hashlib.sha256(original).hexdigest())
        active = {row["link"]:row for row in self.all_active()}
        self.assertEqual(len(active), 2100)
        for row in self.rows: self.assertEqual(active[row["link"]]["content"], row["content"])
        for p in (self.root/"news-archive").glob("*.json"):
            self.assertIsInstance(json.loads(p.read_bytes()), list)
            self.assertLessEqual(p.stat().st_size, 4194304)
        self.assertFalse((self.root/"news-archive/details").exists())
        quick = self.read("news-feed.json")[0]
        self.assertTrue(archive.DETAIL_PATH.fullmatch(quick["detailPath"]))
        self.assertNotIn("detailUrl", quick)
        self.assertNotIn("detailRevision", quick)
        active_cards = self.read(source["path"])
        for protected in (self.rows[1], self.rows[3]):
            card = next(row for row in active_cards if row["link"] == protected["link"])
            self.assertEqual(card["content"], protected["content"])
            self.assertTrue(card["contentComplete"])
            self.assertNotIn("detailPath", card)
        before=self.snapshot();self.run_builder(verify=True);self.assertEqual(self.snapshot(),before)

    def test_rollover_replay_keeps_all_captured_bodies(self):
        self.run_builder()
        self.put("news.json", self.rows[100:2100])
        self.put("news-feed.json", prepare(self.rows[-500:], limit=500, content_limit=4500))
        self.run_builder();self.run_builder(verify=True)
        active={r["link"]:r for r in self.all_active()}
        self.assertEqual(len(active),2100)
        for row in self.rows[:100]: self.assertEqual(active[row["link"]]["content"],row["content"])
        before={r["link"]:r["content"] for r in self.all_active()}
        self.run_builder();self.assertEqual({r["link"]:r["content"] for r in self.all_active()},before)

    def test_protected_inline_growth_fails_instead_of_new_network_dependency(self):
        self.run_builder()
        updates = [{**self.rows[i], "content": "Z" * 2200000} for i in (1, 3)]
        capture_news_archive(updates, self.root / "news-archive-capture.json", [])
        self.put("news.json", updates + self.rows[100:2098])
        self.put("news-feed.json", prepare(self.rows[100:600], limit=500, content_limit=4500))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "exceeds.*refusing silent body truncation"):
            self.run_builder()
        self.assertEqual(self.snapshot(), before)

    def test_withdrawal_removes_current_legacy_and_detail(self):
        self.run_builder();deleted_path=self.read("news-feed.json")[0]["detailPath"]
        capture_news_archive([{**self.rows[0],"status":"withdrawn"}], self.root/"news-archive-capture.json", [])
        self.run_builder();self.run_builder(verify=True)
        self.assertNotIn(self.rows[0]["link"],{r["link"] for r in self.all_active()})
        self.assertFalse((self.root/deleted_path).exists())
        self.assertNotIn(self.rows[0]["link"],{r["link"] for r in self.read("news-archive/"+archive.source_id("Test Labour")+".json")})
        self.assertNotIn(self.rows[0]["link"],{r["link"] for r in self.read("news-feed.json")})

    def test_metadata_policy_redacts_all_server_packages(self):
        self.run_builder()
        policies=[{"name":"Test Labour","status":"approved","homepage":"https://publisher.example/","importMode":"metadata-only","rightsReview":"fixture"}]
        self.put("multilingual-source-registry.json",{"sources":policies})
        capture_news_archive([],self.root/"news-archive-capture.json",policies)
        self.run_builder();self.run_builder(verify=True)
        for p in (self.root/"news-archive").glob("*.json"):
            self.assertNotIn(b"Original body",p.read_bytes())
        self.assertEqual(len(list((self.root/"news-archive").glob("bridge-detail-*.json"))),0)

    def test_corrupt_detail_aborts_before_any_other_change(self):
        self.run_builder();detail=next((self.root/"news-archive").glob("bridge-detail-*.json"));detail.write_bytes(detail.read_bytes()+b" ")
        before=self.snapshot()
        with self.assertRaises(ValueError):self.run_builder()
        self.assertEqual(self.snapshot(),before)

    def test_wrong_absolute_reference_aborts(self):
        self.run_builder();manifest=self.read("news-archive-manifest.json");p=next(s["path"] for s in manifest["sources"] if s["name"]=="Test Labour")
        rows=self.read(p);rows[0]["detailUrl"]="https://wrong.example/body.json";self.put(p,rows)
        before=self.snapshot()
        with self.assertRaises(ValueError):self.run_builder()
        self.assertEqual(self.snapshot(),before)

    def test_corrupt_legacy_compatibility_aborts(self):
        self.run_builder();self.put("news-archive/"+archive.source_id("Test Labour")+".json",[])
        before=self.snapshot()
        with self.assertRaises(ValueError):self.run_builder()
        self.assertEqual(self.snapshot(),before)

    def test_missing_capture_never_implicitly_bootstraps(self):
        (self.root/"news-archive-capture.json").unlink();before=self.snapshot()
        with self.assertRaises(ValueError):self.run_builder()
        self.assertEqual(self.snapshot(),before)

    def test_unknown_source_file_aborts_without_deleting(self):
        self.put("news-archive/unowned.json",[self.rows[20]]);before=self.snapshot()
        with self.assertRaises(ValueError):self.run_builder()
        self.assertEqual(self.snapshot(),before)

    def test_single_oversize_body_fails_closed(self):
        rows=[{**self.rows[0],"content":"q"*4194304}]
        with self.assertRaises(ValueError):archive.build_source_archives(rows,[],generated_at=self.now)

    def test_publication_identity_is_not_interchangeable(self):
        full=self.rows[0];quick=prepare([full],limit=1,content_limit=4500)[0]
        self.assertTrue(archive.detail_matches(quick,full))
        for key in ("pubDate","title","quelleName","link"):
            self.assertFalse(archive.detail_matches({**quick,key:quick[key]+"x"},full))

    def test_casefold_source_id_collision_fails_closed(self):
        rows=[{**self.rows[20],"quelleName":"Foo"},{**self.rows[21],"quelleName":"foo"}]
        with self.assertRaisesRegex(ValueError,"source package identity"):
            archive.build_source_archives(rows,[],generated_at=self.now)

    def test_conflicting_previous_url_never_overwrites(self):
        row=self.rows[20]
        for changed in ({**row,"quelleName":"Other Publisher"},{**row,"content":"Conflicting original"}):
            with self.assertRaisesRegex(ValueError,"previous archive identity/revision"):
                archive.build_source_archives([],[],previous_articles=[row,changed],generated_at=self.now)

    def test_previous_identity_cannot_be_reassigned_by_current(self):
        row=self.rows[20]
        with self.assertRaisesRegex(ValueError,"Current/previous article identity"):
            archive.build_source_archives([{**row,"quelleName":"Other Publisher"}],[],previous_articles=[row],generated_at=self.now)

    def test_legacy_excerpts_are_not_inflated_to_full_package(self):
        # Turn the whole legacy Labour file into a bounded old excerpt index.
        old=self.rows[:20]
        manifest=self.read("news-archive-manifest.json")
        source=next(s for s in manifest["sources"] if s["name"]=="Test Labour")
        source["itemCount"]=20;manifest["itemCount"]=21
        self.put("news-archive-manifest.json",manifest)
        self.put(source["path"],[archive.projected_article(r,1400) for r in old])
        self.run_builder();self.run_builder(verify=True)
        legacy=self.read(source["path"])
        self.assertEqual(len(legacy),20)
        self.assertLess((self.root/source["path"]).stat().st_size,60000)
        self.assertTrue(all(r.get("detailUrl","").startswith(archive.PUBLIC_ARCHIVE_BASE) for r in legacy))
        active={r["link"]:r for r in self.all_active()}
        for row in old:self.assertEqual(active[row["link"]]["content"],row["content"])

    def test_publication_requires_real_bound_recent_aggregation(self):
        self.put("aggregate-run-status.json",{"finishedAt":self.now.isoformat(),"mode":"fast"})
        archive.verify_publication_freshness(self.root/"feed-status.json",self.root/"aggregate-run-status.json",now=self.now)
        with self.assertRaises(ValueError):
            archive.verify_publication_freshness(self.root/"feed-status.json",self.root/"aggregate-run-status.json",now=self.now+timedelta(hours=2))
        self.put("aggregate-run-status.json",{"finishedAt":(self.now-timedelta(minutes=1)).isoformat(),"mode":"fast"})
        with self.assertRaises(ValueError):
            archive.verify_publication_freshness(self.root/"feed-status.json",self.root/"aggregate-run-status.json",now=self.now)

    def test_bounded_fallback_cannot_keep_a_restricted_body(self):
        # This row is deliberately inside bounded news (the reserved source row).
        victim=self.rows[19]
        self.assertIn(victim["link"],{r["link"] for r in self.read("news.json")})
        self.run_builder()
        manifest=self.read("news-archive-manifest.json")
        source=next(s for s in manifest["sources"] if s["name"]=="Test Labour")
        cards=self.read(source["path"])
        card=next(r for r in cards if r["link"]==victim["link"])
        card.update(importMode="metadata-only",rightsReview="fixture",sourceHomepage="https://publisher.example/")
        self.put(source["path"],cards)
        self.run_builder();self.run_builder(verify=True)
        for name in ("news.json","news-archive-capture.json"):
            stored=next(r for r in self.read(name) if r["link"]==victim["link"])
            self.assertEqual(stored["importMode"],"metadata-only")
            self.assertNotIn("Original body",stored["content"])
            self.assertNotIn("capturePreviousRevisions",stored)

    def test_bounded_withdrawal_is_removed_and_verify_checks_real_bytes(self):
        victim=self.rows[19];self.run_builder()
        capture_news_archive([{**victim,"deleted":True}],self.root/"news-archive-capture.json",[])
        self.run_builder();self.run_builder(verify=True)
        self.assertNotIn(victim["link"],{r["link"] for r in self.read("news.json")})
        bad=self.read("news.json")+[victim];self.put("news.json",bad);before=self.snapshot()
        with self.assertRaises(ValueError):self.run_builder(verify=True)
        self.assertEqual(self.snapshot(),before)

    def test_new_capture_row_restriction_reaches_quick_feed_in_same_generation(self):
        self.run_builder()
        victim = self.rows[0]
        self.assertIn(victim["link"], {r["link"] for r in self.read("news-feed.json")})
        restricted = {**victim, "importMode": "metadata-only", "rightsReview": "fixture",
                      "sourceHomepage": "https://publisher.example/"}
        capture_news_archive([restricted], self.root / "news-archive-capture.json", [])
        self.run_builder(); self.run_builder(verify=True)
        quick = next(r for r in self.read("news-feed.json") if r["link"] == victim["link"])
        self.assertEqual(quick["importMode"], "metadata-only")
        self.assertNotIn("Original body", quick["content"])
        self.assertNotIn("detailPath", quick)


if __name__ == "__main__": unittest.main()
