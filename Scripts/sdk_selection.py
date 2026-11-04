"""Validate reviewed local SDK inputs or an explicitly pinned maintenance revision."""
import json
import os
from pathlib import Path
import re
import subprocess

from pilot_provenance import require, sha256, source_digest


def load_selection(root):
    selection = json.loads((root / 'SDKSelection.json').read_bytes())
    require(selection.get('schemaVersion') == 1, 'Unsupported SDK selection.')
    baseline, patch = selection['baseline'], selection['maintenance']
    require(baseline == {
        'repositoryURL': 'https://github.com/modelcontextprotocol/swift-sdk.git',
        'version': '0.12.1', 'revision': 'a0ae212ebf6eab5f754c3129608bc5557637e605',
    }, 'Review SDK baseline changes separately.')
    require(patch['repositoryURL'] == 'https://github.com/RouteObjects/swift-sdk.git',
            'Unexpected maintenance SDK repository.')
    revision = patch['revision']
    require(revision is None or (isinstance(revision, str)
            and re.fullmatch('[0-9a-f]{40}', revision) and revision != baseline['revision']),
            'Maintenance revision must be null or an exact non-baseline commit.')
    # CHANGE: SwiftPM caches manifests without observing arbitrary JSON reads; the pin must be a manifest literal.
    literals = re.findall(r'^let maintenanceSDKRevision: String\? = (nil|"[0-9a-f]{40}")$',
                          (root / 'Package.swift').read_text(), re.MULTILINE)
    require(len(literals) == 1, 'Expected one literal maintenanceSDKRevision in Package.swift.')
    declared = None if literals[0] == 'nil' else json.loads(literals[0])
    require(declared == revision, 'Package.swift and SDKSelection.json revisions disagree.')
    for name in ['sourceSHA256', 'lockfileSHA256']:
        require(isinstance(patch[name], str) and re.fullmatch('[0-9a-f]{64}', patch[name]),
                'Invalid reviewed SDK digest.')
    return selection


def selection_mode(selection):
    return 'pinned' if selection['maintenance']['revision'] is not None else 'development'


def verify_lock(root, selection):
    pins_list = json.loads((root / 'Package.resolved').read_bytes())['pins']
    pins = {pin['identity']: pin for pin in pins_list}
    require(len(pins_list) == len(pins) == 9, 'Review the complete nine-package dependency graph.')
    for identity, version in {'swift-cidr': '0.8.1', 'swift-log': '1.6.2', 'swift-system': '1.4.0'}.items():
        require(pins.get(identity, {}).get('state', {}).get('version') == version,
                f'Unexpected {identity} version.')
    for pin in pins.values():
        require(re.fullmatch('[0-9a-f]{40}', pin['state']['revision']) is not None,
                'Invalid dependency revision.')
    expected = selection['maintenance'] if selection_mode(selection) == 'pinned' else selection['baseline']
    sdk = pins.get('swift-sdk', {})
    require(sdk.get('location') == expected['repositoryURL'] and sdk.get('kind') == 'remoteSourceControl',
            'SDK lock repository mismatch.')
    require(sdk.get('state', {}).get('revision') == expected['revision'], 'SDK lock revision mismatch.')
    if selection_mode(selection) == 'pinned':
        require(set(sdk['state']) == {'revision'}, 'Pinned SDK lock must select only an immutable revision.')
    else:
        require(sdk['state'].get('version') == expected['version'], 'SDK baseline version mismatch.')
    return pins


def verify_sdk(root, selection, sdk_path=None, scratch_path=None, *, selection_only=False):
    """Return the validated actual checkout; no resolve, edits, or Git mutations."""
    verify_lock(root, selection)
    mode = selection_mode(selection)
    scratch = scratch_path or root / '.build'
    if mode == 'pinned':
        # CHANGE: A published pin must never silently fall back to an editable SDK.
        require(sdk_path is None and 'ROUTEOBJECTS_MCP_SDK_PATH' not in os.environ,
                'Pinned SDK selection rejects local SDK overrides.')
        if selection_only:
            return None
    sdk = Path(sdk_path or os.environ.get('ROUTEOBJECTS_MCP_SDK_PATH', root.parent / 'swift-sdk')).resolve(strict=True) if mode == 'development' else None
    if not selection_only:
        require((scratch / 'workspace-state.json').is_file(), 'Configure dependencies before building.')
        dependencies = json.loads((scratch / 'workspace-state.json').read_bytes())['object']['dependencies']
        matches = [d for d in dependencies if d['packageRef']['identity'] == 'swift-sdk']
        require(len(matches) == 1, 'Expected one selected SDK dependency.')
        dependency = matches[0]
        if mode == 'development':
            require(dependency['state']['name'] == 'edited', 'SDK must be explicitly in SwiftPM editable mode.')
            require(Path(dependency['state']['path']).resolve() == sdk, 'Edited SDK path mismatch.')
            require(dependency['packageRef']['location'] == selection['baseline']['repositoryURL'],
                    'Edited SDK repository mismatch.')
        else:
            require(dependency['state']['name'] == 'sourceControlCheckout', 'Pinned SDK cannot be edited.')
            require(dependency['packageRef']['location'] == selection['maintenance']['repositoryURL'],
                    'Pinned SDK checkout repository mismatch.')
            require(dependency['state']['checkoutState']['revision'] == selection['maintenance']['revision'],
                    'Pinned SDK checkout revision mismatch.')
            subpath = Path(dependency['subpath'])
            require(len(subpath.parts) == 1 and subpath.name not in ('.', '..'), 'Unsafe SDK checkout subpath.')
            checkouts = (scratch / 'checkouts').resolve(strict=True)
            sdk = (checkouts / subpath).resolve(strict=True)
            require(sdk.parent == checkouts, 'SDK checkout escapes dependency directory.')
    revision = subprocess.check_output(['git', '-C', str(sdk), 'rev-parse', 'HEAD'], text=True).strip()
    expected = selection['baseline']['revision'] if mode == 'development' else selection['maintenance']['revision']
    require(revision == expected, 'SDK HEAD differs from the selected revision.')
    # CHANGE: Stable-but-unreviewed local source is insufficient; bind the independent approved inputs.
    require(source_digest(sdk) == selection['maintenance']['sourceSHA256'], 'SDK source differs from reviewed selection.')
    require(sha256(sdk / 'Package.resolved') == selection['maintenance']['lockfileSHA256'],
            'SDK lock differs from reviewed selection.')
    if mode == 'pinned':
        status = subprocess.check_output(['git', '-C', str(sdk), 'status', '--porcelain', '--untracked-files=normal'], text=True)
        require(not status.strip(), 'Pinned SDK checkout must be clean.')
    return sdk
