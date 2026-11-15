"""Exercise actual side-writer shell blocks; all Git remotes are local fixtures."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / '.github/workflows'
MEDIA = ('video-feed.json', 'video-health.json', 'library-feed.json', 'library-health.json')
PROTECTED = ('news.json', 'news-feed.json', 'feed-status.json', 'news-archive-capture.json',
             'news-archive-manifest.json', 'news-archive/source.json',
             'news-archive/bridge-detail-' + 'a' * 64 + '.json')


def block(filename, step):
    text = (WORKFLOWS / filename).read_text()
    tail = text.split('      - name: ' + step + '\n', 1)[1]
    tail = tail.split('\n      - ', 1)[0]
    script = tail.split('        run: |\n', 1)[1]
    return '\n'.join(line[10:] if line.startswith('          ') else line
                     for line in script.splitlines()) + '\n'


def run(*args, cwd, check=True):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=check,
                          env=dict(os.environ, GITHUB_REF='refs/heads/main',
                                   GITHUB_REF_NAME='main', WRN_PUSH_ATTEMPTS='1'))


def inventory(root):
    return {str(p.relative_to(root)): ('symlink:' + os.readlink(p) if p.is_symlink()
            else hashlib.sha256(p.read_bytes()).hexdigest())
            for p in root.rglob('*') if p.is_symlink() or p.is_file()}


class WorkflowInventory(unittest.TestCase):
    def test_only_reviewed_workflows_can_generate_news(self):
        actual = {p.name for p in WORKFLOWS.glob('*.yml')
                  if re.search(r'\bpython(?:3)?\s+(?:aggregate|build_source_archive|build_web_feeds|reclassify_news_categories)\.py\b', p.read_text())}
        self.assertEqual(actual, {'update-fast.yml', 'update.yml', 'merge-multilingual-sources.yml'})

    def test_media_is_read_only_for_news_and_keeps_validator(self):
        text = (WORKFLOWS / 'update-media-library.yml').read_text()
        self.assertNotIn('build_source_archive.py', text)
        self.assertNotIn('git add -A news-archive', text)
        self.assertNotIn('news-archive-manifest.json', text)
        self.assertIn('run: python scripts/validate_media_library.py', text)
        self.assertIn('run: node scripts/build_video_feed.js --check-network', text)
        self.assertIn('run: python aggregate_libraries.py', text)

    def test_guard_precedes_every_install_and_mutation(self):
        text = (WORKFLOWS / 'merge-multilingual-sources.yml').read_text()
        guard = text.index('name: Legacy-Quellenmerge gegen aktive Bridge absichern')
        self.assertIn('ref: main', text[:guard])
        for command in ('name: Python einrichten', 'pip install', 'python merge_multilingual_sources.py',
                        'python aggregate.py', 'python build_web_feeds.py', 'git add'):
            self.assertLess(guard, text.index(command))
        self.assertIn('tests/test_bridge_side_writers.py', (WORKFLOWS / 'quality-gate.yml').read_text())


class CombinedSourceGuard(unittest.TestCase):
    def check_case(self, mutate, blocked=True):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'news-archive').mkdir()
            (root / 'news-archive/source.json').write_text('[]\n')
            (root / 'news-archive-manifest.json').write_text(json.dumps({'sources': [
                {'id': 'source', 'name': 'Source', 'path': 'news-archive/source.json'}]}))
            (root / 'aggregate.py').write_text('# original source configuration\n')
            (root / 'news.json').write_text('["existing news"]\n')
            mutate(root)
            before = inventory(root)
            script = block('merge-multilingual-sources.yml', 'Legacy-Quellenmerge gegen aktive Bridge absichern')
            # The sentinel represents the first source mutation in the following step.
            result = run('bash', '-c', script + '\nprintf mutated > mutation-sentinel\n', cwd=root, check=False)
            if blocked:
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse((root / 'mutation-sentinel').exists())
                self.assertEqual(inventory(root), before)
            else:
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual((root / 'mutation-sentinel').read_text(), 'mutated')
                (root / 'mutation-sentinel').unlink()
                self.assertEqual(inventory(root), before)

    def test_valid_legacy_basis_can_continue(self):
        self.check_case(lambda root: None, blocked=False)

    def test_capture_valid_or_corrupt_is_blocked_without_reading(self):
        for payload in ('[]', '{invalid', ''):
            with self.subTest(payload=payload):
                self.check_case(lambda root: (root / 'news-archive-capture.json').write_text(payload))

    def test_capture_directory_is_blocked(self):
        self.check_case(lambda root: (root / 'news-archive-capture.json').mkdir())

    def test_capture_symlinks_including_broken_are_blocked(self):
        for target in ('news.json', 'missing-target'):
            with self.subTest(target=target):
                self.check_case(lambda root: (root / 'news-archive-capture.json').symlink_to(target))

    def test_bridge_manifest_without_capture_is_blocked(self):
        markers = ({'id': 'source-bridge-v1'}, {'path': 'news-archive/source-bridge-v1.json'},
                   {'legacyId': 'source'}, {'legacyPath': 'news-archive/source.json'},
                   {'legacyPackageSha256': 'a' * 64})
        for marker in markers:
            with self.subTest(marker=marker):
                self.check_case(lambda root: (root / 'news-archive-manifest.json').write_text(
                    json.dumps({'sources': [{'id': 'source', **marker}]})))

    def test_detail_namespace_without_capture_is_blocked(self):
        for name in ('bridge-detail-' + 'a' * 64 + '.json', 'source-bridge-v1.json', 'details'):
            with self.subTest(name=name):
                self.check_case(lambda root: (root / 'news-archive' / name).write_text('[]'))

    def test_broken_detail_symlink_is_blocked(self):
        self.check_case(lambda root: (root / 'news-archive/details').symlink_to('missing'))

    def test_unreadable_manifest_shape_is_blocked(self):
        for payload in ('{invalid', '[]', '{}', '{"sources": []}', '{"sources": [1]}'):
            with self.subTest(payload=payload):
                self.check_case(lambda root: (root / 'news-archive-manifest.json').write_text(payload))

    def test_missing_manifest_is_blocked(self):
        self.check_case(lambda root: (root / 'news-archive-manifest.json').unlink())

    def test_manifest_symlink_is_blocked(self):
        def mutate(root):
            (root / 'news-archive-manifest.json').unlink()
            (root / 'news-archive-manifest.json').symlink_to('news.json')
        self.check_case(mutate)

    def test_archive_symlink_is_blocked(self):
        def mutate(root):
            (root / 'news-archive').rename(root / 'real-archive')
            (root / 'news-archive').symlink_to('real-archive', target_is_directory=True)
        self.check_case(mutate)


class MediaPublication(unittest.TestCase):
    def fixture(self, root):
        remote, work = root / 'remote.git', root / 'work'
        run('git', 'init', '--bare', str(remote), cwd=root)
        work.mkdir()
        run('git', 'init', '-b', 'main', cwd=work)
        run('git', 'config', 'user.name', 'fixture', cwd=work)
        run('git', 'config', 'user.email', 'fixture@example.invalid', cwd=work)
        for name in (*MEDIA, *PROTECTED):
            path = work / name
            path.parent.mkdir(exist_ok=True, parents=True)
            path.write_text(json.dumps({'fixture': name}) + '\n')
        shutil.copy2(ROOT / 'wrn-safe-push.sh', work / 'wrn-safe-push.sh')
        run('git', 'add', '.', cwd=work)
        run('git', 'commit', '-m', 'fixture baseline', cwd=work)
        run('git', 'remote', 'add', 'origin', str(remote), cwd=work)
        run('git', 'push', 'origin', 'main', cwd=work)
        base = run('git', 'rev-parse', 'HEAD', cwd=work).stdout.strip()
        return work, remote, base

    def test_actual_publication_changes_only_four_media_paths(self):
        with tempfile.TemporaryDirectory() as name:
            work, remote, base = self.fixture(Path(name))
            protected = {p: (work / p).read_bytes() for p in PROTECTED}
            for path in MEDIA:
                (work / path).write_text('["new media"]\n')
            result = run('bash', '-c', block('update-media-library.yml', 'Geprüfte Ausgaben veröffentlichen'), cwd=work, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            paths = run('git', 'diff', '--name-only', base, 'refs/heads/main', cwd=remote).stdout.splitlines()
            self.assertEqual(set(paths), set(MEDIA))
            for path, data in protected.items():
                self.assertEqual((work / path).read_bytes(), data)
                self.assertEqual(run('git', 'show', 'refs/heads/main:' + path, cwd=remote).stdout.encode(), data)

    def test_unstaged_news_change_still_blocks_remote_push(self):
        with tempfile.TemporaryDirectory() as name:
            work, remote, base = self.fixture(Path(name))
            (work / MEDIA[0]).write_text('["new media"]\n')
            (work / 'news.json').write_text('["unexpected news mutation"]\n')
            protected = {p: (work / p).read_bytes() for p in PROTECTED}
            result = run('bash', '-c', block('update-media-library.yml', 'Geprüfte Ausgaben veröffentlichen'), cwd=work, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('nicht sauber', result.stdout)
            self.assertEqual(run('git', 'rev-parse', 'refs/heads/main', cwd=remote).stdout.strip(), base)
            for path, data in protected.items():
                self.assertEqual((work / path).read_bytes(), data)

    def test_pre_staged_news_cannot_leak_into_media_commit(self):
        with tempfile.TemporaryDirectory() as name:
            work, remote, base = self.fixture(Path(name))
            (work / MEDIA[0]).write_text('["new media"]\n')
            (work / 'news.json').write_text('["unexpected staged news"]\n')
            run('git', 'add', 'news.json', cwd=work)
            result = run('bash', '-c', block('update-media-library.yml', 'Geprüfte Ausgaben veröffentlichen'), cwd=work, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Unerwartet vorgemerkte', result.stdout)
            self.assertEqual(run('git', 'rev-parse', 'HEAD', cwd=work).stdout.strip(), base)
            self.assertEqual(run('git', 'rev-parse', 'refs/heads/main', cwd=remote).stdout.strip(), base)


if __name__ == '__main__':
    unittest.main()
