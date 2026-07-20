#!/usr/bin/env python3
"""Replace placeholder unit cards with references to installed game artwork."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from ntw_pack import decode_units_v4, encode_loc, encode_pack, encode_units_v4, read_pack


ROOT = Path(__file__).resolve().parents[1]

TARGETS = (
    (
        ROOT / "components/experimental-howitzer-parity/WW0_Experimental_Howitzer_Parity.pack",
        "db/units_tables/ww0_experimental_howitzer_parity",
        {
            "WW0_Art_Foot_Minor_Experimental_Howitzer": (
                "prussia_art_foot_prussian_experimental_howitzer_icon",
                "prussia_art_foot_prussian_experimental_howitzer_info",
            ),
            "WW0_Art_Foot_Eastern_Experimental_Howitzer": (
                "russia_art_foot_russian_experimental_howitzer_icon",
                "russia_art_foot_russian_experimental_howitzer_info",
            ),
        },
        "text/ww0_experimental_howitzer_parity.loc",
        "Experimental Howitzer",
    ),
    (
        ROOT / "components/rocket-corps-parity/WW0_Rocket_Corps_Parity.pack",
        "db/units_tables/ww0_rocket_corps_parity",
        {
            "WW0_Art_Fix_Minor_Rocket_Troop": (
                "prussia_art_fix_prussian_rocket_troop_icon",
                "prussia_art_fix_prussian_rocket_troop_info",
            ),
            "WW0_Art_Fix_Eastern_Rocket_Troop": (
                "russia_art_fix_russian_rocket_troop_icon",
                "russia_art_fix_russian_rocket_troop_info",
            ),
        },
        "text/ww0_rocket_corps_parity.loc",
        "Rocket Troop",
    ),
)


def update(
    path: Path,
    table_path: str,
    mappings: dict[str, tuple[str, str]],
    loc_path: str,
    on_screen_name: str,
    write: bool,
) -> bool:
    files = read_pack(path)
    rows = decode_units_v4(files[table_path])
    seen: set[str] = set()
    changed = False
    for row in rows:
        key = str(row["key"])
        if key not in mappings:
            continue
        seen.add(key)
        icon, info = mappings[key]
        if row["icon_name"] != icon or row["info_pic"] != info:
            changed = True
            row["icon_name"] = icon
            row["info_pic"] = info
    missing = set(mappings) - seen
    if missing:
        raise ValueError(f"{path}: missing unit rows: {sorted(missing)}")
    files[table_path] = encode_units_v4(rows)
    loc_rows = [
        (f"units_on_screen_name_{unit}", on_screen_name, False)
        for unit in sorted(mappings)
    ]
    loc_payload = encode_loc(loc_rows)
    if files.get(loc_path) != loc_payload:
        changed = True
        files[loc_path] = loc_payload
    rebuilt = encode_pack(files)
    if write and path.read_bytes() != rebuilt:
        path.write_bytes(rebuilt)
    print(
        f"{path.relative_to(ROOT)} changed={changed} "
        f"sha256={hashlib.sha256(rebuilt).hexdigest()}"
    )
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    any_changed = False
    for target in TARGETS:
        any_changed |= update(*target, write=args.write)
    if not args.write and any_changed:
        raise SystemExit("icon references are stale; rerun with --write")


if __name__ == "__main__":
    main()
