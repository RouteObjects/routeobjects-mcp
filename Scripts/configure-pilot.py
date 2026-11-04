#!/usr/bin/env python3
"""Configure reviewed dependencies without changing their canonical lock."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from pilot_provenance import require
from sdk_selection import load_selection, selection_mode, verify_lock, verify_sdk

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('sdk_path', nargs='?', type=Path, help='Explicit local checkout, development mode only.')
args = parser.parse_args()
selection = load_selection(root)
mode = selection_mode(selection)
sdk = verify_sdk(root, selection, args.sdk_path, selection_only=True)
lock = root / 'Package.resolved'
original = lock.read_bytes()
expected = verify_lock(root, selection)
state = root / '.build/workspace-state.json'
dependencies = json.loads(state.read_bytes())['object']['dependencies'] if state.exists() else []
selected = [d for d in dependencies if d['packageRef']['identity'] == 'swift-sdk']
if selected and selected[0]['state']['name'] == 'edited':
    # CHANGE: Never unedit or replace a caller's checkout to satisfy a newly selected pin.
    require(mode == 'development', 'Remove the existing SDK edit explicitly before configuring an immutable pin.')
    verify_sdk(root, selection, args.sdk_path)
else:
    environment = os.environ.copy()
    if mode == 'development':
        environment['ROUTEOBJECTS_MCP_SDK_PATH'] = str(sdk)
    try:
        subprocess.run(['swift', 'package', '--force-resolved-versions', 'resolve'], cwd=root, env=environment, check=True)
        if mode == 'development':
            subprocess.run(['swift', 'package', 'edit', 'swift-sdk', '--path', str(sdk)], cwd=root, env=environment, check=True)
        actual_list = json.loads(lock.read_bytes())['pins']
        actual = {pin['identity']: pin for pin in actual_list}
        require(len(actual_list) == len(actual), 'Duplicate dependency identity.')
        allowed = (set(expected), set(expected) - {'swift-sdk'}) if mode == 'development' else (set(expected),)
        require(set(actual) in allowed and all(pin == expected[name] for name, pin in actual.items()),
                'Dependency graph changed during configuration.')
    finally:
        lock.write_bytes(original)
require(load_selection(root) == selection, 'SDK selection changed during configuration.')
verify_sdk(root, selection, args.sdk_path)
print(f'Configured {mode} SDK selection; complete dependency lock retained.')
