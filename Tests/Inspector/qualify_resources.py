#!/usr/bin/env python3
"""Check the bundled guide with an installed Inspector and qualify_cli.py session."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from qualify_cli import ROOT, environment

URI = 'routeobjects://routeobjects-mcp/guides/cips-v1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    node = ROOT / '.verification/node-v22.23.4-darwin-arm64/bin/node'
    package = ROOT / '.verification/inspector/node_modules/@modelcontextprotocol/inspector'
    launcher = package / 'clients/launcher/build/index.js'
    config = output / 'config.json'
    env = environment(output, node)
    results = []
    guide = None
    for era in ('legacy', 'auto'):
        for name, method, flags in (
            ('list', 'resources/list', []),
            ('read', 'resources/read', ['--uri', URI]),
            ('templates', 'resources/templates/list', []),
        ):
            command = [str(node), str(launcher), '--cli', '--config', str(config),
                       '--server', f'routeobjects-{era}', '--format', 'json', '--method', method, *flags]
            completed = subprocess.run(command, env=env, capture_output=True, text=True, timeout=25)
            stem = f'cli-{era}-resource-{name}'
            (output / f'{stem}.stdout.json').write_text(completed.stdout)
            (output / f'{stem}.stderr.txt').write_text(completed.stderr)
            assert completed.returncode == 0, f'{stem}: unexpected exit {completed.returncode}'
            result = json.loads(completed.stdout)['result']
            if name == 'list':
                assert len(result['resources']) == 1
                resource = result['resources'][0]
                assert resource['uri'] == URI and resource['mimeType'] == 'text/markdown'
            elif name == 'read':
                assert len(result['contents']) == 1
                content = result['contents'][0]
                assert content['uri'] == URI and content['mimeType'] == 'text/markdown'
                assert len(content['text'].encode()) == resource['size']
                assert 'draft-munro-cips-00' in content['text']
                # CHANGE: Both negotiation modes must deliver the identical complete bundled text.
                if guide is not None:
                    assert content['text'] == guide
                guide = content['text']
            else:
                assert result == {'resourceTemplates': []}
            results.append({'case': stem, 'status': 'PASS'})
    summary = {'uri': URI, 'guideBytes': len(guide.encode()),
               'guideSHA256': hashlib.sha256(guide.encode()).hexdigest(), 'results': results}
    (output / 'resource-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
