#!/bin/sh
set -eu
cidr_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
# CHANGE: The same reviewed selection and lock checks govern bootstrap and later builds.
exec python3 "$cidr_root/Scripts/configure-pilot.py" "$@"
