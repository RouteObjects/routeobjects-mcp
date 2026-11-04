#!/usr/bin/env python3
"""Exercise manifest-only review bundles without staging or creating Git commits.

A read-only Git process fixture supplies repository bases and prior blobs. The
real Git patch parser checks the successful output against the fixture files.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[2]
BASE = 'a' * 40
POSTING_FILES = [
    'UPSTREAM-POSTING.md', 'upstream-posting-receipt.json',
    'upstream-pr266-comment.md', 'upstream-pr298-comment.md', 'upstream-resource-proposal.md',
]


class ReviewBundleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='routeobjects-review-test-')
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name).resolve()
        self.output = self.workspace / 'artifacts/new-review'
        self.manifest_path = self.workspace / 'publication-manifest.json'
        self.tools = self.workspace / 'tools'
        self.tools.mkdir()
        self.script = self.workspace / 'make-review-bundle.py'
        shutil.copy2(PROJECT / 'Scripts/make-review-bundle.py', self.script)
        self.real_git = shutil.which('git')
        self.env = dict(os.environ, PATH=str(self.tools) + os.pathsep + os.environ['PATH'])
        git = self.tools / 'git'
        git.write_text('#!' + sys.executable + '\n' + '''
import hashlib, json, pathlib, sys
args=sys.argv[1:]; assert args[0]=='-C'; repo=pathlib.Path(args[1]); command=args[2:]
state=json.loads((repo/'.fixture-git.json').read_text())
if command==['rev-parse','--show-toplevel']:
    print(state.get('root',str(repo))); raise SystemExit(0)
if command==['rev-parse','--verify','HEAD']:
    if state['head'] is None: raise SystemExit(128)
    print(state['head']); raise SystemExit(0)
if command==['diff','--cached','--name-only','-z']:
    sys.stdout.write('staged.swift\\0' if state.get('staged') else ''); raise SystemExit(0)
if command[:2]==['ls-tree','-z']:
    path=command[-1]; entry=state['tree'].get(path)
    if state.get('mutateOnRead'):
        (repo/state['mutateOnRead']).write_text('Unreviewed replacement\\n')
    if entry:
        blob=hashlib.sha1(entry['content'].encode()).hexdigest()
        sys.stdout.write(entry['mode']+' blob '+blob+'\\t'+path+'\\0')
    raise SystemExit(0)
if command[:2]==['cat-file','blob']:
    for entry in state['tree'].values():
        if hashlib.sha1(entry['content'].encode()).hexdigest()==command[2]:
            sys.stdout.write(entry['content']); raise SystemExit(0)
raise SystemExit('Unpermitted Git operation: '+repr(command))
''')
        git.chmod(0o755)
        self.consumer = self.workspace / 'routeobjects-mcp'
        self.sdk = self.workspace / 'swift-sdk'
        for repo, head in [(self.consumer, None), (self.sdk, BASE)]:
            repo.mkdir()
            self.write_git(repo, {'head': head, 'tree': {}})
        self.write_file(self.consumer, 'Sources/Entry.swift', 'public let example = 1\n')
        self.write_file(self.sdk, 'Sources/MCP/Server/Server.swift', 'Reviewed server correction\n')
        self.write_file(self.sdk, 'README.md', 'Inherited upstream documentation\n')
        for name in ['REVIEW-CORRECTIONS.md', 'review-corrections.json']:
            self.write_file(self.sdk, 'verification/routeobjects-pilot/' + name, 'Reviewed current identity\n')
        self.write_git(self.sdk, {'head': BASE, 'tree': {
            'Sources/MCP/Server/Server.swift': {'mode': '100644', 'content': 'Prior SDK server\n'},
            'README.md': {'mode': '100644', 'content': 'Inherited upstream documentation\n'},
            'private-unapproved.txt': {'mode': '100644', 'content': 'Before unapproved edit\n'},
        }})
        # CHANGE: All five formerly over-selected posting files and an unrelated tracked edit are deliberately present.
        for name in POSTING_FILES:
            self.write_file(self.sdk, 'verification/routeobjects-pilot/' + name, 'Excluded posting material\n')
        self.write_file(self.sdk, 'private-unapproved.txt', 'Excluded unrelated tracked change\n')
        sdk_paths = ['Sources/MCP/Server/Server.swift', 'verification/routeobjects-pilot/REVIEW-CORRECTIONS.md',
                     'verification/routeobjects-pilot/review-corrections.json']
        self.manifest = {'repositories': {
            'routeobjects-mcp': {'base': None, 'fileCount': 1,
                                 'files': [self.record(self.consumer, 'Sources/Entry.swift')]},
            'swift-sdk': {'base': BASE, 'changedOrAddedFileCount': len(sdk_paths),
                          'changedOrAddedFiles': [self.record(self.sdk, path) for path in sdk_paths],
                          'fullTreeFileCount': len(sdk_paths) + 1,
                          'fullTreeFiles': [self.record(self.sdk, path) for path in [*sdk_paths, 'README.md']]},
        }}

    def write_file(self, repo, relative, text):
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(0o644)
        return path

    def write_git(self, repo, state):
        (repo / '.fixture-git.json').write_text(json.dumps(state))

    def record(self, repo, relative):
        path = repo / relative
        data = path.read_bytes()
        return {'path': relative, 'mode': '100755' if path.stat().st_mode & 0o111 else '100644',
                'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    def run_bundle(self, *extra):
        self.manifest_path.write_text(json.dumps(self.manifest))
        return subprocess.run([sys.executable, str(self.script), '--manifest', str(self.manifest_path),
                               '--workspace', str(self.workspace), '--output', str(self.output), *extra],
                              cwd=self.workspace, env=self.env, capture_output=True, text=True)

    def assert_refused(self, result, reason):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(reason, result.stderr)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.output.parent.exists(), 'Rejected input must not create output directories.')

    def test_approved_sdk_corrections_included_posting_and_unrelated_edits_excluded(self):
        result = self.run_bundle()
        self.assertEqual(result.returncode, 0, result.stderr)
        patch = (self.output / 'workspace.patch').read_text()
        paths = json.loads((self.output / 'paths.json').read_text())
        self.assertEqual(paths['swift-sdk'], sorted(e['path'] for e in self.manifest['repositories']['swift-sdk']['changedOrAddedFiles']))
        self.assertIn('-Prior SDK server\n+Reviewed server correction', patch)
        for name in ['REVIEW-CORRECTIONS.md', 'review-corrections.json']:
            self.assertIn('swift-sdk/verification/routeobjects-pilot/' + name, patch)
        for excluded in [*POSTING_FILES, 'private-unapproved.txt', 'Inherited upstream documentation']:
            self.assertNotIn(excluded, patch)
        self.assertIn('new file mode 100644', patch)
        self.assertIn('routeobjects-mcp/Sources/Entry.swift', patch)
        metadata = json.loads((self.output / 'manifest-identity.json').read_text())
        self.assertEqual(metadata['manifestSHA256'], hashlib.sha256(self.manifest_path.read_bytes()).hexdigest())
        self.assertEqual(metadata['verifiedFileCounts'], {'routeobjects-mcp': 1, 'swift-sdk': 4})
        self.assertEqual((self.output / 'workspace.patch.sha256').read_text().split()[0],
                         hashlib.sha256((self.output / 'workspace.patch').read_bytes()).hexdigest())
        check = subprocess.run([self.real_git, 'apply', '--reverse', '--check', str(self.output / 'workspace.patch')],
                               cwd=self.workspace, capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_explicit_manifest_is_required(self):
        result = subprocess.run([sys.executable, str(self.script), '--output', str(self.output)],
                                env=self.env, capture_output=True, text=True)
        self.assert_refused(result, '--manifest')

    def test_consumer_only_unborn_selection_does_not_require_sibling_repositories(self):
        del self.manifest['repositories']['swift-sdk']
        shutil.rmtree(self.sdk)
        result = self.run_bundle()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((self.output / 'paths.json').read_text()), {'routeobjects-mcp': ['Sources/Entry.swift']})

    def test_swift_versioned_manifest_and_extension_paths_are_validated_and_selected(self):
        # CHANGE: At-sign manifests and plus-sign Swift extensions are legitimate, unambiguous Git patch paths.
        relatives = ['Package@swift-6.0.swift', 'Sources/MCP/Extensions/Data+Extensions.swift']
        state = json.loads((self.sdk / '.fixture-git.json').read_text())
        section = self.manifest['repositories']['swift-sdk']
        for relative in relatives:
            self.write_file(self.sdk, relative, '// Reviewed Swift source\n')
            state['tree'][relative] = {'mode': '100644', 'content': '// Prior Swift source\n'}
            section['fullTreeFiles'].append(self.record(self.sdk, relative))
            section['fullTreeFileCount'] += 1
            section['changedOrAddedFiles'].append(self.record(self.sdk, relative))
            section['changedOrAddedFileCount'] += 1
        self.write_git(self.sdk, state)
        result = self.run_bundle()
        self.assertEqual(result.returncode, 0, result.stderr)
        patch = (self.output / 'workspace.patch').read_text()
        for relative in relatives:
            self.assertIn('a/swift-sdk/' + relative, patch)
            self.assertIn(relative, json.loads((self.output / 'paths.json').read_text())['swift-sdk'])
        self.assertEqual(patch.count('-// Prior Swift source\n+// Reviewed Swift source'), 2)
        self.assertEqual(json.loads((self.output / 'manifest-identity.json').read_text())['verifiedFileCounts']['swift-sdk'], 6)
        check = subprocess.run([self.real_git, 'apply', '--reverse', '--check', str(self.output / 'workspace.patch')],
                               cwd=self.workspace, capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_hash_size_and_mode_drift_are_rejected_before_output(self):
        original = copy.deepcopy(self.manifest)
        for field, value, reason in [('sha256', '0' * 64, 'hash or size mismatch'),
                                     ('bytes', 999, 'hash or size mismatch'), ('mode', '100755', 'mode mismatch')]:
            with self.subTest(field=field):
                self.manifest = copy.deepcopy(original)
                self.manifest['repositories']['routeobjects-mcp']['files'][0][field] = value
                self.assert_refused(self.run_bundle(), reason)

    def test_unselected_full_tree_drift_is_rejected(self):
        (self.sdk / 'README.md').write_text('Changed inherited SDK source inventory\n')
        self.assert_refused(self.run_bundle(), 'hash or size mismatch')

    def test_counts_duplicates_and_delta_identity_mismatch_are_rejected(self):
        original = copy.deepcopy(self.manifest)
        self.manifest['repositories']['swift-sdk']['fullTreeFileCount'] += 1
        self.assert_refused(self.run_bundle(), 'count mismatch')
        self.manifest = copy.deepcopy(original)
        section = self.manifest['repositories']['routeobjects-mcp']
        section['files'].append(copy.deepcopy(section['files'][0])); section['fileCount'] += 1
        self.assert_refused(self.run_bundle(), 'Duplicate review path')
        self.manifest = copy.deepcopy(original)
        self.manifest['repositories']['swift-sdk']['changedOrAddedFiles'][0]['sha256'] = '0' * 64
        self.assert_refused(self.run_bundle(), 'Delta disagrees')

    def test_traversal_absolute_git_metadata_and_ambiguous_paths_are_rejected(self):
        original = copy.deepcopy(self.manifest)
        for path in ['../secret', '/tmp/secret', '.git/config', '.GIT/config', 'Sources/../secret', 'Sources//Entry.swift',
                     'Sources/Entry.swift\nother', 'Sources\\Entry.swift']:
            with self.subTest(path=path):
                self.manifest = copy.deepcopy(original)
                self.manifest['repositories']['routeobjects-mcp']['files'][0]['path'] = path
                self.assert_refused(self.run_bundle(), 'Unsafe review path')
        self.manifest = copy.deepcopy(original)
        self.manifest['repositories']['../swift-sdk'] = self.manifest['repositories'].pop('swift-sdk')
        self.assert_refused(self.run_bundle(), 'Unsafe review path')

    def test_symlink_file_and_ancestor_are_rejected(self):
        source = self.consumer / 'Sources/Entry.swift'
        original = source.read_bytes()
        outside = self.workspace / 'outside.swift'; outside.write_bytes(original)
        source.unlink(); source.symlink_to(outside)
        self.assert_refused(self.run_bundle(), 'Symlink in review path')
        source.unlink(); source.write_bytes(original)
        moved = self.workspace / 'moved-sources'
        (self.consumer / 'Sources').rename(moved)
        (self.consumer / 'Sources').symlink_to(moved, target_is_directory=True)
        self.assert_refused(self.run_bundle(), 'Symlink in review path')

    def test_staged_files_or_changed_base_are_rejected(self):
        state = json.loads((self.sdk / '.fixture-git.json').read_text())
        for change, reason in [({'staged': True}, 'Unexpected staged files'),
                               ({'head': 'b' * 40}, 'base differs')]:
            with self.subTest(change=change):
                self.write_git(self.sdk, dict(state, **change))
                self.assert_refused(self.run_bundle(), reason)

    def test_non_repository_and_non_unborn_consumer_are_rejected(self):
        original = json.loads((self.consumer / '.fixture-git.json').read_text())
        self.write_git(self.consumer, dict(original, root=str(self.workspace)))
        self.assert_refused(self.run_bundle(), 'Repository root mismatch')
        self.write_git(self.consumer, dict(original, head=BASE))
        self.assert_refused(self.run_bundle(), 'Expected unborn repository')

    def test_source_changes_during_baseline_reads_are_rejected(self):
        state = json.loads((self.sdk / '.fixture-git.json').read_text())
        state['mutateOnRead'] = 'Sources/MCP/Server/Server.swift'
        self.write_git(self.sdk, state)
        self.assert_refused(self.run_bundle(), 'hash or size mismatch')

    def test_unsupported_deletion_manifest_is_rejected(self):
        self.manifest['repositories']['swift-sdk']['deletedPaths'] = ['README.md']
        self.assert_refused(self.run_bundle(), 'Deletion manifests require')

    def test_executable_mode_and_no_final_newline_produce_applicable_patch(self):
        path = self.consumer / 'Sources/Entry.swift'
        path.write_text('last line without newline'); path.chmod(0o755)
        self.manifest['repositories']['routeobjects-mcp']['files'] = [self.record(self.consumer, 'Sources/Entry.swift')]
        result = self.run_bundle()
        self.assertEqual(result.returncode, 0, result.stderr)
        patch = (self.output / 'workspace.patch').read_text()
        self.assertIn('new file mode 100755', patch)
        self.assertIn('\\ No newline at end of file', patch)
        check = subprocess.run([self.real_git, 'apply', '--reverse', '--check', str(self.output / 'workspace.patch')],
                               cwd=self.workspace, capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_existing_output_is_not_overwritten(self):
        self.output.mkdir(parents=True)
        sentinel = self.output / 'keep.txt'; sentinel.write_text('retain prior review\n')
        result = self.run_bundle()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('output already exists', result.stderr)
        self.assertEqual(sentinel.read_text(), 'retain prior review\n')
        self.assertEqual([p.name for p in self.output.iterdir()], ['keep.txt'])


if __name__ == '__main__':
    unittest.main()
