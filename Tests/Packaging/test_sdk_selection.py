#!/usr/bin/env python3
"""Exercise SDK selection through real driver subprocesses and fake Git/Swift.

No real Git commits, repositories, network fetches, or compiler builds are made.
These regressions prove publication/build guards, not native SDK qualification.
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
PIN = '1234567890abcdef1234567890abcdef12345678'
UPSTREAM = 'https://github.com/modelcontextprotocol/swift-sdk.git'
FORK = 'https://github.com/RouteObjects/swift-sdk.git'


def source_digest(root):
    digest = hashlib.sha256()
    for path in sorted([*root.glob('Package*.swift'), *root.glob('Sources/**/*')]):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode() + b'\0')
            digest.update(path.read_bytes() + b'\0')
    return digest.hexdigest()


class SDKSelectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='routeobjects-sdk-selection-')
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        self.root = self.workspace / 'routeobjects-mcp'
        self.sdk = self.workspace / 'swift-sdk'
        self.tools = self.workspace / 'tools'
        for path in [self.root / 'Scripts', self.root / 'Sources', self.root / '.build/debug',
                     self.root / 'Docs', self.root / 'ThirdPartyNotices',
                     self.sdk / 'Sources', self.tools]:
            path.mkdir(parents=True)
        for name in ['archive-pilot.py', 'build-pilot.py', 'configure-pilot.py', 'verify-dependencies.py',
                     'pilot_provenance.py', 'sdk_selection.py']:
            shutil.copy2(PROJECT / 'Scripts' / name, self.root / 'Scripts' / name)
        for root in [self.root, self.sdk]:
            (root / 'Package.swift').write_text('// Fixture package\n')
            (root / 'Sources/Entry.swift').write_text('// Fixture source\n')
            (root / 'LICENSE').write_text('Fixture license\n')
        for name in ['README.md', 'CONTRACTS.md', 'Docs/Fixture.md', 'ThirdPartyNotices/Fixture.txt']:
            (self.root / name).write_text('Fixture documentation\n')
        (self.root / 'Package.swift').write_text('// Fixture package\nlet maintenanceSDKRevision: String? = nil\n')
        (self.sdk / 'Package.resolved').write_text('{"pins": [], "version": 3}\n')
        (self.sdk / '.fixture-HEAD').write_text(BASE)
        # CHANGE: Independent fixture locks cannot race SwiftPM's temporary editable-pin omission in a real build.
        versions = {'swift-cidr': '0.8.1', 'swift-sdk': '0.12.1', 'swift-log': '1.6.2',
                    'swift-system': '1.4.0', **{f'fixture-{n}': '1.0.0' for n in range(5)}}
        self.lock = {'version': 3, 'pins': [
            {'identity': identity, 'kind': 'remoteSourceControl',
             'location': UPSTREAM if identity == 'swift-sdk' else f'https://example.invalid/{identity}.git',
             'state': {'version': version, 'revision': BASE if identity == 'swift-sdk' else 'c' * 40}}
            for identity, version in versions.items()
        ]}
        self.selection = {
            'schemaVersion': 1,
            'baseline': {'repositoryURL': UPSTREAM, 'version': '0.12.1', 'revision': BASE},
            'maintenance': {
                'repositoryURL': FORK, 'revision': None,
                'sourceSHA256': source_digest(self.sdk),
                'lockfileSHA256': hashlib.sha256((self.sdk / 'Package.resolved').read_bytes()).hexdigest(),
            },
        }
        self.state = {'object': {'dependencies': []}}
        for pin in self.lock['pins']:
            identity = pin['identity']
            if identity != 'swift-sdk':
                checkout = self.root / '.build/checkouts' / identity
                checkout.mkdir(parents=True)
                (checkout / 'LICENSE').write_text('Fixture dependency license\n')
            self.state['object']['dependencies'].append({
                'packageRef': {'identity': identity, 'kind': 'remoteSourceControl', 'location': pin['location']},
                'state': {'name': 'sourceControlCheckout', 'checkoutState': dict(pin['state'])},
                'subpath': identity,
            })
        self.sdk_entry = next(e for e in self.state['object']['dependencies'] if e['packageRef']['identity'] == 'swift-sdk')
        self.sdk_entry['state'] = {'name': 'edited', 'path': str(self.sdk)}
        self.mode = 'development'
        self.save_configuration()
        self.env = {k: v for k, v in os.environ.items() if k != 'ROUTEOBJECTS_MCP_SDK_PATH'}
        self.env.update(PATH=str(self.tools) + os.pathsep + os.environ['PATH'],
                        SDK_TEST_ROOT=str(self.root), SDK_TEST_SDK=str(self.sdk), SDK_TEST_MODE=self.mode,
                        SDK_TEST_ARCH={'aarch64': 'arm64', 'AMD64': 'x86_64'}.get(platform.machine(), platform.machine()))
        self.write_tool('file', '''
import os
print('Fixture executable ' + os.environ['SDK_TEST_ARCH'])
''')
        self.write_tool('git', '''
import pathlib, sys
args = sys.argv[1:]
if len(args) < 3 or args[0] != '-C': raise SystemExit('Unexpected fixture Git command')
root = pathlib.Path(args[1]); command = args[2:]
if command[0] == 'rev-parse' and command[-1] == 'HEAD':
    print((root / '.fixture-HEAD').read_text().strip())
elif command[0] == 'status':
    status = root / '.fixture-status'
    print(status.read_text() if status.exists() else '', end='')
else:
    raise SystemExit('Unexpected fixture Git command: ' + repr(command))
''')
        self.write_tool('swift', '''
import json, os, pathlib, sys
root = pathlib.Path(os.environ['SDK_TEST_ROOT']); args = sys.argv[1:]
with (root / 'swift-invocations.jsonl').open('a') as log: log.write(json.dumps(args) + '\\n')
if os.environ['SDK_TEST_MODE'] == 'pinned' and 'ROUTEOBJECTS_MCP_SDK_PATH' in os.environ:
    raise SystemExit('Pinned compiler must not receive a development override')
if args == ['--version']:
    print('Swift fixture compiler 6.2'); raise SystemExit(0)
if args == ['-print-target-info']:
    print(json.dumps({'target': {'triple': 'fixture-target'}})); raise SystemExit(0)
if args[0] == 'package':
    lock = root / 'Package.resolved'; data = json.loads(lock.read_text())
    if (root / 'fail-resolve').exists():
        data['pins'][-1]['state']['revision'] = '0' * 40
        lock.write_text(json.dumps(data)); raise SystemExit(1)
    template = root / 'resolved-workspace-template.json'
    if 'resolve' in args:
        (root / '.build/workspace-state.json').write_bytes(template.read_bytes())
    if 'edit' in args:
        state = json.loads(template.read_text())
        entry = next(e for e in state['object']['dependencies'] if e['packageRef']['identity'] == 'swift-sdk')
        entry['state'] = {'name': 'edited', 'path': args[args.index('--path') + 1]}
        (root / '.build/workspace-state.json').write_text(json.dumps(state))
        data['pins'] = [p for p in data['pins'] if p['identity'] != 'swift-sdk']
        lock.write_text(json.dumps(data))
    raise SystemExit(0)
configuration = args[args.index('-c') + 1]
output = root / '.build' / configuration; output.mkdir(parents=True, exist_ok=True)
if '--show-bin-path' in args:
    print(output); raise SystemExit(0)
lock = root / 'Package.resolved'; data = json.loads(lock.read_text())
if os.environ['SDK_TEST_MODE'] == 'development':
    data['pins'] = [p for p in data['pins'] if p['identity'] != 'swift-sdk']
if (root / 'drift-pin').exists(): data['pins'][-1]['state']['revision'] = '0' * 40
if (root / 'drop-sdk-pin').exists(): data['pins'] = [p for p in data['pins'] if p['identity'] != 'swift-sdk']
if (root / 'duplicate-pin').exists(): data['pins'].append(data['pins'][0].copy())
lock.write_text(json.dumps(data))
if (root / 'drift-selection').exists():
    selection = root / 'SDKSelection.json'; selected = json.loads(selection.read_text())
    selected['maintenance']['sourceSHA256'] = '0' * 64
    selection.write_text(json.dumps(selected))
if (root / 'fail-build').exists(): raise SystemExit(1)
binary = output / 'routeobjects-mcp'
binary.write_text('#!/bin/sh\\n# This build-driver fixture must never be executed.\\nexit 99\\n'); binary.chmod(0o755)
''')
        self.binary = self.root / '.build/debug/routeobjects-mcp'
        self.receipt = self.binary.with_name(self.binary.name + '.build-receipt.json')

    def write_tool(self, name, source):
        path = self.tools / name
        path.write_text('#!' + sys.executable + '\n' + source)
        path.chmod(0o755)

    def save_configuration(self):
        (self.root / 'Package.resolved').write_text(json.dumps(self.lock) + '\n')
        (self.root / 'SDKSelection.json').write_text(json.dumps(self.selection) + '\n')
        (self.root / '.build/workspace-state.json').write_text(json.dumps(self.state) + '\n')
        (self.root / 'resolved-workspace-template.json').write_text(json.dumps(self.state) + '\n')

    def pin_sdk(self):
        # CHANGE: Model the future reviewed commit without creating real Git commits or accepting the baseline as its pin.
        self.selection['maintenance']['revision'] = PIN
        manifest = self.root / 'Package.swift'
        manifest.write_text(manifest.read_text().replace('let maintenanceSDKRevision: String? = nil',
                                                       f'let maintenanceSDKRevision: String? = "{PIN}"'))
        for pin in self.lock['pins']:
            if pin['identity'] == 'swift-sdk':
                pin['location'] = FORK
                pin['state'] = {'revision': PIN}
        checkout = self.root / '.build/checkouts/swift-sdk'
        checkout.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.sdk, checkout)
        self.sdk = checkout
        (self.sdk / '.fixture-HEAD').write_text(PIN)
        self.sdk_entry['packageRef']['location'] = FORK
        self.sdk_entry['state'] = {'name': 'sourceControlCheckout', 'checkoutState': {'revision': PIN}}
        self.mode = 'pinned'
        self.env.update(SDK_TEST_SDK=str(self.sdk), SDK_TEST_MODE=self.mode)
        self.save_configuration()

    def run_script(self, name, *args, env=None):
        return subprocess.run([sys.executable, str(self.root / 'Scripts' / name), *args],
                              cwd=self.root, env=env or self.env, capture_output=True, text=True)

    def verify(self, *args):
        selected = ['--sdk-path', str(self.sdk)] if self.mode == 'development' else []
        return self.run_script('verify-dependencies.py', *selected, *args)

    def build(self, *args, env=None):
        selected = ['--sdk-path', str(self.sdk)] if self.mode == 'development' else []
        return self.run_script('build-pilot.py', *selected, 'build', *args, env=env)

    def assert_passed(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_rejected(self, result, *, before_compiler=False):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        if before_compiler:
            self.assertFalse((self.root / 'swift-invocations.jsonl').exists(), result.stdout + result.stderr)
            self.assertFalse(self.receipt.exists())

    def test_reviewed_development_checkout_and_preflight(self):
        self.assert_passed(self.verify())
        (self.root / '.build/workspace-state.json').unlink()
        self.assert_passed(self.verify('--selection-only'))
        self.assert_rejected(self.verify())

    def test_pinned_configure_bootstraps_locked_checkout_without_local_override(self):
        self.pin_sdk()
        original = (self.root / 'Package.resolved').read_bytes()
        (self.root / '.build/workspace-state.json').unlink()
        self.assert_passed(self.run_script('configure-pilot.py'))
        self.assertEqual((self.root / 'Package.resolved').read_bytes(), original)
        commands = [json.loads(line) for line in (self.root / 'swift-invocations.jsonl').read_text().splitlines()]
        self.assertEqual(commands, [['package', '--force-resolved-versions', 'resolve']])
        self.assert_passed(self.verify())

    def test_pinned_configure_does_not_replace_existing_edit(self):
        self.pin_sdk()
        self.sdk_entry['state'] = {'name': 'edited', 'path': str(self.sdk)}
        self.save_configuration()
        self.assert_rejected(self.run_script('configure-pilot.py'), before_compiler=True)
        self.assertEqual(json.loads((self.root / '.build/workspace-state.json').read_text()), self.state)

    def test_development_configure_rejects_unreviewed_source_before_resolve(self):
        (self.root / '.build/workspace-state.json').unlink()
        (self.sdk / 'Sources/Entry.swift').write_text('// Unreviewed source\n')
        self.assert_rejected(self.run_script('configure-pilot.py', str(self.sdk)), before_compiler=True)

    def test_development_configure_restores_pin_after_explicit_edit(self):
        original = (self.root / 'Package.resolved').read_bytes()
        (self.root / '.build/workspace-state.json').unlink()
        self.assert_passed(self.run_script('configure-pilot.py', str(self.sdk)))
        self.assertEqual((self.root / 'Package.resolved').read_bytes(), original)
        commands = [json.loads(line) for line in (self.root / 'swift-invocations.jsonl').read_text().splitlines()]
        self.assertEqual(commands, [['package', '--force-resolved-versions', 'resolve'],
                                    ['package', 'edit', 'swift-sdk', '--path', str(self.sdk.resolve())]])
        self.assert_passed(self.verify())

    def test_configure_failed_resolution_restores_complete_lock(self):
        for pinned in [False, True]:
            with self.subTest(pinned=pinned):
                if pinned:
                    self.pin_sdk()
                original = (self.root / 'Package.resolved').read_bytes()
                (self.root / '.build/workspace-state.json').unlink()
                (self.root / 'fail-resolve').touch()
                arguments = [str(self.sdk)] if self.mode == 'development' else []
                self.assert_rejected(self.run_script('configure-pilot.py', *arguments))
                self.assertEqual((self.root / 'Package.resolved').read_bytes(), original)
                self.assertFalse(self.receipt.exists())
                (self.root / 'fail-resolve').unlink()

    def test_pinned_revision_need_not_equal_released_baseline(self):
        self.pin_sdk()
        self.assert_passed(self.verify())
        original = (self.root / 'Package.resolved').read_bytes()
        self.assert_passed(self.build())
        self.assertEqual((self.root / 'Package.resolved').read_bytes(), original)
        receipt = json.loads(self.receipt.read_text())
        self.assertIn('--force-resolved-versions', receipt['build']['arguments'])
        self.assertEqual(receipt['inputs']['sdk']['revision'], PIN)
        self.assertEqual(receipt['inputs']['sdk']['baseRevision'], BASE)
        self.assertEqual(receipt['inputs']['sdk']['selectionMode'], 'pinned')
        self.assertFalse(receipt['inputs']['sdk']['uncommittedMaintenancePatch'])
        self.assertEqual(receipt['inputs']['application']['sdkSelectionSHA256'],
                         hashlib.sha256((self.root / 'SDKSelection.json').read_bytes()).hexdigest())

    def test_pinned_archive_preserves_selection_and_rejects_later_selection_drift(self):
        self.pin_sdk()
        self.assert_passed(self.build())
        receipt = json.loads(self.receipt.read_text())
        target = receipt['build']['target']
        output = self.root / 'archives'
        # CHANGE: Exercise pinned archive provenance without executing a pretend native binary.
        args = ['--binary', str(self.binary), '--platform', target, '--execution', 'not-run']
        self.assert_passed(self.run_script('archive-pilot.py', *args, '--output', str(output)))
        archive = next(output.glob('*.tar.gz'))
        original_archive = hashlib.sha256(archive.read_bytes()).hexdigest()
        with tarfile.open(archive) as bundle:
            prefix = f'routeobjects-mcp-0.1.0-pilot-{target}'
            metadata = json.load(bundle.extractfile(prefix + '/BUILD-INFO.json'))
            archived_receipt = json.load(bundle.extractfile(prefix + '/BUILD-RECEIPT.json'))
            selected = bundle.extractfile(prefix + '/SDKSelection.json').read()
            licenses = {Path(member.name).parts[2] for member in bundle.getmembers()
                        if member.name.startswith(prefix + '/ThirdPartyLicenses/') and member.isfile()}
        self.assertEqual(selected, (self.root / 'SDKSelection.json').read_bytes())
        self.assertEqual(archived_receipt, receipt)
        self.assertEqual(hashlib.sha256(selected).hexdigest(), receipt['inputs']['application']['sdkSelectionSHA256'])
        self.assertEqual(metadata['sdk']['revision'], PIN)
        self.assertEqual(metadata['sdk']['baseRevision'], BASE)
        self.assertEqual(metadata['sdk']['selectionMode'], 'pinned')
        self.assertEqual(metadata['sdk']['repositoryURL'], FORK)
        self.assertFalse(metadata['sdk']['uncommittedMaintenancePatch'])
        self.assertFalse(metadata['releaseReady'])
        self.assertEqual(metadata['executionEvidence'], 'not-run')
        self.assertEqual(licenses, {pin['identity'] for pin in self.lock['pins']})
        selection = self.root / 'SDKSelection.json'
        selection.write_bytes(selection.read_bytes() + b'\n')
        rejected_output = self.root / 'rejected-archives'
        result = self.run_script('archive-pilot.py', *args, '--output', str(rejected_output))
        self.assert_rejected(result)
        self.assertIn('differs from the build receipt', result.stderr)
        self.assertEqual(list(rejected_output.glob('*.tar.gz')), [])
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), original_archive)

    def test_wrong_revision_is_rejected_before_compiler(self):
        self.pin_sdk()
        (self.sdk / '.fixture-HEAD').write_text(BASE)
        self.assert_rejected(self.build(), before_compiler=True)

    def test_pinned_dirty_checkout_is_rejected_before_compiler(self):
        self.pin_sdk()
        (self.sdk / '.fixture-status').write_text(' M Sources/Entry.swift\n')
        self.assert_rejected(self.build(), before_compiler=True)

    def test_pinned_wrong_origin_and_edit_are_rejected(self):
        self.pin_sdk()
        self.sdk_entry['packageRef']['location'] = UPSTREAM
        self.save_configuration()
        self.assert_rejected(self.build(), before_compiler=True)
        self.sdk_entry['packageRef']['location'] = FORK
        self.sdk_entry['state'] = {'name': 'edited', 'path': str(self.sdk)}
        self.save_configuration()
        self.assert_rejected(self.build(), before_compiler=True)

    def test_pinned_local_override_is_rejected(self):
        self.pin_sdk()
        result = self.run_script('build-pilot.py', '--sdk-path', str(self.sdk), 'build')
        self.assert_rejected(result, before_compiler=True)
        environment = dict(self.env, ROUTEOBJECTS_MCP_SDK_PATH=str(self.sdk))
        self.assert_rejected(self.build(env=environment), before_compiler=True)

    def test_pinned_missing_pin_is_rejected_before_compiler(self):
        self.pin_sdk()
        self.lock['pins'] = [p for p in self.lock['pins'] if p['identity'] != 'swift-sdk']
        self.save_configuration()
        self.assert_rejected(self.build(), before_compiler=True)

    def test_duplicate_sdk_pin_is_rejected_before_compiler(self):
        self.lock['pins'].append(next(p for p in self.lock['pins'] if p['identity'] == 'swift-sdk').copy())
        self.save_configuration()
        self.assert_rejected(self.build(), before_compiler=True)

    def test_invalid_pinned_revision_is_rejected_before_compiler(self):
        self.pin_sdk()
        self.selection['maintenance']['revision'] = 'main'
        self.save_configuration()
        self.assert_rejected(self.build(), before_compiler=True)

    def test_json_only_pin_change_is_rejected_before_cached_manifest_can_build(self):
        self.selection['maintenance']['revision'] = PIN
        self.save_configuration()
        self.assert_rejected(self.build(), before_compiler=True)

    def test_manifest_only_pin_change_is_rejected_before_compiler(self):
        manifest = self.root / 'Package.swift'
        manifest.write_text(manifest.read_text().replace('= nil', f'= "{PIN}"'))
        self.assert_rejected(self.build(), before_compiler=True)

    def test_ambiguous_manifest_pin_is_rejected_before_compiler(self):
        manifest = self.root / 'Package.swift'
        manifest.write_text(manifest.read_text() + 'let maintenanceSDKRevision: String? = nil\n')
        self.assert_rejected(self.build(), before_compiler=True)

    def test_pinned_workspace_cannot_select_checkout_outside_build_directory(self):
        self.pin_sdk()
        outside = self.workspace / 'outside-sdk'
        shutil.copytree(self.sdk, outside)
        for subpath in [str(outside), '../../../outside-sdk']:
            with self.subTest(subpath=subpath):
                self.sdk_entry['subpath'] = subpath
                self.save_configuration()
                self.assert_rejected(self.build(), before_compiler=True)

    def test_unapproved_sdk_source_and_lock_are_rejected(self):
        for target in ['Sources/Entry.swift', 'Package.resolved']:
            with self.subTest(target=target):
                path = self.sdk / target
                original = path.read_bytes()
                path.write_bytes(original + b'\n')
                self.assert_rejected(self.build(), before_compiler=True)
                path.write_bytes(original)

    def test_development_build_restores_complete_lock(self):
        original = (self.root / 'Package.resolved').read_bytes()
        self.assert_passed(self.build())
        self.assertEqual((self.root / 'Package.resolved').read_bytes(), original)
        receipt = json.loads(self.receipt.read_text())
        self.assertNotIn('--force-resolved-versions', receipt['build']['arguments'])
        self.assertEqual(receipt['inputs']['sdk']['selectionMode'], 'development')
        self.assertTrue(receipt['inputs']['sdk']['uncommittedMaintenancePatch'])

    def test_pinned_lock_drift_never_receives_receipt(self):
        self.pin_sdk()
        for marker in ['drift-pin', 'drop-sdk-pin', 'duplicate-pin']:
            with self.subTest(marker=marker):
                original = (self.root / 'Package.resolved').read_bytes()
                (self.root / marker).touch()
                self.assert_rejected(self.build())
                self.assertFalse(self.receipt.exists())
                self.assertEqual((self.root / 'Package.resolved').read_bytes(), original)
                (self.root / marker).unlink()

    def test_failed_rebuild_invalidates_receipt_and_restores_lock(self):
        for pinned in [False, True]:
            with self.subTest(pinned=pinned):
                if pinned:
                    self.pin_sdk()
                original = (self.root / 'Package.resolved').read_bytes()
                self.assert_passed(self.build())
                self.assertTrue(self.receipt.exists())
                (self.root / 'fail-build').touch()
                self.assert_rejected(self.build())
                self.assertFalse(self.receipt.exists())
                self.assertEqual((self.root / 'Package.resolved').read_bytes(), original)
                (self.root / 'fail-build').unlink()

    def test_selection_change_during_build_never_receives_receipt(self):
        original = (self.root / 'Package.resolved').read_bytes()
        (self.root / 'drift-selection').touch()
        self.assert_rejected(self.build())
        self.assertFalse(self.receipt.exists())
        self.assertEqual((self.root / 'Package.resolved').read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
