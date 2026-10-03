"""Exercise the real save/validation steps against an isolated local Git remote."""

import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ('podcasts.json', 'podcast-archive.json', 'podcast-health.json', 'generated-podcasts.json')


def workflow_step(name):
    source = (ROOT / '.github/workflows/update-podcasts.yml').read_text(encoding='utf-8')
    lines = source.splitlines()
    start = lines.index('      - name: ' + name)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('      - name: ')), len(lines))
    block = lines[start:end]
    body = block[block.index('        run: |') + 1:]
    if any(line and not line.startswith('          ') for line in body):
        raise AssertionError('Unexpected workflow shell indentation: ' + name)
    return '\n'.join(line[10:] if line else '' for line in body) + '\n'


class PodcastPublicationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wrn-podcast-publication-')
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.repo = base / 'checkout'
        self.remote = base / 'remote.git'
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0', GITHUB_REF_NAME='main', WRN_PUSH_ATTEMPTS='1')
        self.bash = shutil.which('bash')
        if os.name == 'nt':
            self.bash = str(Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Git/bin/bash.exe')
        if not self.bash or not Path(self.bash).is_file():
            self.fail('Git Bash/Bash is required; publication regression must not silently skip.')
        self.git('init', '--bare', str(self.remote), cwd=base)
        self.repo.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'WRN isolated test')
        self.git('config', 'user.email', 'test@example.invalid')
        for name in OUTPUTS:
            (self.repo / name).write_text('[]\n', encoding='utf-8')
        (self.repo / 'audio-health.json').write_text('{}\n', encoding='utf-8')
        (self.repo / 'unrelated.json').write_text('{}\n', encoding='utf-8')
        # Keep the production guard byte-for-byte, never replace it with a stub.
        (self.repo / 'wrn-safe-push.sh').write_bytes((ROOT / 'wrn-safe-push.sh').read_bytes())
        self.git('add', '.')
        self.git('commit', '-m', 'baseline')
        self.git('remote', 'add', 'origin', str(self.remote))
        self.git('push', '-u', 'origin', 'main')
        self.before = self.git('--git-dir=' + str(self.remote), 'rev-parse', 'main').stdout.strip()

    def git(self, *args, cwd=None):
        return subprocess.run(['git', *args], cwd=cwd or self.repo, env=self.env, check=True, capture_output=True, text=True, encoding='utf-8')

    def shell(self, script):
        # The workflow uses the installed runner Python; use the test interpreter locally.
        script = re.sub(r'(?m)^(\s*)python ', lambda m: m[1] + shlex.quote(sys.executable.replace('\\', '/')) + ' ', script)
        return subprocess.run([self.bash, '-c', script], cwd=self.repo, env=self.env, capture_output=True, text=True, encoding='utf-8', timeout=30)

    def change_outputs(self):
        for name in OUTPUTS:
            (self.repo / name).write_text(json.dumps([{'id': name}]) + '\n', encoding='utf-8')

    def test_archive_is_published_with_all_outputs_and_optional_health(self):
        self.change_outputs()
        (self.repo / 'audio-health.json').write_text('{"ok":true}\n', encoding='utf-8')
        valid = self.shell(workflow_step('Podcast-Daten prüfen'))
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
        saved = self.shell(workflow_step('Podcast-Daten speichern'))
        self.assertEqual(saved.returncode, 0, saved.stdout + saved.stderr)
        self.assertEqual(self.git('status', '--porcelain').stdout, '')
        for name in (*OUTPUTS, 'audio-health.json'):
            remote_bytes = self.git('--git-dir=' + str(self.remote), 'show', 'main:' + name).stdout
            self.assertEqual(remote_bytes, (self.repo / name).read_text(encoding='utf-8'))

    def test_invalid_or_missing_archive_prevents_commit_and_push(self):
        for archive in ('invalid-json', None):
            with self.subTest(archive=archive):
                self.change_outputs()
                path = self.repo / 'podcast-archive.json'
                if archive is None:
                    path.unlink()
                else:
                    path.write_text(archive, encoding='utf-8')
                combined = workflow_step('Podcast-Daten prüfen') + '\n' + workflow_step('Podcast-Daten speichern')
                result = self.shell(combined)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.git('--git-dir=' + str(self.remote), 'rev-parse', 'main').stdout.strip(), self.before)
                self.assertEqual(self.git('rev-parse', 'HEAD').stdout.strip(), self.before)

    def test_unrelated_change_still_blocks_the_safe_push(self):
        self.change_outputs()
        (self.repo / 'unrelated.json').write_text('{"unexpected":true}\n', encoding='utf-8')
        result = self.shell(workflow_step('Podcast-Daten speichern'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Arbeitsbaum ist vor dem Rebase nicht sauber', result.stdout)
        self.assertEqual(self.git('--git-dir=' + str(self.remote), 'rev-parse', 'main').stdout.strip(), self.before)
        self.assertIn('unrelated.json', self.git('status', '--porcelain').stdout)

    def test_no_change_is_a_noop(self):
        result = self.shell(workflow_step('Podcast-Daten speichern'))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Keine Podcast-Änderungen', result.stdout)
        self.assertEqual(self.git('rev-parse', 'HEAD').stdout.strip(), self.before)


if __name__ == '__main__':
    unittest.main()
