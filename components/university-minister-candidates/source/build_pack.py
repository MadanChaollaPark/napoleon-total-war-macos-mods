#!/usr/bin/env python3
"""Build a deterministic PFH0 Napoleon pack for university-educated ministers."""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path


PACK_NAME = "WW0_University_Minister_Candidates.pack"
TABLE_FILE = "ww0_university_minister_candidates"
TRAIT = "C_Minister_University_Educated"
TRAIT_LEVEL = f"{TRAIT}_1"

FACTIONS = (
    "austria",
    "bavaria",
    "belgium",
    "britain",
    "brittany",
    "catalonia",
    "courland",
    "crimean_khanate",
    "denmark",
    "egy_bedouin",
    "egy_britain",
    "egy_french_republic",
    "egy_mamelukes",
    "egy_ottomans",
    "france",
    "greece",
    "hannover",
    "hessen",
    "hungary",
    "ireland",
    "ita_austrian_alliance",
    "ita_french_republic",
    "ita_genoa",
    "ita_lucca",
    "ita_milan",
    "ita_modena",
    "ita_papal_states",
    "ita_parma",
    "ita_piedmont",
    "ita_trent",
    "ita_tuscany",
    "ita_venice",
    "italy",
    "italy_kingdom",
    "mecklenburg",
    "naples",
    "netherlands",
    "norway",
    "oldenburg",
    "ottomans",
    "piedmont_savoy",
    "poland_lithuania",
    "portugal",
    "prussia",
    "romania",
    "russia",
    "sardinia",
    "saxony",
    "scotland",
    "sicily",
    "spa_britain",
    "spa_france",
    "spa_portugal",
    "spa_spain",
    "spain",
    "sweden",
    "swiss_confederation",
    "tut_britain",
    "tut_france",
    "tut_sardinia",
    "tut_swiss_confederation",
    "united_netherlands",
    "westphalia",
    "wurttemberg",
)

TIERS = (
    (1, 6, "tEducation1_college", "tEducationSpain1_college"),
    (2, 12, "tEducation2_university", "tEducationSpain2_university"),
    (3, 20, "tEducation3_enlightened_university", "tEducationSpain3_enlightened_university"),
)

BASE_CANDIDATE_CONDITIONS = (
    'CharacterType("minister") and not IsFactionLeader() and '
    'not IsFactionLeaderFemale() and not CharacterMinisterialPosition("royal_heir") and '
    'not IsTheatreGovernor() and not CampaignName("egy_napoleon") and '
    'not CampaignName("ita_napoleon") and not CharacterMinisterialPosition("accident")'
)

TABLES = {
    "character_traits_tables": ("s16", "i32", "bool", "i32", "s16"),
    "character_trait_levels_tables": ("s16", "i32", "s16", "i32"),
    "trait_info_tables": ("s16", "s16"),
    "trait_to_included_agents_tables": ("s16", "s16"),
    "trait_attribute_effects_tables": ("s16", "s16", "i32"),
    "trait_triggers_tables": ("s16", "s16", "s16"),
    "trigger_effects_tables": ("s16", "s16", "s16", "i32", "i32"),
}


def u16_string(value: str) -> bytes:
    encoded = value.encode("utf-16le")
    units = len(encoded) // 2
    if units > 0xFFFF:
        raise ValueError(f"String is too long for StringU16: {value[:80]!r}")
    return struct.pack("<H", units) + encoded


def encode_cell(kind: str, value: object) -> bytes:
    if kind == "s16":
        return u16_string(str(value))
    if kind == "i32":
        return struct.pack("<i", int(value))
    if kind == "bool":
        return struct.pack("<?", bool(value))
    raise ValueError(f"Unsupported field type: {kind}")


def encode_db(field_types: tuple[str, ...], rows: list[tuple[object, ...]]) -> bytes:
    payload = bytearray(struct.pack("<?I", True, len(rows)))
    for row in rows:
        if len(row) != len(field_types):
            raise ValueError(f"Expected {len(field_types)} fields, got {len(row)}: {row!r}")
        for kind, value in zip(field_types, row, strict=True):
            payload.extend(encode_cell(kind, value))
    return bytes(payload)


def building_group(faction: str, standard: str, peninsular: str) -> str:
    return (
        f'[FactionBuildingExists("{faction}", "{standard}") or '
        f'FactionBuildingExists("{faction}", "{peninsular}")]'
    )


def tier_condition(faction: str, tier: int) -> str:
    groups = {
        number: building_group(faction, standard, peninsular)
        for number, _chance, standard, peninsular in TIERS
    }
    current = groups[tier]
    if tier == 3:
        education = current
    elif tier == 2:
        education = f"{current} and not {groups[3]}"
    else:
        education = f"{current} and not {groups[2]} and not {groups[3]}"
    return (
        f'{BASE_CANDIDATE_CONDITIONS} and CharacterFactionName("{faction}") and {education}'
    )


def make_rows() -> dict[str, list[tuple[object, ...]]]:
    trigger_rows: list[tuple[object, ...]] = []
    effect_rows: list[tuple[object, ...]] = []
    effect_id = -2_100_000_000

    for faction in FACTIONS:
        for tier, chance, _standard, _peninsular in TIERS:
            trigger = f"C_UMQ_{faction}_T{tier}"
            trigger_rows.append((trigger, "CharacterCreated", tier_condition(faction, tier)))
            effect_rows.append((str(effect_id), trigger, TRAIT, 1, chance))
            effect_id -= 1

    return {
        "character_traits_tables": [(TRAIT, 1, False, 1, "Character Quirk")],
        "character_trait_levels_tables": [(TRAIT_LEVEL, 1, TRAIT, 1)],
        "trait_info_tables": [(TRAIT, "agent")],
        "trait_to_included_agents_tables": [(TRAIT, "minister")],
        "trait_attribute_effects_tables": [(TRAIT_LEVEL, "management", 1)],
        "trait_triggers_tables": trigger_rows,
        "trigger_effects_tables": effect_rows,
    }


def encode_loc() -> bytes:
    rows = (
        (
            f"character_trait_levels_onscreen_name_{TRAIT_LEVEL}",
            "University Educated",
            False,
        ),
        (
            f"character_trait_levels_colour_text_{TRAIT_LEVEL}",
            "A rigorous education has prepared this minister for the demands of government.",
            False,
        ),
    )
    payload = bytearray(struct.pack("<H", 0xFEFF))
    payload.extend(b"LOC\x00")
    payload.extend(struct.pack("<iI", 1, len(rows)))
    for key, text, tooltip in rows:
        payload.extend(u16_string(key))
        payload.extend(u16_string(text))
        payload.extend(struct.pack("<?", tooltip))
    return bytes(payload)


def encode_pack(files: dict[str, bytes]) -> bytes:
    ordered = sorted(files.items(), key=lambda item: item[0].lower())
    file_index = bytearray()
    file_data = bytearray()
    for path, data in ordered:
        pack_path = path.replace("/", "\\").encode("utf-8")
        file_index.extend(struct.pack("<I", len(data)))
        file_index.extend(pack_path)
        file_index.append(0)
        file_data.extend(data)

    header = bytearray(b"PFH0")
    header.extend(struct.pack("<IIIII", 3, 0, 0, len(ordered), len(file_index)))
    return bytes(header + file_index + file_data)


def build(output: Path) -> bytes:
    rows = make_rows()
    files = {
        f"db/{table}/{TABLE_FILE}": encode_db(TABLES[table], table_rows)
        for table, table_rows in rows.items()
    }
    files[f"text/{TABLE_FILE}.loc"] = encode_loc()
    pack = encode_pack(files)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(pack)
    return pack


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name(PACK_NAME))
    args = parser.parse_args()
    pack = build(args.output)
    print(f"built={args.output}")
    print(f"bytes={len(pack)}")
    print(f"sha256={hashlib.sha256(pack).hexdigest()}")
    print(f"factions={len(FACTIONS)}")
    print(f"triggers={len(FACTIONS) * len(TIERS)}")


if __name__ == "__main__":
    main()
