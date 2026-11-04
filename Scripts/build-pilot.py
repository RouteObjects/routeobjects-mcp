#!/usr/bin/env python3
"""Build the reviewed local patch or immutable SDK without allowing lock drift.

SwiftPM force-resolved mode discards edits. Ordinary editable mode omits the SDK
pin when it rewrites Package.resolved. Compare the entire remaining graph and
SDK base/source identity, then restore the complete canonical lock bytes.
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

from pilot_provenance import host, inputs, receipt_path, require, target, write_receipt
from sdk_selection import load_selection, selection_mode, verify_sdk

root = pathlib.Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--sdk-path', type=pathlib.Path)
parser.add_argument('command', choices=['build', 'test'])
parser.add_argument('--configuration', choices=['debug', 'release'], default='debug')
parser.add_argument('--static-swift-stdlib', action='store_true')
parser.add_argument('--linker-strip-all', action='store_true',
                    help='Omit symbols during a Linux Release build; the receipt records the linker option.')
parser.add_argument('--arch', choices=['arm64', 'x86_64'])
args = parser.parse_args()
if args.linker_strip_all and (args.command != 'build' or args.configuration != 'release'
                             or host()['system'] != 'Linux'):
    parser.error('--linker-strip-all requires a Linux Release build.')
selection = load_selection(root)
mode = selection_mode(selection)
sdk_override = args.sdk_path
if mode == 'development' and sdk_override is None:
    sdk_override = pathlib.Path(os.environ.get('ROUTEOBJECTS_MCP_SDK_PATH', root.parent / 'swift-sdk'))
sdk = verify_sdk(root, selection, sdk_override)
lock_path = root / 'Package.resolved'
original = lock_path.read_bytes()
expected = {p['identity']: p for p in json.loads(original)['pins']}

def verify():
    require(load_selection(root) == selection, 'SDK selection changed during build.')
    require(verify_sdk(root, selection, sdk_override) == sdk, 'SDK checkout changed during build.')

verify()
inputs_before = inputs(root, sdk)
environment = os.environ.copy()
if mode == 'development':
    environment['ROUTEOBJECTS_MCP_SDK_PATH'] = str(sdk)
# CHANGE: Immutable mode uses SwiftPM's locked resolution and cannot omit the SDK pin.
options = ['--skip-update', *(['--force-resolved-versions'] if mode == 'pinned' else []), '-c', args.configuration]
if args.arch:
    # CHANGE: Cross-build explicitly without changing the canonical dependency graph.
    options.extend(['--arch', args.arch])
if args.static_swift_stdlib:
    options.append('--static-swift-stdlib')
if args.linker_strip_all:
    # CHANGE: Reduce distribution size at link time so the receipt binds final bytes, without post-build stripping.
    options.extend(['-Xlinker', '--strip-all'])
command = ['swift', args.command, *options]
if args.command == 'build':
    command.extend(['--product', 'routeobjects-mcp'])
receipt = None
binary = None
code = 1
try:
    if args.command == 'build':
        # CHANGE: SwiftPM selects the target output directory; never certify an arbitrary supplied binary.
        bin_path = subprocess.check_output(
            ['swift', 'build', *options, '--show-bin-path'], cwd=root, env=environment, text=True).strip()
        binary = pathlib.Path(bin_path) / 'routeobjects-mcp'
        receipt = receipt_path(binary)
        receipt.unlink(missing_ok=True)
        build = {
            'configuration': args.configuration,
            'arguments': command[1:],
            'requestedArchitecture': args.arch,
            'staticSwiftStdlib': args.static_swift_stdlib,
            'target': target(args.arch),
            'swift': subprocess.check_output(['swift', '--version'], text=True, stderr=subprocess.STDOUT).strip(),
            # CHANGE: This is the compiler's default, not SwiftPM's selected architecture/deployment target.
            'compilerDefaultTarget': json.loads(subprocess.check_output(['swift', '-print-target-info'], text=True))['target'],
            'host': host(),
        }
    code = subprocess.run(command, cwd=root, env=environment).returncode
    actual_list = json.loads(lock_path.read_bytes())['pins']
    actual = {p['identity']: p for p in actual_list}
    require(len(actual_list) == len(actual), 'Duplicate dependency identity.')
    # CHANGE: The sole permitted lockfile difference is omission of the explicitly edited SDK pin.
    allowed = (set(expected), set(expected) - {'swift-sdk'}) if mode == 'development' else (set(expected),)
    require(set(actual) in allowed, 'Dependency identities changed.')
    require(all(pin == expected[name] for name, pin in actual.items()), 'A dependency pin changed.')
finally:
    lock_path.write_bytes(original)
require(inputs(root, sdk) == inputs_before, 'Source, SDK revision, or lock changed during build; retry with a stable checkout.')
verify()
if code == 0 and receipt is not None:
    require(binary.is_file(), 'Successful build did not produce the executable.')
    write_receipt(receipt, binary, inputs_before, build)
    print(f'Build receipt: {receipt}', flush=True)
print(f'Locked graph retained; SDK source SHA-256: {inputs_before["sdk"]["sourceSHA256"]}', flush=True)
sys.exit(code)
