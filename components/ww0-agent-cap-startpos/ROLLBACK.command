#!/bin/bash
set -euo pipefail

APP_PATH="${NTW_APP_PATH:-/Applications/Napoleon Total War.app}"
STARTPOS="$APP_PATH/Contents/Resources/Data/Data/campaigns/ww0_europe/startpos.esf"
STATE_ROOT="${NTW_MOD_STATE_ROOT:-$HOME/Library/Application Support/Napoleon Total War macOS Mods}"
COMPONENT_STATE="$STATE_ROOT/ww0-agent-cap-startpos"
LATEST_FILE="$COMPONENT_STATE/latest-backup.txt"

UPSTREAM_HASH="35e29a3a220eb6fede7f15bcd52af0c6338fc902ae247af803bf30ca56402394"
LEGACY_PATCHED_HASH="a52843a83bdbb00710ac74ac3cdf87d76f2209bae81818fdd7016395d80fdf30"
PATCHED_HASH="1a28aeb95cfa4f342eab3b17ddb7818abbb4e059038638b8f4c0d4fc7d58eb0d"

hash_file() {
  shasum -a 256 "$1" | awk '{print $1}'
}

fail() {
  printf 'ROLLBACK ABORTED: %s\n' "$1" >&2
  exit 1
}

if pgrep -f '/Applications/Napoleon Total War.app/Contents/MacOS/' >/dev/null 2>&1; then
  fail "Napoleon: Total War is running. Quit it first."
fi

[[ -f "$STARTPOS" ]] || fail "WW0 Europe startpos not found at: $STARTPOS"
current_hash="$(hash_file "$STARTPOS")"
if [[ "$current_hash" == "$UPSTREAM_HASH" ]]; then
  printf 'Original WW0 startpos is already installed.\n'
  exit 0
fi
[[ "$current_hash" == "$PATCHED_HASH" ]] || fail "Installed startpos has an unknown checksum; refusing to overwrite it."
[[ -f "$LATEST_FILE" ]] || fail "No recorded backup was found."

backup_dir="$(<"$LATEST_FILE")"
backup_file="$backup_dir/startpos.esf"
[[ -f "$backup_file" ]] || fail "Recorded backup is missing: $backup_file"
if [[ -f "$backup_dir/before.sha256" ]]; then
  before_hash="$(<"$backup_dir/before.sha256")"
else
  before_hash="$(hash_file "$backup_file")"
fi
[[ "$before_hash" == "$UPSTREAM_HASH" || "$before_hash" == "$LEGACY_PATCHED_HASH" ]] || fail "Recorded backup has an unsupported checksum."
[[ "$(hash_file "$backup_file")" == "$before_hash" ]] || fail "Recorded backup failed its checksum."

cp -p "$backup_file" "$STARTPOS"
[[ "$(hash_file "$STARTPOS")" == "$before_hash" ]] || fail "Restore verification failed."

printf 'Rollback complete. The exact pre-install WW0 startpos was restored.\n'
