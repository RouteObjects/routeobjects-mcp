#!/usr/bin/env python3
"""Launch the pinned Inspector TUI in the caller's real terminal."""
import argparse
import os
from pathlib import Path
from qualify_cli import ROOT, environment

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--session-dir', type=Path, default=ROOT / '.verification/inspector-session')
output = parser.parse_args().session_dir.resolve()
node = ROOT / '.verification/node-v22.23.4-darwin-arm64/bin/node'
launcher = ROOT / '.verification/inspector/node_modules/@modelcontextprotocol/inspector/clients/launcher/build/index.js'
config = output / 'config.json'
if not config.exists():
    raise SystemExit('Run Tests/Inspector/qualify_cli.py first to create the isolated config.')
os.execve(node, [str(node), str(launcher), '--tui', '--config', str(config)], environment(output, node))
