#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec /usr/bin/env python3 "$SCRIPT_DIR/mod_manager.py" install --components radious unlock agents naval startpos

