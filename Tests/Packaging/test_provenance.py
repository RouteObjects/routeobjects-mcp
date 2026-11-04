#!/usr/bin/env python3
"""Exercise the real build/archive drivers with isolated fake compiler processes.

These tests validate provenance enforcement, not a native Swift build or platform
qualification. They never read or modify the real build directory or SDK checkout.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[2]
BASE = 'a0ae212ebf6eab5f754c3129608bc5557637e605'


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='cidr-provenance-test-')
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.root = self.workspace / 'routeobjects-mcp'
        self.sdk = self.workspace / 'swift-sdk'
        self.tools = self.workspace / 'tools'
        for path in [self.root / 'Scripts', self.root / 'Sources', self.root / 'Docs',
                     self.root / 'ThirdPartyNotices', self.root / '.build/debug', self.sdk / 'Sources', self.tools]:
            path.mkdir(parents=True)
        for name in ['build-pilot.py', 'archive-pilot.py', 'pilot_provenance.py', 'verify-dependencies.py', 'sdk_selection.py']:
            shutil.copy2(PROJECT / 'Scripts' / name, self.root / 'Scripts' / name)
        for directory in [self.root, self.sdk]:
            (directory / 'Package.swift').write_text('// fixture manifest\n')
            (directory / 'Sources/Entry.swift').write_text('// fixture source\n')
            (directory / 'LICENSE').write_text('Fixture license\n')
        (self.root / 'Package.swift').write_text('let maintenanceSDKRevision: String? = nil\n')
        (self.sdk / 'HEAD.txt').write_text(BASE)
        pins = []
        for identity, version in {'swift-cidr':'0.8.1', 'swift-sdk':'0.12.1', 'swift-log':'1.6.2',
                                  'swift-system':'1.4.0', **{f'fixture-{n}':'1.0.0' for n in range(5)}}.items():
            pins.append({'identity': identity, 'kind': 'remoteSourceControl',
                         'location': 'https://github.com/modelcontextprotocol/swift-sdk.git' if identity == 'swift-sdk' else 'https://example.invalid/' + identity,
                         'state': {'version': version, 'revision': BASE}})
            checkout = self.root / '.build/checkouts' / identity
            checkout.mkdir(parents=True)
            (checkout / 'LICENSE').write_text('Fixture dependency license\n')
        (self.root / 'Package.resolved').write_text(json.dumps({'pins': pins, 'version': 3}) + '\n')
        (self.sdk / 'Package.resolved').write_text('{"pins": [], "version": 3}\n')
        state = {'object': {'dependencies': [{'packageRef': {'identity':'swift-sdk', 'location':'https://github.com/modelcontextprotocol/swift-sdk.git'},
                                             'state': {'name':'edited', 'path':str(self.sdk)}}]}}
        (self.root / '.build/workspace-state.json').write_text(json.dumps(state))
        # CHANGE: Fixtures approve their own isolated source; production checks are not bypassed.
        sdk_digest = hashlib.sha256()
        for path in sorted([*self.sdk.glob('Package*.swift'), *self.sdk.glob('Sources/**/*')]):
            if path.is_file():
                sdk_digest.update(path.relative_to(self.sdk).as_posix().encode() + b'\0')
                sdk_digest.update(path.read_bytes() + b'\0')
        selection = {'schemaVersion': 1,
                     'baseline': {'repositoryURL': 'https://github.com/modelcontextprotocol/swift-sdk.git',
                                  'version': '0.12.1', 'revision': BASE},
                     'maintenance': {'repositoryURL': 'https://github.com/RouteObjects/swift-sdk.git',
                                     'revision': None, 'sourceSHA256': sdk_digest.hexdigest(),
                                     'lockfileSHA256': hashlib.sha256((self.sdk / 'Package.resolved').read_bytes()).hexdigest()}}
        (self.root / 'SDKSelection.json').write_text(json.dumps(selection) + '\n')
        for name in ['README.md', 'CONTRACTS.md']:
            (self.root / name).write_text('Fixture documentation\n')
        self.system = 'macos' if platform.system() == 'Darwin' else 'linux'
        self.arch = {'aarch64':'arm64', 'AMD64':'x86_64'}.get(platform.machine(), platform.machine())
        self.target = f'{self.system}-{self.arch}'
        self.env = dict(os.environ, PATH=str(self.tools) + os.pathsep + os.environ['PATH'],
                        FIXTURE_ROOT=str(self.root), FIXTURE_SDK=str(self.sdk), FIXTURE_ARCH=self.arch)
        self.write_tool('git', '''
import os, pathlib
sdk = pathlib.Path(os.environ['FIXTURE_SDK'])
print((sdk / 'HEAD.txt').read_text().strip())
''')
        self.write_tool('file', '''
import json, os, pathlib, sys
root = pathlib.Path(os.environ['FIXTURE_ROOT'])
if (root / 'mutate-at-copy').exists():
    with pathlib.Path(sys.argv[-1]).open('a') as output: output.write('# changed after initial validation\\n')
if (root / 'mutate-receipt-at-copy').exists():
    receipt = pathlib.Path(sys.argv[-1] + '.build-receipt.json')
    data = json.loads(receipt.read_text()); data['build']['swift'] = 'Replaced receipt compiler'
    receipt.write_text(json.dumps(data))
print('fixture executable ' + os.environ['FIXTURE_ARCH'])
''')
        self.write_tool('swift', '''
import hashlib, json, os, pathlib, sys
root = pathlib.Path(os.environ['FIXTURE_ROOT']); sdk = pathlib.Path(os.environ['FIXTURE_SDK'])
args = sys.argv[1:]
if args == ['--version']:
    print('Swift fixture compiler 6.2'); raise SystemExit(0)
if args == ['-print-target-info']:
    print(json.dumps({'target': {'triple': 'fixture-target'}})); raise SystemExit(0)
configuration = args[args.index('-c') + 1]
output = root / '.build' / configuration
output.mkdir(parents=True, exist_ok=True)
if '--show-bin-path' in args:
    print(output); raise SystemExit(0)
lock = root / 'Package.resolved'; data = json.loads(lock.read_text())
data['pins'] = [p for p in data['pins'] if p['identity'] != 'swift-sdk']
lock.write_text(json.dumps(data))
if (root / 'fail-build').exists(): raise SystemExit(1)
if (root / 'drift-app').exists(): (root / 'Sources/Entry.swift').write_text('// changed during build\\n')
if (root / 'drift-sdk').exists(): (sdk / 'Sources/Entry.swift').write_text('// changed during build\\n')
binary = output / 'routeobjects-mcp'
source = hashlib.sha256((root / 'Sources/Entry.swift').read_bytes()).hexdigest()
binary.write_text('#!/bin/sh\\n# ' + source + '\\nprintf "routeobjects-mcp 0.1.0\\\\n"\\n')
binary.chmod(0o755)
''')
        self.binary = self.root / '.build/debug/routeobjects-mcp'
        self.receipt = self.binary.with_name(self.binary.name + '.build-receipt.json')
        self.original_lock = (self.root / 'Package.resolved').read_bytes()

    def write_tool(self, name, source):
        path = self.tools / name
        path.write_text('#!' + sys.executable + '\n' + source)
        path.chmod(0o755)

    def run_script(self, name, *arguments):
        return subprocess.run([sys.executable, str(self.root / 'Scripts' / name), *arguments],
                              cwd=self.root, env=self.env, text=True, capture_output=True)

    def build(self):
        result = self.run_script('build-pilot.py', 'build')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(self.receipt.is_file())
        self.assertEqual((self.root / 'Package.resolved').read_bytes(), self.original_lock)

    def archive(self, target=None):
        return self.run_script('archive-pilot.py', '--binary', str(self.binary), '--platform', target or self.target,
                               '--execution', 'native', '--output', str(self.root / 'artifacts'))

    def assert_rejected(self, result, reason):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(reason, result.stderr)
        self.assertEqual(list((self.root / 'artifacts').glob('*.tar.gz')), [])

    def test_successful_build_archive_preserves_build_time_metadata(self):
        self.build()
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt['build']['arguments'], ['build', '--skip-update', '-c', 'debug', '--product', 'routeobjects-mcp'])
        self.assertEqual(receipt['build']['compilerDefaultTarget'], {'triple': 'fixture-target'})
        self.assertEqual(receipt['inputs']['application']['lockfileSHA256'], hashlib.sha256(self.original_lock).hexdigest())
        # A different/missing compiler on the packaging host must not rewrite build provenance.
        self.write_tool('swift', 'raise SystemExit("Packager must not invoke Swift")\n')
        result = self.archive()
        self.assertEqual(result.returncode, 0, result.stderr)
        archive = next((self.root / 'artifacts').glob('*.tar.gz'))
        with tarfile.open(archive) as tar:
            prefix = f'routeobjects-mcp-0.1.0-pilot-{self.target}'
            metadata = json.load(tar.extractfile(prefix + '/BUILD-INFO.json'))
            archived_receipt = json.load(tar.extractfile(prefix + '/BUILD-RECEIPT.json'))
            executable = tar.extractfile(prefix + '/bin/routeobjects-mcp').read()
            selected = tar.extractfile(prefix + '/SDKSelection.json').read()
        self.assertEqual(metadata['swift'], 'Swift fixture compiler 6.2')
        self.assertEqual(metadata['build'], receipt['build'])
        self.assertEqual(archived_receipt, receipt)
        self.assertEqual(metadata['binarySHA256'], hashlib.sha256(executable).hexdigest())
        self.assertFalse(metadata['releaseReady'])
        self.assertTrue(metadata['sdk']['uncommittedMaintenancePatch'])
        self.assertEqual(metadata['sdk']['selectionMode'], 'development')
        self.assertEqual(hashlib.sha256(selected).hexdigest(), receipt['inputs']['application']['sdkSelectionSHA256'])

    def test_missing_receipt_is_rejected(self):
        self.build()
        self.receipt.unlink()
        self.assert_rejected(self.archive(), 'Missing build receipt')

    def test_linux_distribution_receipt_records_linker_stripping(self):
        # CHANGE: Model the Linux host at the process boundary without requiring a Linux compiler for this driver test.
        (self.root / 'Scripts/platform.py').write_text(
            "def system(): return 'Linux'\n"
            "def release(): return 'fixture'\n"
            f"def machine(): return {self.arch!r}\n")
        result = self.run_script('build-pilot.py', 'build', '--configuration', 'release',
                                 '--static-swift-stdlib', '--linker-strip-all')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.binary = self.root / '.build/release/routeobjects-mcp'
        self.receipt = self.binary.with_name(self.binary.name + '.build-receipt.json')
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt['build']['arguments'], [
            'build', '--skip-update', '-c', 'release', '--static-swift-stdlib',
            '-Xlinker', '--strip-all', '--product', 'routeobjects-mcp'])
        self.assertEqual(receipt['postProcessing'], [])
        self.assertEqual(receipt['binary']['sha256'], hashlib.sha256(self.binary.read_bytes()).hexdigest())
        self.assertEqual((self.root / 'Package.resolved').read_bytes(), self.original_lock)
        result = self.archive(f'linux-{self.arch}')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_linker_stripping_rejects_unsupported_modes_before_build(self):
        for command in [ ['build'], ['test', '--configuration', 'release'] ]:
            with self.subTest(command=command):
                result = self.run_script('build-pilot.py', *command, '--linker-strip-all')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('requires a Linux Release build', result.stderr)
                self.assertFalse(self.receipt.exists())
                self.assertEqual((self.root / 'Package.resolved').read_bytes(), self.original_lock)
        if platform.system() != 'Linux':
            result = self.run_script('build-pilot.py', 'build', '--configuration', 'release', '--linker-strip-all')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('requires a Linux Release build', result.stderr)

    def test_old_binary_cannot_receive_new_source_identity(self):
        self.build()
        old_binary = self.binary.read_bytes()
        (self.root / 'Sources/Entry.swift').write_text('// newer source\n')
        self.build()
        self.binary.write_bytes(old_binary)
        self.assert_rejected(self.archive(), 'Executable differs from the build receipt')

    def test_source_sdk_revision_and_lock_drift_are_rejected(self):
        self.build()
        for path in [self.root / 'Sources/Entry.swift', self.sdk / 'Sources/Entry.swift',
                     self.root / 'Package.resolved', self.sdk / 'Package.resolved', self.sdk / 'HEAD.txt']:
            with self.subTest(path=path.relative_to(self.workspace)):
                original = path.read_bytes()
                path.write_bytes(original + b'\n')
                if path.name == 'HEAD.txt':
                    path.write_text('b' * 40)
                reason = 'differs from the build receipt'
                if path in [self.sdk / 'Sources/Entry.swift', self.sdk / 'Package.resolved']:
                    reason = 'differs from reviewed selection'
                elif path == self.sdk / 'HEAD.txt':
                    reason = 'HEAD differs from the selected revision'
                self.assert_rejected(self.archive(), reason)
                path.write_bytes(original)

    def test_target_mismatch_is_rejected(self):
        self.build()
        other = 'x86_64' if self.arch == 'arm64' else 'arm64'
        self.assert_rejected(self.archive(f'{self.system}-{other}'), 'Archive target differs')

    def test_unsupported_postprocessing_is_rejected(self):
        self.build()
        data = json.loads(self.receipt.read_text())
        data['postProcessing'] = ['strip']
        self.receipt.write_text(json.dumps(data))
        self.assert_rejected(self.archive(), 'Post-build transformations are not supported')

    def test_failed_rebuild_invalidates_previous_receipt_and_restores_lock(self):
        self.build()
        (self.root / 'fail-build').touch()
        result = self.run_script('build-pilot.py', 'build')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.receipt.exists())
        self.assertEqual((self.root / 'Package.resolved').read_bytes(), self.original_lock)

    def test_changed_sources_during_build_cannot_receive_a_receipt(self):
        for marker in ['drift-app', 'drift-sdk']:
            with self.subTest(marker=marker):
                (self.root / marker).touch()
                result = self.run_script('build-pilot.py', 'build')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('changed during build', result.stderr)
                self.assertFalse(self.receipt.exists())
                self.assertEqual((self.root / 'Package.resolved').read_bytes(), self.original_lock)
                (self.root / marker).unlink()

    def test_binary_change_before_copy_is_rejected(self):
        self.build()
        (self.root / 'mutate-at-copy').touch()
        self.assert_rejected(self.archive(), 'Executable changed while preparing the archive')

    def test_receipt_replacement_before_copy_is_rejected(self):
        self.build()
        (self.root / 'mutate-receipt-at-copy').touch()
        self.assert_rejected(self.archive(), 'Build receipt changed while preparing the archive')

    def test_malformed_receipt_is_rejected(self):
        self.build()
        self.receipt.write_text('{"schemaVersion":1}')
        self.assert_rejected(self.archive(), 'Malformed or incomplete build receipt')


if __name__ == '__main__':
    unittest.main()
