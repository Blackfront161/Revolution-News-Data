"""Real Git regression for coupled source-archive publication in the media job."""
from pathlib import Path
import importlib.util
import json
import hashlib
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_source_archive as builder
from build_web_feeds import shorten, clean_text

spec = importlib.util.spec_from_file_location(
    "archive_publication_gate", ROOT / "scripts/validate_source_archive_publication.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class MediaArchivePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(
            prefix="m-", dir=os.environ.get("WRN_TEST_TMPDIR"))
        self.addCleanup(self.temp.cleanup)
        self.outer = Path(self.temp.name).resolve()
        self.root = self.outer / "repo"
        self.root.mkdir()
        self.remote = self.outer / "remote.git"

    def git(self, *args, check=True):
        result = subprocess.run(["git", *map(str, args)], cwd=self.root,
                                capture_output=True, text=True)
        if check and result.returncode:
            self.fail("git " + " ".join(map(str, args)) + "\n" + result.stdout + result.stderr)
        return result

    def prepare(self, already_bound=False):
        self.git("init", "-b", "main")
        self.git("config", "user.name", "WRN test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "core.autocrlf", "false")
        self.git("config", "commit.gpgsign", "false")
        full = dict(quelleName="Fixture source", title="Complete article",
                    link="https://example.org/article",
                    pubDate=datetime.now(timezone.utc).isoformat(),
                    content="Full article paragraph. " * 300, contentComplete=True)
        text, cut = shorten(full["content"], 4500)
        quick = dict(full, content=text, contentComplete=False, webFeedTruncated=cut,
                     webFeedOriginalLength=len(clean_text(full["content"])))
        source_path = "news-archive/" + builder.source_id(full["quelleName"]) + ".json"
        if already_bound:
            quick["detailPath"] = source_path
        for name, data in [
            ("news.json", [full]), ("news-feed.json", [quick]), (source_path, [full]),
            ("news-archive-manifest.json", {"sources": []}),
            ("events.json", [{"marker": "protected legacy event"}]),
            ("events-feed.json", [{"marker": "protected legacy event"}]),
            ("video-feed.json", {"marker": "video"}),
            ("video-health.json", {"marker": "video health"}),
            ("library-feed.json", [{"marker": "library"}]),
            ("library-health.json", {"marker": "library health"}),
        ]:
            builder.write_payload(self.root / name, data)
        status = {"ok": True, "generatedAt": "preserved publication",
                  "news": {"feedCount": 1, "bytes": (self.root / "news-feed.json").stat().st_size},
                  "events": {"revision": "legacy-preserved", "contentLimit": 2800},
                  "calendarV2": {"revision": "v2-preserved", "feedCount": 123}}
        # This formatted status reproduces the calendar producer's layout.
        builder.write_payload(self.root / "feed-status.json", status, pretty=True)
        (self.root / "wrn-safe-push.sh").write_bytes((ROOT / "wrn-safe-push.sh").read_bytes())
        self.git("add", ".")
        self.git("commit", "-m", "Published baseline")
        subprocess.run(["git", "init", "--bare", "-b", "main", str(self.remote)],
                       check=True, capture_output=True)
        self.git("remote", "add", "origin", self.remote.as_posix())
        self.git("push", "-u", "origin", "main")

    def rebuild(self):
        with patch.object(builder, "ROOT", self.root), patch.object(
            sys, "argv", ["build_source_archive.py"]):
            builder.main()

    def stage(self, old=False):
        workflow = (ROOT / ".github/workflows/update-media-library.yml").read_text()
        for line in workflow.splitlines():
            command = line.strip()
            if command.startswith("git add "):
                if old:
                    command = command.replace(" news-feed.json feed-status.json", "")
                self.git(*shlex.split(command)[1:])

    def safe_push(self):
        bash = Path("C:/Program Files/Git/bin/bash.exe")
        executable = str(bash) if bash.exists() else shutil.which("bash")
        self.assertTrue(executable)
        return subprocess.run([executable, "wrn-safe-push.sh", "main"], cwd=self.root,
                              capture_output=True, text=True)

    def install_v2_calendar(self):
        calendar = {"schema": "wrn.calendar-status.v2", "revision": "fixture-v2",
                    "generatedAt": "2026-11-17T07:00:00Z", "state": "partial",
                    "archiveCount": 0, "feedCount": 0,
                    "legacy": {"archiveCount": 0, "feedCount": 0}}
        names = ["events.json", "events-feed.json", "events-v2.json", "events-v2-feed.json"]
        for name in names:
            builder.write_payload(self.root / name, [])
        builder.write_payload(self.root / "calendar-source-cache.json", {})
        builder.write_payload(self.root / "calendar-status.json", calendar)
        from update_calendar import calendar_status_sections
        status = json.loads((self.root / "feed-status.json").read_bytes())
        sections = calendar_status_sections(calendar, 3, 3)
        status.update(sections)
        builder.write_payload(self.root / "feed-status.json", status, pretty=True)
        bound = names + ["calendar-source-cache.json", "calendar-status.json"]
        marker = {"schema": "wrn.calendar-generation.v1", "revision": "fixture-v2",
                  "files": {name: hashlib.sha256((self.root / name).read_bytes()).hexdigest()
                            for name in bound},
                  "eventStatus": sections["events"], "calendarV2Status": sections["calendarV2"]}
        builder.write_payload(self.root / "calendar-generation.json", marker)
        self.git("add", ".")
        self.git("commit", "-m", "Published v2 fixture")

    def test_valid_v2_certificate_and_calendar_status_survive_archive_rebuild(self):
        self.prepare()
        self.install_v2_calendar()
        self.rebuild()
        self.assertTrue(gate.validate(self.root)["protectedInputsUnchanged"])

    def test_preexisting_bad_v2_certificate_blocks_media_publication(self):
        self.prepare()
        self.install_v2_calendar()
        marker_path = self.root / "calendar-generation.json"
        marker = json.loads(marker_path.read_bytes())
        marker["files"]["events-v2.json"] = "0" * 64
        builder.write_payload(marker_path, marker)
        self.git("add", ".")
        self.git("commit", "-m", "Deliberately mixed fixture")
        self.rebuild()
        with self.assertRaisesRegex(ValueError, "Mixed calendar generation"):
            gate.validate(self.root)

    def test_gate_rejects_unsafe_detail_path_without_writing(self):
        self.prepare()
        self.rebuild()
        quick_path = self.root / "news-feed.json"
        rows = json.loads(quick_path.read_bytes())
        rows[0]["detailPath"] = "../foreign.json"
        builder.write_payload(quick_path, rows)
        status = json.loads((self.root / "feed-status.json").read_bytes())
        status["news"]["bytes"] = quick_path.stat().st_size
        builder.write_payload(self.root / "feed-status.json", status)
        before = quick_path.read_bytes()
        with self.assertRaisesRegex(ValueError, "Unsafe source detail path"):
            gate.validate(self.root)
        self.assertEqual(quick_path.read_bytes(), before)

    def test_old_workflow_rejects_format_only_unstaged_status(self):
        self.prepare(already_bound=True)
        before = (self.root / "feed-status.json").read_bytes()
        self.rebuild()
        after = (self.root / "feed-status.json").read_bytes()
        self.assertNotEqual(before, after)
        self.assertEqual(json.loads(before), json.loads(after))
        self.stage(old=True)
        self.git("commit", "-m", "Old incomplete output set")
        self.assertIn(" M feed-status.json", self.git("status", "--porcelain").stdout)
        result = self.safe_push()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Arbeitsbaum ist vor dem Rebase nicht sauber", result.stdout)

    def test_old_workflow_leaves_both_real_builder_outputs_unstaged(self):
        self.prepare()
        self.rebuild()
        self.stage(old=True)
        self.git("commit", "-m", "Old incomplete output set")
        dirty = self.git("status", "--porcelain").stdout
        self.assertIn(" M news-feed.json", dirty)
        self.assertIn(" M feed-status.json", dirty)
        self.assertNotEqual(self.safe_push().returncode, 0)

    def test_new_workflow_commits_outputs_and_actual_safe_push_preserves_them(self):
        for already_bound in [False, True]:
            with self.subTest(formatOnly=already_bound):
                if already_bound:
                    self.root = self.outer / "b"
                    self.root.mkdir()
                    self.remote = self.outer / "r2"
                self.prepare(already_bound)
                self.rebuild()
                before = {n: (self.root / n).read_bytes() for n in
                          ["news-feed.json", "feed-status.json", "news.json",
                           "events.json", "events-feed.json"]}
                checked = gate.validate(self.root)
                self.assertTrue(checked["protectedInputsUnchanged"])
                self.stage()
                self.git("commit", "-m", "Coupled source archive outputs")
                self.assertEqual(self.git("status", "--porcelain").stdout, "")
                result = self.safe_push()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                local = self.git("rev-parse", "HEAD").stdout.strip()
                remote = self.git("ls-remote", "origin", "refs/heads/main").stdout.split()[0]
                self.assertEqual(local, remote)
                self.assertEqual({n: (self.root / n).read_bytes() for n in before}, before)

    def test_gate_rejects_nonbyte_status_changes_and_preserves_worktree(self):
        self.prepare()
        self.rebuild()
        status_path = self.root / "feed-status.json"
        data = json.loads(status_path.read_bytes())
        data["calendarV2"]["revision"] = "corrupted"
        builder.write_payload(status_path, data)
        before = status_path.read_bytes()
        with self.assertRaisesRegex(ValueError, "beyond news.bytes"):
            gate.validate(self.root)
        self.assertEqual(status_path.read_bytes(), before)

    def test_gate_rejects_changed_news_body_or_identity(self):
        self.prepare()
        self.rebuild()
        data = json.loads((self.root / "news-feed.json").read_bytes())
        data[0]["content"] = "Silently shortened"
        builder.write_payload(self.root / "news-feed.json", data)
        with self.assertRaisesRegex(ValueError, "content, identity or order"):
            gate.validate(self.root)

    def test_gate_rejects_protected_calendar_file_change(self):
        self.prepare()
        self.rebuild()
        builder.write_payload(self.root / "events.json", [])
        with self.assertRaisesRegex(ValueError, "protected news/calendar"):
            gate.validate(self.root)

    def test_gate_rejects_unbound_incomplete_or_unsafe_detail(self):
        self.prepare()
        self.rebuild()
        quick = json.loads((self.root / "news-feed.json").read_bytes())
        source = self.root / quick[0]["detailPath"]
        package = json.loads(source.read_bytes())
        package[0]["contentComplete"] = False
        builder.write_payload(source, package)
        with self.assertRaisesRegex(ValueError, "one admitted complete body"):
            gate.validate(self.root)


if __name__ == "__main__":
    unittest.main()
