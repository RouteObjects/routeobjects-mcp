"""Build receipts for the local pilot; these are integrity records, not signatures."""
import hashlib
import json
import platform
import subprocess


class ProvenanceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ProvenanceError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_digest(root):
    digest = hashlib.sha256()
    # CHANGE: The selection controls compiled dependencies and flags, so it is part of application identity.
    for path in sorted([*root.glob('Package*.swift'), *root.glob('SDKSelection.json'), *root.glob('Sources/**/*')]):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode() + b'\0')
            digest.update(path.read_bytes() + b'\0')
    return digest.hexdigest()


def inputs(root, sdk):
    from sdk_selection import load_selection, selection_mode
    selection = load_selection(root)
    mode = selection_mode(selection)
    lock = root / 'Package.resolved'
    pins = json.loads(lock.read_bytes())['pins']
    require(any(pin['identity'] == 'swift-sdk' for pin in pins), 'Complete baseline lock required.')
    return {
        'application': {'sourceSHA256': source_digest(root), 'lockfileSHA256': sha256(lock),
                        'sdkSelectionSHA256': sha256(root / 'SDKSelection.json')},
        'sdk': {
            'baseRevision': selection['baseline']['revision'],
            'revision': subprocess.check_output(['git', '-C', str(sdk), 'rev-parse', 'HEAD'], text=True).strip(),
            'repositoryURL': selection['maintenance']['repositoryURL'],
            'selectionMode': mode,
            'uncommittedMaintenancePatch': mode == 'development',
            'sourceSHA256': source_digest(sdk),
            'lockfileSHA256': sha256(sdk / 'Package.resolved'),
        },
        'dependencies': pins,
    }


def host():
    return {'system': platform.system(), 'release': platform.release(), 'architecture': platform.machine()}


def target(architecture=None):
    system = {'Darwin': 'macos', 'Linux': 'linux'}.get(platform.system())
    arch = architecture or {'aarch64': 'arm64', 'AMD64': 'x86_64'}.get(platform.machine(), platform.machine())
    require(system is not None and arch in ('arm64', 'x86_64'), 'Unsupported pilot build target.')
    return f'{system}-{arch}'


def receipt_path(binary):
    return binary.with_name(binary.name + '.build-receipt.json')


def write_receipt(path, binary, source_inputs, build):
    # CHANGE: Only the successful build driver issues receipts; packaging cannot manufacture provenance.
    receipt = {
        'schemaVersion': 1,
        'name': 'routeobjects-mcp',
        'version': '0.1.0',
        'inputs': source_inputs,
        'build': build,
        'binary': {
            'name': 'routeobjects-mcp',
            'sha256': sha256(binary),
        },
        'postProcessing': [],
    }
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(receipt, indent=2) + '\n')
    temporary.replace(path)
    return receipt


def validate_receipt(path, binary, root, sdk, requested_target):
    require(path.is_file(), 'Missing build receipt: rebuild with Scripts/build-pilot.py build.')
    try:
        raw = path.read_bytes()
        receipt = json.loads(raw)
        require(receipt['schemaVersion'] == 1 and receipt['name'] == 'routeobjects-mcp'
                and receipt['version'] == '0.1.0', 'Unsupported build receipt.')
        require(receipt['postProcessing'] == [], 'Post-build transformations are not supported; rebuild the executable.')
        require(receipt['binary']['sha256'] == sha256(binary), 'Executable differs from the build receipt; rebuild it.')
        require(receipt['build']['target'] == requested_target, 'Archive target differs from the build receipt.')
        require(receipt['build']['configuration'] in ('debug', 'release')
                and isinstance(receipt['build']['arguments'], list)
                and receipt['build']['arguments'][0] == 'build'
                and isinstance(receipt['build']['swift'], str)
                and isinstance(receipt['build']['compilerDefaultTarget'], dict)
                and isinstance(receipt['build']['host'], dict), 'Incomplete build metadata.')
        # CHANGE: Require the same compiled inputs and complete locks, not just a matching --version.
        require(receipt['inputs'] == inputs(root, sdk), 'Source, SDK revision, or dependency lock differs from the build receipt.')
        return receipt, hashlib.sha256(raw).hexdigest()
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise ProvenanceError('Malformed or incomplete build receipt.') from error
