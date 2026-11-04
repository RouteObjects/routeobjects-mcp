#!/usr/bin/env python3
"""Create a review patch from an explicit, hash-checked publication manifest.

This does not discover a publication allowlist, stage files, or create commits.
The manifest must be reviewed separately and regenerated when approved bytes or
repository bases change. Output is a new, installation-local review directory.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile


class ReviewError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ReviewError(message)


def relative_path(value, *, repository=False):
    # CHANGE: Patch paths cannot escape a repository or address Git metadata.
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9._/@+-]+', value),
            f'Unsafe review path: {value!r}')
    parts = value.split('/')
    require(not value.startswith('/') and all(part not in ('', '.', '..') and part.casefold() != '.git' for part in parts),
            f'Unsafe review path: {value!r}')
    require(not repository or len(parts) == 1, f'Unsafe repository name: {value!r}')
    return PurePosixPath(value)


def guarded_path(root, relative):
    path = root
    for part in relative.parts:
        path /= part
        require(not path.is_symlink(), f'Symlink in review path: {relative}')
    return path


def git(repo, *arguments, check=True):
    result = subprocess.run(['git', '-C', str(repo), *arguments], capture_output=True)
    if check:
        require(result.returncode == 0, f'Git inspection failed in {repo.name}: {" ".join(arguments)}')
    return result


def check_repository(repo, base):
    require(git(repo, 'rev-parse', '--show-toplevel').stdout.decode().strip() == str(repo),
            f'Repository root mismatch: {repo.name}')
    head = git(repo, 'rev-parse', '--verify', 'HEAD', check=False)
    if base is None:
        require(head.returncode != 0, f'Expected unborn repository: {repo.name}')
    else:
        require(isinstance(base, str) and re.fullmatch(r'[0-9a-f]{40}', base),
                f'Invalid reviewed base: {repo.name}')
        require(head.returncode == 0 and head.stdout.decode().strip() == base,
                f'Repository base differs from manifest: {repo.name}')
    require(not git(repo, 'diff', '--cached', '--name-only', '-z').stdout,
            f'Unexpected staged files in {repo.name}: stop for review.')


def entries(section, field, count_field):
    values = section.get(field)
    require(isinstance(values, list) and type(section.get(count_field)) is int
            and section[count_field] == len(values), f'Manifest count mismatch: {field}')
    result = {}
    for entry in values:
        require(isinstance(entry, dict), f'Invalid manifest entry: {field}')
        relative_path(entry.get('path'))
        require(entry['path'] not in result, f'Duplicate review path: {entry["path"]}')
        require(entry.get('mode') in ('100644', '100755'), f'Unsupported file mode: {entry["path"]}')
        require(type(entry.get('bytes')) is int and entry['bytes'] >= 0,
                f'Invalid byte count: {entry["path"]}')
        require(isinstance(entry.get('sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', entry['sha256']),
                f'Invalid SHA-256: {entry["path"]}')
        result[entry['path']] = entry
    return result


def read_approved(repo, entry):
    path = guarded_path(repo, relative_path(entry['path']))
    require(path.is_file(), f'Missing regular review file: {repo.name}/{entry["path"]}')
    info = path.stat()
    require(stat.S_ISREG(info.st_mode), f'Not a regular review file: {entry["path"]}')
    mode = '100755' if info.st_mode & 0o111 else '100644'
    require(mode == entry['mode'], f'Review mode mismatch: {repo.name}/{entry["path"]}')
    data = path.read_bytes()
    require(len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'],
            f'Review hash or size mismatch: {repo.name}/{entry["path"]}')
    return data


def text_lines(data, path):
    require(b'\0' not in data, f'Binary review file is unsupported: {path}')
    try:
        return data.decode('utf-8').splitlines(keepends=True)
    except UnicodeDecodeError as error:
        raise ReviewError(f'Non-UTF-8 review file is unsupported: {path}') from error


def patch_for(repo, base, entry, after):
    relative = entry['path']
    before, old_mode = b'', None
    if base is not None:
        listing = git(repo, 'ls-tree', '-z', base, '--', relative).stdout
        if listing:
            require(listing.count(b'\0') == 1, f'Ambiguous baseline path: {relative}')
            metadata, listed_path = listing.rstrip(b'\0').split(b'\t', 1)
            mode, kind, blob = metadata.decode().split()
            require(listed_path.decode() == relative and kind == 'blob' and mode in ('100644', '100755'),
                    f'Unsupported baseline entry: {relative}')
            old_mode = mode
            before = git(repo, 'cat-file', 'blob', blob).stdout
    if old_mode == entry['mode'] and before == after:
        return ''
    target = f'{repo.name}/{relative}'
    output = [f'diff --git a/{target} b/{target}\n']
    if old_mode is None:
        output.append(f'new file mode {entry["mode"]}\n')
    elif old_mode != entry['mode']:
        output.extend([f'old mode {old_mode}\n', f'new mode {entry["mode"]}\n'])
    # CHANGE: Derive each hunk from the approved path only; an unrelated tracked diff cannot leak into the bundle.
    for line in difflib.unified_diff(text_lines(before, target), text_lines(after, target),
                                     fromfile='/dev/null' if old_mode is None else 'a/' + target,
                                     tofile='b/' + target):
        output.append(line)
        if not line.endswith('\n'):
            output.append('\n\\ No newline at end of file\n')
    return ''.join(output)


def create_bundle(manifest_path, workspace, output):
    workspace = workspace.resolve(strict=True)
    raw_manifest = manifest_path.read_bytes()
    manifest = json.loads(raw_manifest)
    require(isinstance(manifest, dict), 'Manifest must be a JSON object.')
    repositories = manifest.get('repositories')
    require(isinstance(repositories, dict) and repositories, 'Manifest must select repositories.')
    require(output.is_absolute(), 'Review output must be an absolute path.')
    try:
        output_relative = output.relative_to(workspace)
    except ValueError as error:
        raise ReviewError('Review output must be inside the selected workspace.') from error
    require(output_relative.parts and all(part.casefold() != '.git' for part in output_relative.parts)
            and '..' not in output_relative.parts, 'Unsafe review output path.')
    guarded_path(workspace, output_relative)
    require(not output.exists(), 'Review output already exists; choose a fresh directory.')
    patch, allowlist, checked = [], {}, []
    for name, section in sorted(repositories.items()):
        repo = guarded_path(workspace, relative_path(name, repository=True))
        require(isinstance(section, dict) and 'base' in section, f'Missing repository base: {name}')
        require(not section.get('deletedPaths'), 'Deletion manifests require a separately reviewed implementation.')
        check_repository(repo, section['base'])
        require(('files' in section) != ('changedOrAddedFiles' in section),
                f'Ambiguous manifest file selection: {name}')
        selected = entries(section, 'files', 'fileCount') if 'files' in section else entries(
            section, 'changedOrAddedFiles', 'changedOrAddedFileCount')
        # CHANGE: Full-tree SDK identity is verified, but only its approved delta is emitted.
        complete = entries(section, 'fullTreeFiles', 'fullTreeFileCount') if 'fullTreeFiles' in section else selected
        require(all(complete.get(path) == entry for path, entry in selected.items()),
                f'Delta disagrees with full-tree manifest: {name}')
        contents = {path: read_approved(repo, entry) for path, entry in complete.items()}
        allowlist[name] = sorted(selected)
        for relative in sorted(selected):
            patch.append(patch_for(repo, section['base'], selected[relative], contents[relative]))
        checked.append((repo, section['base'], complete))
    # CHANGE: Validate everything before creating output, then recheck snapshots and index ownership after Git reads.
    for repo, base, complete in checked:
        check_repository(repo, base)
        for entry in complete.values():
            read_approved(repo, entry)
    require(manifest_path.read_bytes() == raw_manifest, 'Manifest changed during review.')
    data = ''.join(patch).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.review-bundle-', dir=output.parent))
    try:
        (temporary / 'workspace.patch').write_bytes(data)
        (temporary / 'paths.json').write_text(json.dumps(allowlist, indent=2) + '\n')
        (temporary / 'workspace.patch.sha256').write_text(hashlib.sha256(data).hexdigest() + '  workspace.patch\n')
        (temporary / 'manifest-identity.json').write_text(json.dumps({
            'manifestSHA256': hashlib.sha256(raw_manifest).hexdigest(),
            'verifiedFileCounts': {repo.name: len(complete) for repo, _, complete in checked},
        }, indent=2) + '\n')
        temporary.rename(output)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {'patch': str(output / 'workspace.patch'), 'bytes': len(data),
            'paths': {name: len(paths) for name, paths in allowlist.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True, help='Explicit reviewed path/hash/mode manifest.')
    parser.add_argument('--workspace', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True, help='Fresh review directory inside the workspace.')
    args = parser.parse_args()
    try:
        print(json.dumps(create_bundle(args.manifest, args.workspace, args.output), indent=2))
    except (ReviewError, OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Review bundle refused: {error}\n')


if __name__ == '__main__':
    main()
