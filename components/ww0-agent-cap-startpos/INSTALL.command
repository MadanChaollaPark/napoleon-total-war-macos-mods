#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="${NTW_APP_PATH:-/Applications/Napoleon Total War.app}"
STARTPOS="$APP_PATH/Contents/Resources/Data/Data/campaigns/ww0_europe/startpos.esf"
PATCH_FILE="$SCRIPT_DIR/ww0_europe_agent_caps.bsdiff"
UPGRADE_PATCH_FILE="$SCRIPT_DIR/ww0_italian_agent_caps_upgrade.bsdiff"
STATE_ROOT="${NTW_MOD_STATE_ROOT:-$HOME/Library/Application Support/Napoleon Total War macOS Mods}"
COMPONENT_STATE="$STATE_ROOT/ww0-agent-cap-startpos"

UPSTREAM_HASH="35e29a3a220eb6fede7f15bcd52af0c6338fc902ae247af803bf30ca56402394"
LEGACY_PATCHED_HASH="a52843a83bdbb00710ac74ac3cdf87d76f2209bae81818fdd7016395d80fdf30"
PATCHED_HASH="1a28aeb95cfa4f342eab3b17ddb7818abbb4e059038638b8f4c0d4fc7d58eb0d"
PATCH_HASH="faa5903265d5308b2a212a6073bbec8b9fb76d77b04e938d157d35521a484ede"
UPGRADE_PATCH_HASH="9f7110e56b85cadbf8c794d1a05f3d4d9adb90c44693f104cb14187ae304ab3b"

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
[[ -f "$UPGRADE_PATCH_FILE" ]] || fail "Legacy-upgrade patch file is missing."
[[ "$(hash_file "$PATCH_FILE")" == "$PATCH_HASH" ]] || fail "Patch checksum failed."
[[ "$(hash_file "$UPGRADE_PATCH_FILE")" == "$UPGRADE_PATCH_HASH" ]] || fail "Legacy-upgrade patch checksum failed."

current_hash="$(hash_file "$STARTPOS")"
if [[ "$current_hash" == "$PATCHED_HASH" ]]; then
  printf 'WW0 agent-cap startpos correction is already installed.\n'
  exit 0
fi
if [[ "$current_hash" == "$UPSTREAM_HASH" ]]; then
  selected_patch="$PATCH_FILE"
elif [[ "$current_hash" == "$LEGACY_PATCHED_HASH" ]]; then
  selected_patch="$UPGRADE_PATCH_FILE"
else
  fail "Unknown WW0 startpos version; nothing was changed."
fi

timestamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="$COMPONENT_STATE/backups/$timestamp"
mkdir -p "$backup_dir"
cp -p "$STARTPOS" "$backup_dir/startpos.esf"
[[ "$(hash_file "$backup_dir/startpos.esf")" == "$current_hash" ]] || fail "Backup verification failed."
printf '%s\n' "$current_hash" > "$backup_dir/before.sha256"

patched_temp="$backup_dir/startpos.patched.esf"
/usr/bin/bspatch "$STARTPOS" "$patched_temp" "$selected_patch"
[[ "$(hash_file "$patched_temp")" == "$PATCHED_HASH" ]] || fail "Patched output verification failed."

cp -p "$patched_temp" "$STARTPOS"
[[ "$(hash_file "$STARTPOS")" == "$PATCHED_HASH" ]] || fail "Installed file verification failed. Restore from $backup_dir/startpos.esf."
printf '%s\n' "$backup_dir" > "$COMPONENT_STATE/latest-backup.txt"

printf 'Installed successfully. Start a new WW0 campaign for corrected agent caps.\n'
printf 'Backup: %s\n' "$backup_dir/startpos.esf"
