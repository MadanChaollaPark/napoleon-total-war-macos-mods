#!/usr/bin/env python3
"""Build the deterministic Very Hard auto-resolve correction pack."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct


PACK_NAME = "NTW_Fair_Very_Hard_Autoresolve.pack"
TABLE_PATH = "db/campaign_variables_tables/ntw_fair_very_hard_autoresolve"
ROWS = (
    ("autoresolve_very_hard_campaign_AI_percent_increase", 0.0),
    ("autoresolve_very_hard_difficulty_AI_advantage", 0.0),
)


def u16_string(value: str) -> bytes:
    encoded = value.encode("utf-16le")
    return struct.pack("<H", len(encoded) // 2) + encoded


def encode_table() -> bytes:
    payload = bytearray(struct.pack("<?I", True, len(ROWS)))
    for key, value in ROWS:
        payload.extend(u16_string(key))
        payload.extend(struct.pack("<f", value))
    return bytes(payload)


def encode_pack(files: dict[str, bytes]) -> bytes:
    index = bytearray()
    data = bytearray()
    for path, payload in sorted(files.items(), key=lambda item: item[0].lower()):
        index.extend(struct.pack("<I", len(payload)))
        index.extend(path.replace("/", "\\").encode("utf-8") + b"\x00")
        data.extend(payload)
    return b"PFH0" + struct.pack("<IIIII", 3, 0, 0, len(files), len(index)) + index + data


def build(output: Path) -> bytes:
    pack = encode_pack({TABLE_PATH: encode_table()})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(pack)
    return pack


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / PACK_NAME,
    )
    args = parser.parse_args()
    pack = build(args.output)
    print(f"built={args.output}")
    print(f"bytes={len(pack)}")
    print(f"sha256={hashlib.sha256(pack).hexdigest()}")
    print(f"rows={len(ROWS)}")


if __name__ == "__main__":
    main()
