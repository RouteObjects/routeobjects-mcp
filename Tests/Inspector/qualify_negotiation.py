#!/usr/bin/env python3
"""Capture actual Inspector legacy negotiation and auto fallback on synthetic discovery."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ['cidr_inspect', 'cidr_contains', 'cidr_relation', 'cidr_summarize_range']
VERSIONS = {'2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', type=Path, default=ROOT / '.verification/node-v22.23.4-darwin-arm64/bin/node')
    parser.add_argument('--inspector-package', type=Path,
                        default=ROOT / '.verification/inspector/node_modules/@modelcontextprotocol/inspector')
    parser.add_argument('--binary', type=Path, default=ROOT / '.build/release/routeobjects-mcp')
    parser.add_argument('--expected-binary-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    node, package, binary, output = [p.resolve() for p in
                                     (args.node, args.inspector_package, args.binary, args.output)]
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == args.expected_binary_sha256
    assert json.loads((package / 'package.json').read_text())['version'] == '2.13.0'
    assert subprocess.check_output([str(node), '--version'], text=True).strip() == 'v22.23.4'
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    relay = Path(__file__).with_name('stdio_negotiation_relay.py').resolve()
    results = []
    for era in ('legacy', 'auto'):
        session = output / era
        session.mkdir(mode=0o700)
        events = session / 'wire'
        events.mkdir(mode=0o700)
        config = session / 'config.json'
        config.write_text(json.dumps({'mcpServers': {'qualification': {
            'command': sys.executable, 'args': [str(relay), '--binary', str(binary), '--events', str(events)],
            'type': 'stdio', 'protocolEra': era, 'connectionTimeout': 5000, 'requestTimeout': 5000,
        }}}) + '\n')
        environment = {**os.environ,
            'PATH': str(node.parent) + os.pathsep + os.environ.get('PATH', os.defpath),
            'MCP_STORAGE_DIR': str(session / 'storage'), 'MCP_CLIENT_CONFIG_PATH': str(session / 'client.json'),
            'MCP_INSPECTOR_LOG_DIR': str(session / 'logs'), 'MCP_INSPECTOR_SECRET_STORE': 'memory',
            'MCP_INSPECTOR_PERSIST_TOKENS': 'none', 'MCP_AUTO_OPEN_ENABLED': 'false'}
        command = [str(node), str(package / 'clients/launcher/build/index.js'), '--cli',
                   '--config', str(config), '--server', 'qualification', '--format', 'json',
                   '--method', 'tools/list', '--strict']
        started = time.monotonic_ns()
        process = subprocess.Popen(command, env=environment, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=25)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=5)
            raise
        ended = time.monotonic_ns()
        assert process.returncode == 0
        assert [tool['name'] for tool in json.loads(stdout)['result']['tools']] == TOOLS
        wire = sorted([json.loads(line) for path in events.glob('*.jsonl')
                       for line in path.read_text().splitlines()], key=lambda event: event['monotonicNs'])
        assert not any(event['event'] in {'relay_failure', 'relay_deadline'} for event in wire)
        initialized = [event for event in wire if 'negotiatedProtocolVersion' in event]
        assert len(initialized) == 1 and initialized[0]['negotiatedProtocolVersion'] in VERSIONS
        lists = [event for event in wire if event.get('method') == 'tools/list' and event['event'] == 'response']
        assert len(lists) == 1 and lists[0]['toolCount'] == 4
        row = {'era': era, 'exit': process.returncode, 'negotiatedProtocolVersion': initialized[0]['negotiatedProtocolVersion'],
               'launchToInitializationMs': (initialized[0]['monotonicNs'] - started) / 1_000_000,
               'launchToDiscoveryMs': (lists[0]['monotonicNs'] - started) / 1_000_000,
               'totalCLIElapsedMs': (ended - started) / 1_000_000,
               'stdoutBytes': len(stdout), 'stderrBytes': len(stderr), 'status': 'PASS'}
        if era == 'auto':
            probes = [event for event in wire if event.get('method') == 'server/discover']
            assert len(probes) == 2 and probes[0]['event'] == 'request' and probes[1]['event'] == 'response'
            assert 'errorCode' in probes[1]
            fallback = next(event for event in wire if event.get('method') == 'initialize' and event['event'] == 'request')
            assert probes[0]['monotonicNs'] < probes[1]['monotonicNs'] < fallback['monotonicNs'] < initialized[0]['monotonicNs']
            row.update(discoveryProbeErrorCode=probes[1]['errorCode'],
                       discoveryProbeElapsedMs=(probes[1]['monotonicNs'] - probes[0]['monotonicNs']) / 1_000_000,
                       errorToFallbackRequestMs=(fallback['monotonicNs'] - probes[1]['monotonicNs']) / 1_000_000)
        else:
            assert not any(event.get('method') == 'server/discover' for event in wire)
        # CHANGE: Persist only allowlisted negotiation fields; no raw CLI logs, schemas, secrets or tool arguments.
        for event in wire:
            event['elapsedFromLaunchMs'] = (event.pop('monotonicNs') - started) / 1_000_000
        (output / f'{era}-negotiation.json').write_text(json.dumps(wire, indent=2) + '\n')
        results.append(row)
    summary = {'inspectorVersion': '2.13.0', 'nodeVersion': 'v22.23.4',
               'binarySHA256': args.expected_binary_sha256, 'results': results,
               'scope': 'Two synthetic tools/list sessions through a transparent test relay; elapsed times include relay overhead, not a performance benchmark.'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
