"""Private bridge orchestration/CAS tests; only disposable local Git remotes."""
import os
import copy
import hashlib
import json
from unittest.mock import patch
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'wrn-bridge-safe-push.sh'


def run(*args, cwd=None, check=True, env=None):
    return subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=check)


class WorkflowStructure(unittest.TestCase):
    def test_both_flows_capture_validate_and_pin(self):
        for name in ['update-fast.yml', 'update.yml']:
            with self.subTest(name=name):
                text = (ROOT / '.github/workflows' / name).read_text()
                self.assertIn('ref: main', text)
                self.assertIn('WRN_BRIDGE_BASE_SHA=%s', text)
                self.assertIn('[[ "$GITHUB_REF" == "refs/heads/main" ]]', text)
                self.assertLess(text.index('WRN_BRIDGE_BASE_SHA=%s'), text.index('python aggregate.py'))
                self.assertIn('read_capture(Path("news-archive-capture.json"))', text)
                self.assertLess(text.index('read_capture('), text.index('python aggregate.py'))
                self.assertIn('validate_capture_archive_coverage(capture, previous, policies, datetime.now(timezone.utc))', text)
                self.assertLess(text.index('validate_capture_archive_coverage(capture,'), text.index('python aggregate.py'))
                self.assertNotIn('allow_initialize=True', text)
                self.assertNotIn('allow_bootstrap=True', text)
                self.assertIn('git add news-archive-manifest.json news-archive news-archive-capture.json', text)
                self.assertIn('run: python build_source_archive.py --verify-only', text)
                self.assertLess(text.index('run: python build_source_archive.py --verify-only'), text.index('git commit -m'))
                self.assertIn('bash wrn-bridge-safe-push.sh main "$WRN_BRIDGE_BASE_SHA"', text)
                self.assertNotIn('git rebase', text)
                self.assertNotIn('bash wrn-safe-push.sh', text)
                self.assertIn('group: wrn-main-write', text)
                self.assertIn('cancel-in-progress: false', text)
                self.assertIn('PYTHONDONTWRITEBYTECODE: "1"', text)

    def test_legacy_integrity_gates_remain(self):
        fast = (ROOT / '.github/workflows/update-fast.yml').read_text()
        enrich = (ROOT / '.github/workflows/update.yml').read_text()
        for phrase in ['stoppedForBudget', 'sourcesWithEntries', 'age > 3600', 'publication", {}).get("pending',
                       'WRN_FEED_TARGETS="news,status"', 'git restore -- events.json events-feed.json']:
            self.assertIn(phrase, fast)
        self.assertIn('python tests/validate_app.py', enrich)
        self.assertIn('WRN_FEED_TARGETS="news,events,status"', enrich)
        self.assertIn('news-archive-capture.json', enrich)

    def test_shell_blocks_parse(self):
        for name in ['update-fast.yml', 'update.yml']:
            lines = (ROOT / '.github/workflows' / name).read_text().splitlines()
            for i, line in enumerate(lines):
                if line.strip() != 'run: |':
                    continue
                block = []
                for following in lines[i+1:]:
                    if following and not following.startswith('          '):
                        break
                    block.append(following[10:] if following else '')
                result = subprocess.run(['bash', '-n'], input='\n'.join(block), text=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(result.returncode, 0, (name, i, result.stderr))
        self.assertEqual(run('bash', '-n', str(HELPER), check=False).returncode, 0)


    def test_recovery_is_failure_only_after_normal_publication(self):
        for name, derivation in [('update-fast.yml', 'News-Feed und Status erzeugen'),
                                 ('update.yml', 'Quellenkatalog erzeugen')]:
            with self.subTest(name=name):
                text=(ROOT/'.github/workflows'/name).read_text()
                self.assertIn('id: aggregate',text)
                self.assertIn("always() && failure() && (steps.aggregate.outcome == 'success' || steps.aggregate.outcome == 'failure')",text)
                self.assertIn("always() && steps.capture_recovery_prepare.outcome == 'success'",text)
                self.assertIn('uses: actions/upload-artifact@v4',text)
                self.assertIn('if-no-files-found: error',text)
                self.assertIn('retention-days: 7',text)
                self.assertIn('overwrite: false',text)
                self.assertIn('include-hidden-files: false',text)
                self.assertNotIn('continue-on-error',text)
                self.assertIn('steps.capture_recovery_upload.outputs.artifact-id',text)
                self.assertIn('steps.capture_recovery_upload.outputs.artifact-digest',text)
                self.assertLess(text.index('id: aggregate'),text.index('id: capture_recovery_prepare'))
                self.assertLess(text.index('id: capture_recovery_upload'),text.index('id: capture_recovery_confirm'))
                self.assertLess(text.index('- name: '+derivation),text.index('id: capture_recovery_prepare'))
                self.assertNotIn("success() && steps.capture_recovery_confirm.outcome",text)
                self.assertLess(text.index('bash wrn-bridge-safe-push.sh'),text.index('id: capture_recovery_prepare'))
                self.assertNotIn('actions/download-artifact',text)


    def test_recovery_condition_matrix_and_failure_not_hidden(self):
        for name in ('update-fast.yml','update.yml'):
            text=(ROOT/'.github/workflows'/name).read_text()
            steps=text.split('      - name: ')[1:]
            prepare=next(step for step in steps if 'id: capture_recovery_prepare' in step)
            condition_line=next(line.strip() for line in prepare.splitlines() if line.strip().startswith('if: '))
            expression=condition_line.removeprefix('if: ')[3:-2].strip()
            for failed,outcome,expected in (
                (False,'success',False), # normal commit/push success: zero artifacts
                (False,'skipped',False),
                (True,'skipped',False), # aggregation never ran
                (True,'failure',True), # failed aggregation with valid checkpoint
                (True,'success',True), # build/verify/commit/push (including uncertain) failure
            ):
                condition=expression.replace('always()','True').replace('failure()',str(failed))
                condition=condition.replace('steps.aggregate.outcome',repr(outcome))
                condition=condition.replace('&&','and').replace('||','or')
                self.assertEqual(eval(condition,{'__builtins__':{}}),expected)
            # Recovery success cannot erase the preceding failed step; quota failure
            # adds a failure. There are no continue-on-error or subsequent push steps.
            recovery_index=steps.index(prepare)
            self.assertTrue(all('continue-on-error' not in step for step in steps))
            self.assertFalse(any('wrn-bridge-safe-push' in step
                                 for step in steps[recovery_index:]))
            self.assertEqual([next(line.strip().removeprefix('id: ') for line in step.splitlines() if line.strip().startswith('id: ')) for step in steps[recovery_index:]],
                             ['capture_recovery_prepare','capture_recovery_upload','capture_recovery_confirm'])


class RecoveryPreparation(unittest.TestCase):
    def setUp(self):
        import prepare_capture_recovery as recovery
        self.recovery=recovery
        self.temp=tempfile.TemporaryDirectory(prefix='wrn-capture-recovery-test-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.repo=self.root/'repo';self.repo.mkdir()
        self.output=self.root/'output'
        self.env=dict(os.environ,GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',
                      GIT_AUTHOR_NAME='Recovery test',GIT_AUTHOR_EMAIL='recovery@example.invalid',
                      GIT_COMMITTER_NAME='Recovery test',GIT_COMMITTER_EMAIL='recovery@example.invalid')
        run('git','init','-b','main',cwd=self.repo,env=self.env)
        (self.repo/'base.txt').write_text('base')
        run('git','add','.',cwd=self.repo,env=self.env)
        run('git','commit','-m','test base',cwd=self.repo,env=self.env)
        self.base=run('git','rev-parse','HEAD',cwd=self.repo,env=self.env).stdout.strip()
        self.row={'link':'https://source.test/article','title':'Original title','quelleName':'Source',
                  'pubDate':'2026-11-14T12:00:00Z','content':'Unchanged complete body.',
                  'contentComplete':True}
        self.policies=[{'name':'Source','homepage':'https://source.test/','importMode':'fulltext'}]
        self.write([self.row],self.policies)
        self.args=dict(base_sha=self.base,run_id='12345',run_attempt='2',workflow_sha='a'*40,
                       job='refresh',aggregation_outcome='success')

    def write(self,rows,policies):
        (self.repo/'news-archive-capture.json').write_text(json.dumps(rows,ensure_ascii=False)+'\n')
        (self.repo/'multilingual-source-registry.json').write_text(json.dumps({'sources':policies})+'\n')

    def prepare(self,**changes):
        return self.recovery.prepare_recovery(self.repo,self.output,**(self.args|changes))

    def test_exact_capture_bytes_and_provenance_bound(self):
        before=(self.repo/'news-archive-capture.json').read_bytes()
        result=self.prepare()
        self.assertEqual((self.output/'news-archive-capture.json').read_bytes(),before)
        self.assertEqual(result['generationBaseSha'],self.base)
        self.assertEqual(result['runId'],'12345');self.assertEqual(result['runAttempt'],'2')
        self.assertEqual(result['purpose'],'capture-recovery-only')
        self.assertFalse(result['publicationPerformed']);self.assertFalse(result['automaticRestorePermitted'])
        self.assertEqual(result['freshnessClaim'],'none')
        for name,entry in result['files'].items():
            raw=(self.output/name).read_bytes()
            self.assertEqual(len(raw),entry['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(),entry['sha256'])
        self.assertEqual(json.loads((self.output/'recovery-receipt.json').read_text()),result)
        self.assertEqual((self.repo/'news-archive-capture.json').read_bytes(),before)

    def data_child(self):
        # Policy exists at the generation base and may not change in output commit.
        run('git','add','multilingual-source-registry.json',cwd=self.repo,env=self.env)
        run('git','commit','-m','base policy',cwd=self.repo,env=self.env)
        self.base=run('git','rev-parse','HEAD',cwd=self.repo,env=self.env).stdout.strip()
        self.args['base_sha']=self.base
        run('git','add','news-archive-capture.json',cwd=self.repo,env=self.env)
        run('git','commit','-m','data checkpoint',cwd=self.repo,env=self.env)
        return run('git','rev-parse','HEAD',cwd=self.repo,env=self.env).stdout.strip()

    def test_failed_push_data_child_retained_without_remote_claim(self):
        head=self.data_child()
        result=self.prepare()
        self.assertEqual(result['checkpointHeadSha'],head)
        self.assertEqual(result['remotePublicationState'],'not-established-by-recovery')
        self.assertEqual(result['freshnessClaim'],'none')

    def test_postcommit_modified_capture_rejected(self):
        self.data_child()
        self.write([self.row|{'content':'Changed after commit'}],self.policies)
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_postcommit_modified_policy_rejected(self):
        self.data_child()
        with (self.repo/'multilingual-source-registry.json').open('a') as f:f.write(' ')
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_recovery_nonoutput_commit_rejected(self):
        self.data_child()
        (self.repo/'code.py').write_text('pass')
        run('git','add','code.py',cwd=self.repo,env=self.env)
        run('git','commit','--amend','--no-edit',cwd=self.repo,env=self.env)
        with self.assertRaises(subprocess.CalledProcessError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_recovery_multiple_commits_rejected(self):
        self.data_child()
        (self.repo/'news.json').write_text('[]')
        run('git','add','news.json',cwd=self.repo,env=self.env)
        run('git','commit','-m','second',cwd=self.repo,env=self.env)
        with self.assertRaises(subprocess.CalledProcessError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_recovery_merge_commit_rejected(self):
        head=self.data_child()
        merged=run('git','commit-tree',head+'^{tree}','-p',head,'-p',self.base,'-m','merge',
                   cwd=self.repo,env=self.env).stdout.strip()
        run('git','reset','--hard',merged,cwd=self.repo,env=self.env)
        with self.assertRaises(subprocess.CalledProcessError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_recovery_symlink_output_commit_rejected(self):
        self.data_child()
        (self.repo/'news.json').symlink_to('base.txt')
        run('git','add','news.json',cwd=self.repo,env=self.env)
        run('git','commit','--amend','--no-edit',cwd=self.repo,env=self.env)
        with self.assertRaises(subprocess.CalledProcessError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_failed_aggregation_can_retain_valid_checkpoint(self):
        result=self.prepare(aggregation_outcome='failure')
        self.assertEqual(result['aggregationOutcome'],'failure')
        self.assertEqual(result['freshnessClaim'],'none')

    def test_missing_capture_is_not_bootstrapped(self):
        (self.repo/'news-archive-capture.json').unlink()
        with self.assertRaises((ValueError,FileNotFoundError)):self.prepare()
        self.assertFalse(self.output.exists())

    def test_malformed_capture_not_staged(self):
        (self.repo/'news-archive-capture.json').write_text('not json')
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_duplicate_keys_not_staged(self):
        raw=json.dumps([self.row]).replace('"content":','"content":"unverified", "content":')
        (self.repo/'news-archive-capture.json').write_text(raw)
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_invalid_history_not_staged(self):
        row=copy.deepcopy(self.row)
        row['capturePreviousRevisions']=[{'body':'forged','bodySha256':'0'*64}]
        self.write([row],self.policies)
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_valid_prior_body_hash_preserved(self):
        row=copy.deepcopy(self.row);old='Earlier admitted body.'
        row['capturePreviousRevisions']=[{k:row[k] for k in ('link','title','quelleName','pubDate')}|
             {'body':old,'bodySha256':hashlib.sha256(old.encode()).hexdigest(),
              'capturedAt':'2026-11-14T13:00:00Z','provenance':'prior-validated-capture'}]
        self.write([row],self.policies);self.prepare()
        saved=json.loads((self.output/'news-archive-capture.json').read_text())
        self.assertEqual(saved[0]['capturePreviousRevisions'][0]['body'],old)

    def test_new_metadata_restriction_rejects_old_body(self):
        policies=[{'name':'Source','homepage':'https://source.test/','importMode':'metadata-only','status':'approved'}]
        self.write([self.row],policies)
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_already_restricted_metadata_passes_without_full_body(self):
        from source_import_policy import restrict_existing_article
        policies=[{'name':'Source','homepage':'https://source.test/','importMode':'metadata-only','status':'approved'}]
        row=restrict_existing_article(self.row,policies)
        self.write([row],policies);self.prepare()
        self.assertNotIn(self.row['content'],(self.output/'news-archive-capture.json').read_text())

    def test_withdrawn_source_old_body_rejected(self):
        self.write([self.row],[self.policies[0]|{'status':'withdrawn'}])
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_clean_tombstone_passes(self):
        row={k:self.row[k]for k in ('link','title','quelleName','pubDate')}|{
            'content':'','contentComplete':False,'status':'withdrawn','deleted':True,
            'captureWithdrawnAt':'2026-11-14T13:00:00Z'}
        self.write([row],self.policies);self.prepare()
        self.assertEqual(json.loads((self.output/'news-archive-capture.json').read_text())[0]['content'],'')

    def test_tombstone_cannot_carry_body_or_media(self):
        row=self.row|{'status':'withdrawn','deleted':True,'contentComplete':False,
                     'captureWithdrawnAt':'2026-11-14T13:00:00Z'}
        self.write([row],self.policies)
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_unknown_policy_rejected(self):
        self.write([self.row],[self.policies[0]|{'importMode':'unknown'}])
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_capture_byte_limit_enforced(self):
        with patch.object(self.recovery,'MAX_CAPTURE_BYTES',16):
            with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_total_bundle_limit_enforced(self):
        with patch.object(self.recovery,'MAX_RECOVERY_BYTES',1024):
            with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_symlink_capture_rejected(self):
        p=self.repo/'news-archive-capture.json';p.rename(self.repo/'other.json');p.symlink_to('other.json')
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_symlink_policy_rejected(self):
        p=self.repo/'multilingual-source-registry.json';p.rename(self.repo/'other.json');p.symlink_to('other.json')
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_existing_output_not_overwritten(self):
        self.output.mkdir();(self.output/'existing.txt').write_text('retain')
        with self.assertRaises(FileExistsError):self.prepare()
        self.assertEqual((self.output/'existing.txt').read_text(),'retain')

    def test_output_inside_worktree_rejected(self):
        self.output=self.repo/'recovery'
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_invalid_provenance_rejected(self):
        for changes in [{'base_sha':'b'*40},{'base_sha':'short'},{'run_id':'0'},
                        {'run_attempt':'0'},{'workflow_sha':'invalid'},
                        {'aggregation_outcome':'skipped'},{'repository_name':'Other/Repo'},
                        {'job':'../../target'}]:
            with self.subTest(changes=changes):
                with self.assertRaises((ValueError,subprocess.CalledProcessError)):self.prepare(**changes)
                self.assertFalse(self.output.exists())

    def test_capture_race_rejected(self):
        original=self.recovery.regular_bytes;calls=0
        def racing(path,limit):
            nonlocal calls
            calls+=1
            if calls==3:(self.repo/'news-archive-capture.json').write_text('[]')
            return original(path,limit)
        with patch.object(self.recovery,'regular_bytes',side_effect=racing):
            with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_generation_base_race_rejected(self):
        original=self.recovery.subprocess.run;calls=0
        def racing(*args,**kwargs):
            nonlocal calls
            calls+=1
            result=original(*args,**kwargs)
            if calls==2:
                return subprocess.CompletedProcess(result.args,0,stdout='b'*40+'\n',stderr='')
            return result
        with patch.object(self.recovery.subprocess,'run',side_effect=racing):
            with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())

    def test_policy_race_rejected(self):
        original=self.recovery.regular_bytes;calls=0
        def racing(path,limit):
            nonlocal calls
            calls+=1
            if calls==4:(self.repo/'multilingual-source-registry.json').write_text('{"sources":[]}')
            return original(path,limit)
        with patch.object(self.recovery,'regular_bytes',side_effect=racing):
            with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(self.output.exists())


class CasPush(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wrn-bridge-cas-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root / 'remote.git'
        self.work = self.root / 'work'
        self.work.mkdir()
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_TERMINAL_PROMPT='0',
                        GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
                        GIT_AUTHOR_NAME='Bridge test', GIT_AUTHOR_EMAIL='bridge@example.invalid',
                        GIT_COMMITTER_NAME='Bridge test', GIT_COMMITTER_EMAIL='bridge@example.invalid')
        self.real_git = shutil.which('git')
        self.git('init', '--bare', str(self.remote), cwd=self.root)
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Bridge test')
        self.git('config', 'user.email', 'bridge@example.invalid')
        self.git('remote', 'add', 'origin', str(self.remote))
        (self.work / 'news.json').write_text('[]\n')
        (self.work / 'news-archive-capture.json').write_text('[]\n')
        (self.work / 'build_source_archive.py').write_text(
            'import sys\nassert sys.argv[1:] == ["--verify-only", "--require-fresh"]\n')
        self.git('add', '.')
        self.git('commit', '-m', 'initial fixture')
        self.initial = self.rev()
        (self.work / 'fixture.txt').write_text('generation base\n')
        self.git('add', '.')
        self.git('commit', '-m', 'generation base')
        self.base = self.rev()
        self.git('push', 'origin', 'HEAD:refs/heads/main')
        (self.work / 'news.json').write_text('[{"title":"fresh"}]\n')
        (self.work / 'news-archive-capture.json').write_text('[{"body":"preserved"}]\n')
        self.git('add', '.')
        self.git('commit', '-m', 'generated output')
        self.head = self.rev()

    def git(self, *args, cwd=None, **kwargs):
        return run(self.real_git, *args, cwd=cwd or self.work, env=self.env, **kwargs)

    def rev(self):
        return self.git('rev-parse', 'HEAD').stdout.strip()

    def remote_rev(self):
        return self.git('--git-dir=' + str(self.remote), 'rev-parse', 'refs/heads/main').stdout.strip()

    def helper(self, base=None, branch='main', env=None):
        return run('bash', str(HELPER), branch, base if base is not None else self.base,
                   cwd=self.work, env=env or self.env, check=False)

    def alternate(self, parent=None):
        oid = self.git('commit-tree', self.base + '^{tree}', '-p', parent or self.base,
                       '-m', 'different producer').stdout.strip()
        self.git('--git-dir=' + str(self.remote), 'fetch', str(self.work), oid)
        return oid

    def assert_refused(self, expected=None):
        before = self.remote_rev()
        result = self.helper()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.remote_rev(), expected or before)
        return result

    def shim(self, before_push='', after_push='', ls_remote=''):
        folder = self.root / 'bin'; folder.mkdir()
        script = folder / 'git'
        # Scripts only manipulate this test's temporary bare remote.
        script.write_text('#!/usr/bin/env bash\nset -eu\n'
                          + (f'if [[ "${{1:-}}" == ls-remote ]]; then {ls_remote}; fi\n' if ls_remote else '')
                          + 'if [[ "${1:-}" == push ]]; then\n'
                          + f'  printf "push\\n" >> "{self.root}/push-count"\n'
                          + before_push + '\n'
                          + f'  "{self.real_git}" "$@"\n'
                          + after_push + '\n  exit 0\nfi\n'
                          + f'exec "{self.real_git}" "$@"\n')
        script.chmod(0o700)
        return dict(self.env, PATH=str(folder) + os.pathsep + os.environ['PATH'])

    def test_successful_exact_fast_forward(self):
        result = self.helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_rev(), self.head)

    def test_same_head_idempotent_without_second_push(self):
        self.git('push', 'origin', 'HEAD:refs/heads/main')
        env = self.shim(before_push='exit 91')
        result = self.helper(env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('already', result.stdout)
        self.assertFalse((self.root/'push-count').exists())

    def test_remote_advanced(self):
        other = self.alternate()
        self.git('--git-dir='+str(self.remote), 'update-ref', 'refs/heads/main', other, self.base)
        self.assert_refused(other)

    def test_remote_reset_to_ancestor(self):
        self.git('--git-dir='+str(self.remote), 'update-ref', 'refs/heads/main', self.initial, self.base)
        self.assert_refused(self.initial)

    def test_rebased_output_rejected(self):
        other = self.alternate()
        self.git('rebase', '--onto', other, self.base)
        self.assert_refused()

    def test_multiple_output_commits_rejected(self):
        (self.work/'news.json').write_text('[{"title":"changed twice"}]\n')
        self.git('add', 'news.json'); self.git('commit', '-m', 'second')
        self.assert_refused()

    def test_merge_commit_rejected(self):
        other = self.alternate()
        merge = self.git('commit-tree', self.head+'^{tree}', '-p', self.base, '-p', other,
                         '-m', 'merge output').stdout.strip()
        self.git('reset', '--hard', merge)
        self.assert_refused()

    def test_dirty_tracked_tree_rejected(self):
        (self.work/'news.json').write_text('dirty\n')
        self.assert_refused()

    def test_dirty_index_rejected(self):
        (self.work/'news.json').write_text('staged\n'); self.git('add', 'news.json')
        self.assert_refused()

    def test_untracked_output_rejected(self):
        (self.work/'stray.json').write_text('[]\n')
        self.assert_refused()

    def test_non_output_change_rejected(self):
        (self.work/'source.py').write_text('pass\n'); self.git('add', 'source.py')
        self.git('commit', '--amend', '--no-edit')
        self.assert_refused()

    def test_symlink_output_rejected(self):
        (self.work/'news.json').unlink(); (self.work/'news.json').symlink_to('fixture.txt')
        self.git('add', 'news.json'); self.git('commit', '--amend', '--no-edit')
        self.assert_refused()

    def test_empty_commit_rejected(self):
        self.git('reset', '--hard', self.base); self.git('commit', '--allow-empty', '-m', 'empty')
        self.assert_refused()

    def test_invalid_branch_or_base_rejected(self):
        for branch, base in [('other', self.base), ('main', self.base[:7]), ('main',''), ('main','g'*40)]:
            with self.subTest(branch=branch,base=base):
                self.assertNotEqual(self.helper(branch=branch,base=base).returncode, 0)
        self.assertEqual(self.remote_rev(), self.base)

    def test_validation_failure_rejected(self):
        # Validator content is part of the immutable producer base, not output.
        self.git('reset', '--hard', self.base)
        (self.work/'build_source_archive.py').write_text('raise SystemExit("validation failed")\n')
        self.git('add', '.'); self.git('commit', '-m', 'failing validator base'); self.base=self.rev()
        self.git('push', 'origin', 'HEAD:refs/heads/main')
        (self.work/'news.json').write_text('[{}]\n'); self.git('add','.'); self.git('commit','-m','output')
        self.assert_refused()

    def test_validator_cannot_mutate_outputs(self):
        self.git('reset', '--hard', self.base)
        (self.work/'build_source_archive.py').write_text('open("news.json","w").write("changed")\n')
        self.git('add', '.'); self.git('commit', '-m', 'mutating validator base'); self.base=self.rev()
        self.git('push', 'origin', 'HEAD:refs/heads/main')
        (self.work/'news.json').write_text('[{}]\n'); self.git('add','.'); self.git('commit','-m','output')
        self.assert_refused()

    def test_server_lease_rejects_racing_advance(self):
        other = self.alternate()
        env=self.shim(before_push=f'"{self.real_git}" --git-dir="{self.remote}" update-ref refs/heads/main {other} {self.base}')
        result=self.helper(env=env)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(self.remote_rev(),other)
        self.assertEqual((self.root/'push-count').read_text().splitlines(),['push'])

    def test_server_lease_rejects_racing_reset(self):
        env=self.shim(before_push=f'"{self.real_git}" --git-dir="{self.remote}" update-ref refs/heads/main {self.initial} {self.base}')
        result=self.helper(env=env)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(self.remote_rev(),self.initial)

    def test_accepted_transport_failure_verified_without_retry(self):
        env=self.shim(after_push='exit 111')
        result=self.helper(env=env)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.remote_rev(),self.head)
        self.assertEqual((self.root/'push-count').read_text().splitlines(),['push'])

    def test_unexecuted_transport_failure_not_retried(self):
        env=self.shim(before_push='exit 111')
        result=self.helper(env=env)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(self.remote_rev(),self.base)
        self.assertEqual((self.root/'push-count').read_text().splitlines(),['push'])

    def test_uncertain_postpush_verification_no_retry(self):
        env=self.shim(ls_remote=f'if [[ -e "{self.root}/push-count" ]]; then exit 92; fi')
        result=self.helper(env=env)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('verification unavailable',result.stderr)
        self.assertEqual(self.remote_rev(),self.head)
        self.assertEqual((self.root/'push-count').read_text().splitlines(),['push'])


if __name__ == '__main__':
    unittest.main()
