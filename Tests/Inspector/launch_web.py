#!/usr/bin/env python3
"""Launch the pinned Inspector locally without printing its authentication token."""
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

from qualify_cli import ROOT, environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session-dir', type=Path, default=ROOT / '.verification/inspector-session')
    output = parser.parse_args().session_dir.resolve()
    node = ROOT / '.verification/node-v22.23.4-darwin-arm64/bin/node'
    launcher = ROOT / '.verification/inspector/node_modules/@modelcontextprotocol/inspector/clients/launcher/build/index.js'
    config = output / 'config.json'
    if not config.exists():
        raise SystemExit('Run Tests/Inspector/qualify_cli.py first to create the isolated config.')
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    env = {**environment(output, node), 'HOST': '127.0.0.1', 'CLIENT_PORT': str(port),
           'MCP_SANDBOX_PORT': '0', 'MCP_APP_ORIGIN_PORT': '0'}
    log_path = output / 'web-private.log'
    # CHANGE: Inspector logs an authenticated URL; keep it out of terminal output.
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as log:
        child = subprocess.Popen([str(node), str(launcher), '--web', '--config', str(config)],
                                 env=env, stdout=log, stderr=log, start_new_session=True)
        def stop(_signal, _frame):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, stop)
        try:
            url = f'http://127.0.0.1:{port}/'
            for _ in range(100):
                if child.poll() is not None:
                    raise SystemExit('Inspector exited; inspect the private log locally.')
                try:
                    with urllib.request.urlopen(url, timeout=0.5) as response:
                        if response.status == 200:
                            break
                except (OSError, urllib.error.URLError):
                    time.sleep(0.1)
            else:
                raise SystemExit('Inspector did not become ready within ten seconds.')
            metadata = {'url': url, 'pid': child.pid, 'authentication': 'enabled',
                        'secretStore': 'memory', 'config': str(config)}
            (output / 'web-session.json').write_text(json.dumps(metadata, indent=2) + '\n')
            print(json.dumps(metadata), flush=True)
            child.wait()
        except KeyboardInterrupt:
            pass
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
    return 0


if __name__ == '__main__':
    sys.exit(main())
