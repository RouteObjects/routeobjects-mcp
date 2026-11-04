#!/usr/bin/env python3
"""Exercise an already installed Inspector; never download tools or start a model."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ['cidr_inspect', 'cidr_contains', 'cidr_relation', 'cidr_summarize_range']


def environment(output, node):
    return {**os.environ, 'PATH': str(node.parent) + os.pathsep + os.environ.get('PATH', os.defpath),
            'MCP_STORAGE_DIR': str(output / 'storage'),
            'MCP_CLIENT_CONFIG_PATH': str(output / 'client.json'),
            'MCP_INSPECTOR_LOG_DIR': str(output / 'logs'),
            'MCP_INSPECTOR_SECRET_STORE': 'memory', 'MCP_INSPECTOR_PERSIST_TOKENS': 'none',
            'MCP_AUTO_OPEN_ENABLED': 'false'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', type=Path, default=ROOT / '.verification/node-v22.23.4-darwin-arm64/bin/node')
    parser.add_argument('--inspector-package', type=Path,
                        default=ROOT / '.verification/inspector/node_modules/@modelcontextprotocol/inspector')
    parser.add_argument('--binary', type=Path, default=ROOT / '.build/debug/routeobjects-mcp')
    parser.add_argument('--output', type=Path, default=ROOT / '.verification/inspector-session')
    args = parser.parse_args()
    node, package, binary, output = [p.resolve() for p in
                                     (args.node, args.inspector_package, args.binary, args.output)]
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output, 0o700)
    config = output / 'config.json'
    config.write_text(json.dumps({'mcpServers': {
        f'routeobjects-{era}': {'command': str(binary), 'args': [], 'type': 'stdio',
                            'protocolEra': era, 'connectionTimeout': 5000, 'requestTimeout': 5000}
        for era in ('legacy', 'auto', 'modern')}}, indent=2) + '\n')
    env = environment(output, node)
    launcher = package / 'clients/launcher/build/index.js'
    results = []
    for era in ('legacy', 'auto'):
        cases = [('list', ['--method', 'tools/list', '--strict'], 0),
                 ('context', ['--method', 'tools/call', '--tool-name', 'cidr_inspect',
                              '--tool-args-json', '{"kind":"address_with_prefix","value":"192.0.2.129/24"}'], 0),
                 ('ipv6-full', ['--method', 'tools/call', '--tool-name', 'cidr_inspect',
                                '--tool-args-json', '{"kind":"network","value":"::/0"}'], 0),
                 ('invalid', ['--method', 'tools/call', '--tool-name', 'cidr_inspect',
                              '--tool-args-json', '{"kind":"address","value":"not-an-address"}'], 5)]
        # CHANGE: qualify every public tool through the real client, including domain errors.
        for name, tool, arguments, expected in [
            ('contains', 'cidr_contains', {'container': '192.0.2.0/24',
                'target': {'kind': 'network', 'value': '192.0.2.0/25'}}, 0),
            ('contains-invalid', 'cidr_contains', {'container': '192.0.2.0/24',
                'target': {'kind': 'address', 'value': '::1'}}, 5),
            ('relation', 'cidr_relation', {'left': '192.0.2.0/24', 'right': '192.0.2.0/25'}, 0),
            ('relation-invalid', 'cidr_relation', {'left': '192.0.2.0/24', 'right': '::/0'}, 5),
            ('range', 'cidr_summarize_range', {'start': '192.0.2.1', 'end': '192.0.2.6'}, 0),
            ('range-invalid', 'cidr_summarize_range', {'start': '192.0.2.6', 'end': '192.0.2.1'}, 5),
        ]:
            cases.append((name, ['--method', 'tools/call', '--tool-name', tool,
                                 '--tool-args-json', json.dumps(arguments)], expected))
        for name, flags, expected in cases:
            command = [str(node), str(launcher), '--cli', '--config', str(config),
                       '--server', f'routeobjects-{era}', '--format', 'json', *flags]
            completed = subprocess.run(command, env=env, capture_output=True, text=True, timeout=25)
            stem = f'cli-{era}-{name}'
            (output / f'{stem}.stdout.json').write_text(completed.stdout)
            (output / f'{stem}.stderr.txt').write_text(completed.stderr)
            assert completed.returncode == expected, f'{stem}: unexpected exit {completed.returncode}'
            result = json.loads(completed.stdout)['result']
            if name == 'list':
                assert [tool['name'] for tool in result['tools']] == TOOLS
            else:
                data = result['structuredContent']
                text = next(item['text'] for item in result['content'] if item['type'] == 'text')
                assert json.loads(text) == data
                if name == 'context':
                    assert data['result']['address'] == '192.0.2.129'
                    assert data['result']['network']['cidr'] == '192.0.2.0/24'
                elif name == 'ipv6-full':
                    assert data['result']['network']['addressCount'] == str(2 ** 128)
                elif name == 'contains':
                    assert data['result']['contains'] is True
                    assert data['result']['basis'] == 'network_containment'
                elif name == 'relation':
                    assert data['result']['relation'] == 'left_contains_right'
                    assert data['result']['overlaps'] is True
                elif name == 'range':
                    assert data['result']['addressCount'] == '6'
                    assert data['result']['prefixes'] == [
                        '192.0.2.1/32', '192.0.2.2/31', '192.0.2.4/31', '192.0.2.6/32']
                else:
                    code = {'invalid': 'invalid_address', 'contains-invalid': 'family_mismatch',
                            'relation-invalid': 'family_mismatch', 'range-invalid': 'reversed_range'}[name]
                    assert result['isError'] is True and data['error']['code'] == code
                if expected == 0:
                    assert result.get('isError', False) is False and data['error'] is None
            results.append({'case': stem, 'status': 'PASS', 'exit': completed.returncode})
    completed = subprocess.run([str(node), str(launcher), '--cli', '--config', str(config),
                               '--server', 'routeobjects-modern', '--format', 'json', '--method', 'tools/list'],
                              env=env, capture_output=True, text=True, timeout=25)
    (output / 'cli-modern-list.stdout.json').write_text(completed.stdout)
    (output / 'cli-modern-list.stderr.txt').write_text(completed.stderr)
    assert completed.returncode == 1 and 'Version negotiation failed' in completed.stderr
    assert '2026-07-28' in completed.stderr and 'server/discover' in completed.stderr
    results.append({'case': 'cli-modern-list', 'status': 'EXPECTED_INCOMPATIBILITY', 'exit': 1})
    summary = {'inspectorVersion': json.loads((package / 'package.json').read_text())['version'],
               'nodeVersion': subprocess.check_output([str(node), '--version'], text=True).strip(),
               'binarySHA256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'results': results}
    (output / 'cli-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
