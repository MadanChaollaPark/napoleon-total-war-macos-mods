#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
exec /usr/bin/env python3 "$ROOT/installers/macos/mod_manager.py" install --components fair-autoresolve
