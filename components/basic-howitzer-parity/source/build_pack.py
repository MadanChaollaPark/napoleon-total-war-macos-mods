#!/usr/bin/env python3
"""Build the WW0 basic Howitzer parity pack deterministically.

The four faction-specific unit rows let Napoleon use an explicit, already
installed national artillery card as the fallback artwork.  No Creative
Assembly UI image is copied into this pack.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path


PACK_NAME = "WW0_Basic_Howitzer_Parity.pack"
TABLE_NAME = "ww0_basic_howitzer_parity"

BUILDINGS = (
    "sCannon3_great_arsenal",
    "sCannon4_ordnance_board",
    "sCannon5_engineer_school",
)

FACTIONS = (
    {
        "faction": "spain",
        "unit": "WW0_Art_Foot_Spain_7_lber_Howitzer",
        "uniform": "WW0_spain_Art_Foot_7_lber_Howitzer",
        "uniform_file": "Spain_Art_Foot_Spanish_9_lber",
        "icon": "spanish_rebels_art_foot_7_lber_howitzer_icon",
        "info": "spanish_rebels_art_foot_7_lber_howitzer_info",
        "colours": (45, 44, 84, 191, 28, 22, 45, 44, 84),
    },
    {
        "faction": "portugal",
        "unit": "WW0_Art_Foot_Portugal_7_lber_Howitzer",
        "uniform": "WW0_portugal_Art_Foot_7_lber_Howitzer",
        "uniform_file": "Portugal_Art_Foot_Portuguese_9_lber",
        "icon": "portugal_art_foot_portuguese_9_lber_icon",
        "info": "portugal_art_foot_portuguese_9_lber_info",
        "colours": (27, 44, 100, 27, 44, 100, 255, 255, 255),
    },
    {
        "faction": "swiss_confederation",
        "unit": "WW0_Art_Foot_Swiss_7_lber_Howitzer",
        "uniform": "WW0_swiss_confederation_Art_Foot_7_lber_Howitzer",
        "uniform_file": "Swiss_Art_Foot_6_lber",
        "icon": "swiss_art_foot_6_lber_icon",
        "info": "swiss_art_foot_6_lber_info",
        "colours": (197, 0, 0, 255, 234, 0, 255, 255, 255),
    },
    {
        "faction": "crimean_khanate",
        "unit": "WW0_Art_Foot_Crimean_7_lber_Howitzer",
        "uniform": "WW0_crimean_khanate_Art_Foot_7_lber_Howitzer",
        "uniform_file": "Crimean_Khanate_Art_Foot_6_lber",
        "icon": "ottomans_art_foot_ottoman_howitzers_icon",
        "info": "ottomans_art_foot_ottoman_howitzers_info",
        "colours": (255, 255, 255, 54, 54, 54, 255, 255, 255),
    },
)

BUILDING_SCHEMA = ("s16", "s16", "i32", "os16")
QUALITY_SCHEMA = ("s16", "s16", "s16", "i32")
COLOUR_SCHEMA = ("s16", "s16") + ("i32",) * 9
UNIFORM_SCHEMA = ("s16", "s16", "s16", "s16")
PERMISSION_SCHEMA = ("s16", "s16", "bool")
UNITS_SCHEMA = (
    "s16", "s16", "s16", "s16", "i32", "i32", "i32", "i32", "i32", "i32",
    "os16", "s16", "s16", "s16", "os16", "i32", "s16", "bool", "bool", "bool",
    "i32", "bool", "i32", "os16", "bool",
)
STATS_SCHEMA = (
    "s16", "i32", "i32", "i32", "s16", "os16", "os16", "s16", "s16", "s16",
    "s16", "i32", "s16", "i32", "os16", "os16", "os16", "s16", "s16", "os16",
    "os16", "os16", "os16", "bool", "os16", "os16", "i32", "i32", "s16", "s16",
    "os16", "i32", "os16", "s16", "i32", "i32", "i32", "i32", "s16", "s16",
    "s16", "s16", "i32", "i32", "f32", "f32", "f32", "f32", "f32", "f32",
    "f32", "i32",
) + ("bool",) * 14 + ("f32",) * 3 + ("bool",) * 16 + ("os16", "os16", "os16", "bool")


def u16(value: str) -> bytes:
    encoded = value.encode("utf-16le")
    return struct.pack("<H", len(encoded) // 2) + encoded


def cell(kind: str, value: object) -> bytes:
    if kind == "s16":
        return u16(str(value))
    if kind == "os16":
        return (b"\x00" if not value else b"\x01" + u16(str(value)))
    if kind == "i32":
        return struct.pack("<i", int(value))
    if kind == "f32":
        return struct.pack("<f", float(value))
    if kind == "bool":
        return struct.pack("<?", bool(value))
    raise ValueError(kind)


def db(schema: tuple[str, ...], rows: list[tuple[object, ...]], version: int | None = None) -> bytes:
    out = bytearray()
    if version is not None:
        out.extend(b"\xfc\xfd\xfe\xff")
        out.extend(struct.pack("<i", version))
    out.extend(struct.pack("<?I", True, len(rows)))
    for row in rows:
        if len(row) != len(schema):
            raise ValueError(f"row has {len(row)} values, schema has {len(schema)}")
        for kind, value in zip(schema, row, strict=True):
            out.extend(cell(kind, value))
    return bytes(out)


def unit_row(entry: dict[str, object]) -> tuple[object, ...]:
    return (
        entry["unit"], "7-lber Howitzer", "artillery", "artillery_foot",
        780, 780, 3, 640, 160, 23, "artillery_medium_howitzer",
        entry["icon"], entry["info"], "Art_Foot_7_lber_Howitzer", "global", 0,
        "mp_artillery", True, True, True, 0, False, 0, "mortars", False,
    )


def stats_row(unit: str) -> tuple[object, ...]:
    return (
        unit, 24, 0, 4, "euro_officer", "", "", "euroline", "infantry_euro_medium",
        "rider_sabre", "generic_gun", 2, "leather", 1, "horse_artillery_mixed_brown",
        "horse_medium", "mount_horse", "0", "0", "gun_train_2_horse",
        "ammo_caisson_small", "limber_model", "Howitzer", True, "howitzer_7_pounder", "",
        35, 20, "0", "matchlock", "", 30, "cannon_crew", "sword", 2, 3, 2, 0,
        "one_handed", "0", "drill_set_artillery", "trained", 3, 1,
        8.0, 12.0, 16.0, 16.0, 1.5, 3.0, 7.0, 0,
        False, False, False, False, False, True, False, True, False, False, False,
        False, False, False, 50.0, 75.0, 100.0,
        False, False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, "", "Ammo_Caisson_destructed",
        "Ammo_Caisson_destruction", False,
    )


def make_files() -> dict[str, bytes]:
    building_rows = [
        (building, entry["unit"], 0, "")
        for entry in FACTIONS
        for building in BUILDINGS
    ]
    quality_rows = [("default", "artillery", entry["unit"], 600) for entry in FACTIONS]
    colour_rows = [
        (entry["uniform"], entry["faction"], *entry["colours"])
        for entry in FACTIONS
    ]
    uniform_rows = [
        (entry["uniform"], entry["faction"], entry["uniform_file"], entry["unit"])
        for entry in FACTIONS
    ]
    stats_rows = [stats_row(str(entry["unit"])) for entry in FACTIONS]
    unit_rows = [unit_row(entry) for entry in FACTIONS]
    permission_rows = [(entry["unit"], entry["faction"], True) for entry in FACTIONS]
    loc_rows = [
        (f"units_on_screen_name_{entry['unit']}", "7-lber Howitzer", False)
        for entry in FACTIONS
    ]
    files = {
        f"db/building_units_allowed_tables/{TABLE_NAME}": db(BUILDING_SCHEMA, building_rows),
        f"db/cdir_unit_qualities_tables/{TABLE_NAME}": db(QUALITY_SCHEMA, quality_rows),
        f"db/uniform_to_faction_colours_tables/{TABLE_NAME}": db(COLOUR_SCHEMA, colour_rows),
        f"db/uniforms_tables/{TABLE_NAME}": db(UNIFORM_SCHEMA, uniform_rows),
        f"db/unit_stats_land_tables/{TABLE_NAME}": db(STATS_SCHEMA, stats_rows, version=5),
        f"db/units_tables/{TABLE_NAME}": db(UNITS_SCHEMA, unit_rows, version=4),
        f"db/units_to_exclusive_faction_permissions_tables/{TABLE_NAME}": db(
            PERMISSION_SCHEMA, permission_rows
        ),
    }
    loc = bytearray(struct.pack("<H", 0xFEFF) + b"LOC\x00" + struct.pack("<iI", 1, len(loc_rows)))
    for key, text, tooltip in loc_rows:
        loc.extend(u16(key))
        loc.extend(u16(text))
        loc.extend(struct.pack("<?", tooltip))
    files[f"text/{TABLE_NAME}.loc"] = bytes(loc)
    return files


def encode_pack(files: dict[str, bytes]) -> bytes:
    index = bytearray()
    data = bytearray()
    for path, payload in sorted(files.items(), key=lambda item: item[0].lower()):
        index.extend(struct.pack("<I", len(payload)))
        index.extend(path.replace("/", "\\").encode("utf-8") + b"\x00")
        data.extend(payload)
    return b"PFH0" + struct.pack("<IIIII", 3, 0, 0, len(files), len(index)) + index + data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).parents[1] / PACK_NAME)
    args = parser.parse_args()
    payload = encode_pack(make_files())
    args.output.write_bytes(payload)
    print(f"built={args.output}")
    print(f"bytes={len(payload)}")
    print(f"sha256={hashlib.sha256(payload).hexdigest()}")


if __name__ == "__main__":
    main()
