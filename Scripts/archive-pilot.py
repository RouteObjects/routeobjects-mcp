#!/usr/bin/env python3
"""Package a local pilot, with source identity, dependency inventory and licenses.

This does not publish, sign, notarize, or assert qualification on another host.
"""
import argparse
import hashlib
import json
import pathlib
import platform
import shutil
import subprocess
import tarfile
import tempfile

from pilot_provenance import ProvenanceError, receipt_path, require, sha256, validate_receipt
from sdk_selection import load_selection, selection_mode, verify_sdk

root = pathlib.Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--binary', type=pathlib.Path, required=True)
p.add_argument('--receipt', type=pathlib.Path, help='Build receipt; defaults to the executable sibling .build-receipt.json.')
p.add_argument('--sdk-path', type=pathlib.Path)
p.add_argument('--platform', required=True, choices=['macos-arm64','macos-x86_64','linux-arm64','linux-x86_64'])
p.add_argument('--execution', required=True, choices=['native','emulated','not-run'])
p.add_argument('--output', type=pathlib.Path, default=root / 'artifacts')
a = p.parse_args()
binary = a.binary.resolve(strict=True)
selection = load_selection(root)
# CHANGE: Pinned archives must use the selected immutable checkout, never a sibling development edit.
sdk = verify_sdk(root, selection, a.sdk_path)
receipt_file = a.receipt.resolve() if a.receipt else receipt_path(binary)
try:
    receipt, receipt_digest = validate_receipt(receipt_file, binary, root, sdk, a.platform)
except ProvenanceError as error:
    p.error(str(error))
a.output.mkdir(parents=True, exist_ok=True)
name = f'routeobjects-mcp-0.1.0-pilot-{a.platform}'
archive = a.output / (name + '.tar.gz')
require(not archive.exists(), 'Archive exists: use a fresh output directory to preserve prior evidence.')
file_description = subprocess.check_output(['file', '-b', str(binary)], text=True).strip()
architecture = 'arm64' if a.platform.endswith('arm64') else 'x86_64'
require(any(x in file_description for x in (['arm64','aarch64'] if architecture == 'arm64' else ['x86_64','x86-64'])), file_description)
if a.execution == 'native':
    require(platform.machine() in (['arm64','aarch64'] if architecture == 'arm64' else ['x86_64','AMD64']), 'Native architecture mismatch.')
    require(('macos' if platform.system() == 'Darwin' else platform.system().lower()) == a.platform.split('-')[0], 'Native platform mismatch.')
if a.execution != 'not-run':
    require(subprocess.check_output([str(binary), '--version'], text=True) == 'routeobjects-mcp 0.1.0\n', 'Executable version mismatch.')
build_inputs = receipt['inputs']
manifest = {
    'name':'routeobjects-mcp', 'version':'0.1.0', 'channel':'local-pilot', 'releaseReady':False,
    # CHANGE: Build claims come from the verified receipt, never the packaging host's current source/toolchain.
    'target':a.platform, 'executionEvidence':a.execution, 'sourceSHA256':build_inputs['application']['sourceSHA256'],
    'lockfileSHA256':build_inputs['application']['lockfileSHA256'],
    'buildHost':receipt['build']['host'], 'swift':receipt['build']['swift'], 'build':receipt['build'],
    'binarySHA256':receipt['binary']['sha256'], 'binaryFormat':file_description,
    'sdk':{'baseline':selection['baseline']['version'], **build_inputs['sdk']},
    'dependencies':build_inputs['dependencies'], 'buildReceiptSHA256':receipt_digest,
}
with tempfile.TemporaryDirectory(prefix='cidr-archive-') as temporary:
    destination = pathlib.Path(temporary) / name
    (destination / 'bin').mkdir(parents=True)
    shutil.copy2(binary, destination / 'bin/routeobjects-mcp')
    (destination / 'bin/routeobjects-mcp').chmod(0o755)
    # CHANGE: Recheck the bytes actually archived, catching changes after the first validation.
    require(sha256(destination / 'bin/routeobjects-mcp') == receipt['binary']['sha256'], 'Executable changed while preparing the archive.')
    shutil.copy2(receipt_file, destination / 'BUILD-RECEIPT.json')
    require(sha256(destination / 'BUILD-RECEIPT.json') == manifest['buildReceiptSHA256'], 'Build receipt changed while preparing the archive.')
    for filename in ['README.md','CONTRACTS.md','LICENSE','Package.resolved','SDKSelection.json']:
        shutil.copy2(root / filename, destination / filename)
    shutil.copytree(root / 'Docs', destination / 'Docs')
    shutil.copytree(root / 'ThirdPartyNotices', destination / 'ThirdPartyNotices')
    (destination / 'BUILD-INFO.json').write_text(json.dumps(manifest,indent=2)+'\n')
    licenses = destination / 'ThirdPartyLicenses'
    licenses.mkdir()
    for pin in build_inputs['dependencies']:
        source = sdk if pin['identity'] == 'swift-sdk' else root / '.build/checkouts' / pin['identity']
        matches = sorted(path for path in source.glob('*') if path.is_file() and (path.name.lower().startswith('license') or path.name.lower().startswith('notice')))
        require(matches, f'Missing license for {pin["identity"]}')
        target = licenses / pin['identity']; target.mkdir()
        for path in matches: shutil.copy2(path, target / path.name)
    require(sha256(destination / 'Package.resolved') == build_inputs['application']['lockfileSHA256'], 'Dependency lock changed while preparing the archive.')
    require(sha256(destination / 'SDKSelection.json') == build_inputs['application']['sdkSelectionSHA256'], 'SDK selection changed while preparing the archive.')
    validate_receipt(receipt_file, binary, root, sdk, a.platform)
    with tarfile.open(archive, 'w:gz') as tar:
        tar.add(destination, arcname=name)
checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
(archive.parent / (archive.name + '.sha256')).write_text(f'{checksum}  {archive.name}\n')
print(json.dumps({'archive':str(archive),'sha256':checksum,'releaseReady':False},indent=2))
