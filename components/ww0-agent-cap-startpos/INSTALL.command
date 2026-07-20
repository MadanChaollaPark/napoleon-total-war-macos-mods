#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="${NTW_APP_PATH:-/Applications/Napoleon Total War.app}"
STARTPOS="$APP_PATH/Contents/Resources/Data/Data/campaigns/ww0_europe/startpos.esf"
PATCH_FILE="$SCRIPT_DIR/ww0_europe_agent_caps.bsdiff"
STATE_ROOT="${NTW_MOD_STATE_ROOT:-$HOME/Library/Application Support/Napoleon Total War macOS Mods}"
COMPONENT_STATE="$STATE_ROOT/ww0-agent-cap-startpos"

UPSTREAM_HASH="35e29a3a220eb6fede7f15bcd52af0c6338fc902ae247af803bf30ca56402394"
PATCHED_HASH="a52843a83bdbb00710ac74ac3cdf87d76f2209bae81818fdd7016395d80fdf30"
PATCH_HASH="1f9bb7cee4708983f282405e5ebff448b5a9f9359be3a2aa587382865f4cd358"

hash_file() {
  shasum -a 256 "$1" | awk '{print $1}'
}

fail() {
  printf 'INSTALL ABORTED: %s\n' "$1" >&2
  exit 1
}

if pgrep -f '/Applications/Napoleon Total War.app/Contents/MacOS/' >/dev/null 2>&1; then
  fail "Napoleon: Total War is running. Quit it first."
fi

[[ -f "$STARTPOS" ]] || fail "WW0 Europe startpos not found at: $STARTPOS"
[[ -f "$PATCH_FILE" ]] || fail "Patch file is missing."
[[ "$(hash_file "$PATCH_FILE")" == "$PATCH_HASH" ]] || fail "Patch checksum failed."

current_hash="$(hash_file "$STARTPOS")"
if [[ "$current_hash" == "$PATCHED_HASH" ]]; then
  printf 'WW0 agent-cap startpos correction is already installed.\n'
  exit 0
fi
[[ "$current_hash" == "$UPSTREAM_HASH" ]] || fail "Unknown WW0 startpos version; nothing was changed."

timestamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="$COMPONENT_STATE/backups/$timestamp"
mkdir -p "$backup_dir"
cp -p "$STARTPOS" "$backup_dir/startpos.esf"
[[ "$(hash_file "$backup_dir/startpos.esf")" == "$UPSTREAM_HASH" ]] || fail "Backup verification failed."

patched_temp="$backup_dir/startpos.patched.esf"
/usr/bin/bspatch "$STARTPOS" "$patched_temp" "$PATCH_FILE"
[[ "$(hash_file "$patched_temp")" == "$PATCHED_HASH" ]] || fail "Patched output verification failed."

cp -p "$patched_temp" "$STARTPOS"
[[ "$(hash_file "$STARTPOS")" == "$PATCHED_HASH" ]] || fail "Installed file verification failed. Restore from $backup_dir/startpos.esf."
printf '%s\n' "$backup_dir" > "$COMPONENT_STATE/latest-backup.txt"

printf 'Installed successfully. Start a new WW0 campaign for corrected agent caps.\n'
printf 'Backup: %s\n' "$backup_dir/startpos.esf"

