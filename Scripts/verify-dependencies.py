#!/usr/bin/env python3
"""Fail closed when the complete lock or reviewed SDK selection drifts."""
import argparse
from pathlib import Path

from pilot_provenance import ProvenanceError
from sdk_selection import load_selection, verify_lock, verify_sdk

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--sdk-path', type=Path)
parser.add_argument('--scratch-path', type=Path, default=root / '.build')
parser.add_argument('--selection-only', action='store_true', help='Validate inputs before resolving or editing dependencies.')
args = parser.parse_args()
try:
    selection = load_selection(root)
    verify_lock(root, selection)
    verify_sdk(root, selection, args.sdk_path, args.scratch_path, selection_only=args.selection_only)
except (ProvenanceError, KeyError, ValueError, OSError) as error:
    parser.error(str(error))
print('Dependency lock and reviewed SDK selection verified.')
