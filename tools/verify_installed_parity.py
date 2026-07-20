#!/usr/bin/env python3
"""Verify installed parity packs and their runtime unit-card dependencies."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from ntw_pack import decode_loc, decode_units_v4, read_pack, read_pack_index


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APP = Path("/Applications/Napoleon Total War.app")
DEFAULT_SUPPORT = (
    Path.home()
    / "Library/Containers/com.feralinteractive.napoleontw/Data/Library/Application Support"
    / "Feral Interactive/Napoleon Total War"
)

PACKS = {
    "WW0_Basic_Howitzer_Parity.pack": (
        "96ff592ad64c1831c129eedf57ccd72bcbe5ff15668ff13b56ade97e89341d4d",
        "db/units_tables/ww0_basic_howitzer_parity",
        "7-lber Howitzer",
    ),
    "WW0_Experimental_Howitzer_Parity.pack": (
        "663bd4653ed3cfd9b58b265700fb87fbcbc2b3d0d3480a77674389802cd220dd",
        "db/units_tables/ww0_experimental_howitzer_parity",
        "Experimental Howitzer",
    ),
    "WW0_Rocket_Corps_Parity.pack": (
        "35ba8da230278939df9055a79dbc670655adfd106da10e520500b67bfdc33372",
        "db/units_tables/ww0_rocket_corps_parity",
        "Rocket Troop",
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=Path, default=DEFAULT_APP)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    args = parser.parse_args()

    data_pack = args.app / "Contents/Resources/Data/Data/data.pack"
    if not data_pack.is_file():
        raise SystemExit(f"missing base data pack: {data_pack}")
    base_files = {path.lower() for path in read_pack_index(data_pack)}
    vfs = args.support / "VFS/Local/Napoleon Total War/data"

    verified_units = 0
    for name, (expected_hash, table_path, display_name) in PACKS.items():
        installed = vfs / name
        if not installed.is_file():
            raise SystemExit(f"missing installed pack: {installed}")
        actual_hash = sha256(installed)
        if actual_hash != expected_hash:
            raise SystemExit(f"stale or unknown {name}: {actual_hash}")
        files = read_pack(installed)
        rows = decode_units_v4(files[table_path])
        suffix = table_path.rsplit("/", 1)[1]
        loc_rows = decode_loc(files[f"text/{suffix}.loc"])
        expected_loc = {
            (f"units_on_screen_name_{row['key']}", display_name, False)
            for row in rows
        }
        if set(loc_rows) != expected_loc or len(loc_rows) != len(expected_loc):
            raise SystemExit(f"{name}: missing or duplicate localized unit names")
        for row in rows:
            icon = str(row["icon_name"])
            info = str(row["info_pic"])
            if "placeholder" in icon.lower() or "placeholder" in info.lower():
                raise SystemExit(f"{name}: {row['key']} still uses placeholder artwork")
            icon_path = f"ui/units/icons/{icon}.tga".lower()
            info_path = f"ui/units/info/{info}.tga".lower()
            if icon_path not in base_files:
                raise SystemExit(f"{name}: unresolved icon {icon_path}")
            if info_path not in base_files:
                raise SystemExit(f"{name}: unresolved info card {info_path}")
            verified_units += 1
        print(f"verified {name}: sha256={actual_hash} units={len(rows)}")

    print(f"verified runtime unit-card references: {verified_units}")


if __name__ == "__main__":
    main()
