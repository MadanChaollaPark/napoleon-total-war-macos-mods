"""Small deterministic helpers for the PFH0 and units-v4 data used here."""

from __future__ import annotations

import struct
from pathlib import Path
from pathlib import PurePosixPath


UNITS_V4_FIELDS = (
    ("key", "s16"),
    ("on_screen_name", "s16"),
    ("category", "s16"),
    ("class", "s16"),
    ("multiplayer_cost", "i32"),
    ("multiplayer_late_cost", "i32"),
    ("create_time", "i32"),
    ("create_cost", "i32"),
    ("upkeep_cost", "i32"),
    ("campaign_action_points", "i32"),
    ("voice", "os16"),
    ("icon_name", "s16"),
    ("info_pic", "s16"),
    ("unit_description_text", "s16"),
    ("region_unit_resource", "os16"),
    ("total_cap", "i32"),
    ("multiplayer_category", "s16"),
    ("mp_available_early", "bool"),
    ("mp_available_middle", "bool"),
    ("mp_available_late", "bool"),
    ("prestige", "i32"),
    ("armed_citizenry", "bool"),
    ("total_cap_mp", "i32"),
    ("unit_type_icon", "os16"),
    ("use_onscreen_name", "bool"),
)


def _validate_member_path(name: str, seen: set[str]) -> str:
    normalized = name.replace("\\", "/")
    parsed = PurePosixPath(normalized)
    if (
        not normalized
        or normalized.startswith("/")
        or parsed.is_absolute()
        or any(part in ("", ".", "..") for part in parsed.parts)
    ):
        raise ValueError(f"unsafe pack member path: {name!r}")
    folded = normalized.casefold()
    if folded in seen:
        raise ValueError(f"duplicate or case-colliding pack member: {normalized}")
    seen.add(folded)
    return normalized


def _parse_pack_index(
    header: bytes, index: bytes, *, total_size: int, source: object
) -> tuple[dict[str, int], int]:
    if len(header) != 24 or header[:4] != b"PFH0":
        raise ValueError(f"{source} is not a complete PFH0 pack")
    _magic, _flags, _packs, packs_size, file_count, index_size = struct.unpack(
        "<4sIIIII", header
    )
    if len(index) != packs_size + index_size:
        raise ValueError(f"{source} has a truncated index")
    cursor = packs_size
    index_end = len(index)
    files: dict[str, int] = {}
    seen: set[str] = set()
    for _ in range(file_count):
        if cursor + 4 > index_end:
            raise ValueError(f"{source} has a malformed file index")
        size = struct.unpack_from("<I", index, cursor)[0]
        cursor += 4
        end = index.find(b"\x00", cursor)
        if end < 0 or end >= index_end:
            raise ValueError(f"{source} has an unterminated member path")
        try:
            raw_name = index[cursor:end].decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"{source} has a non-UTF-8 member path") from error
        name = _validate_member_path(raw_name, seen)
        cursor = end + 1
        files[name] = size
    if cursor != index_end:
        raise ValueError(f"{source} has unused or malformed index bytes")
    data_offset = 24 + len(index)
    if data_offset + sum(files.values()) != total_size:
        raise ValueError(f"{source} has trailing or truncated member data")
    return files, data_offset


def read_pack_index(path: Path) -> dict[str, int]:
    """Return PFH0 member paths and sizes without reading the file payloads."""
    with path.open("rb") as handle:
        header = handle.read(24)
        if len(header) != 24:
            raise ValueError(f"{path} is not a complete PFH0 pack")
        _magic, _flags, _packs, packs_size, _file_count, index_size = struct.unpack(
            "<4sIIIII", header
        )
        index = handle.read(packs_size + index_size)
    files, _data_offset = _parse_pack_index(
        header, index, total_size=path.stat().st_size, source=path
    )
    return files


def read_pack(path: Path) -> dict[str, bytes]:
    payload = path.read_bytes()
    if len(payload) < 24:
        raise ValueError(f"{path} is not a complete PFH0 pack")
    _magic, _flags, _packs, packs_size, _file_count, index_size = struct.unpack_from(
        "<4sIIIII", payload
    )
    index_end = 24 + packs_size + index_size
    sizes, data_cursor = _parse_pack_index(
        payload[:24], payload[24:index_end], total_size=len(payload), source=path
    )
    files: dict[str, bytes] = {}
    for name, size in sizes.items():
        files[name] = payload[data_cursor : data_cursor + size]
        data_cursor += size
    return files


def encode_pack(files: dict[str, bytes]) -> bytes:
    index = bytearray()
    data = bytearray()
    seen: set[str] = set()
    for path, payload in sorted(files.items(), key=lambda item: item[0].lower()):
        path = _validate_member_path(path, seen)
        index.extend(struct.pack("<I", len(payload)))
        index.extend(path.replace("/", "\\").encode("utf-8") + b"\x00")
        data.extend(payload)
    return b"PFH0" + struct.pack("<IIIII", 3, 0, 0, len(files), len(index)) + index + data


def _read_s16(payload: bytes, cursor: int) -> tuple[str, int]:
    count = struct.unpack_from("<H", payload, cursor)[0]
    cursor += 2
    end = cursor + count * 2
    return payload[cursor:end].decode("utf-16le"), end


def _encode_s16(value: str) -> bytes:
    payload = value.encode("utf-16le")
    return struct.pack("<H", len(payload) // 2) + payload


def decode_db(
    payload: bytes, fields: tuple[tuple[str, str], ...], version: int | None = None
) -> list[dict[str, object]]:
    """Decode the simple DB field types used by the parity packs."""
    if version is None:
        cursor = 0
    else:
        if payload[:4] != b"\xfc\xfd\xfe\xff":
            raise ValueError("expected a versioned DB table")
        actual = struct.unpack_from("<i", payload, 4)[0]
        if actual != version:
            raise ValueError(f"expected DB version {version}, found {actual}")
        cursor = 8
    if payload[cursor] != 1:
        raise ValueError("DB table has no row block")
    row_count = struct.unpack_from("<I", payload, cursor + 1)[0]
    cursor += 5
    rows: list[dict[str, object]] = []
    for _ in range(row_count):
        row: dict[str, object] = {}
        for name, kind in fields:
            if kind == "s16":
                value, cursor = _read_s16(payload, cursor)
            elif kind == "os16":
                present = payload[cursor]
                cursor += 1
                if present:
                    value, cursor = _read_s16(payload, cursor)
                else:
                    value = ""
            elif kind == "i32":
                value = struct.unpack_from("<i", payload, cursor)[0]
                cursor += 4
            elif kind == "f32":
                value = struct.unpack_from("<f", payload, cursor)[0]
                cursor += 4
            elif kind == "bool":
                value = bool(payload[cursor])
                cursor += 1
            else:
                raise ValueError(kind)
            row[name] = value
        rows.append(row)
    if cursor != len(payload):
        raise ValueError("DB table has trailing or truncated bytes")
    return rows


def decode_units_v4(payload: bytes) -> list[dict[str, object]]:
    if payload[:4] != b"\xfc\xfd\xfe\xff" or struct.unpack_from("<i", payload, 4)[0] != 4:
        raise ValueError("expected a version-4 units table")
    if payload[8] != 1:
        raise ValueError("units table has no row block")
    row_count = struct.unpack_from("<I", payload, 9)[0]
    cursor = 13
    rows: list[dict[str, object]] = []
    for _ in range(row_count):
        row: dict[str, object] = {}
        for name, kind in UNITS_V4_FIELDS:
            if kind == "s16":
                value, cursor = _read_s16(payload, cursor)
            elif kind == "os16":
                present = payload[cursor]
                cursor += 1
                if present:
                    value, cursor = _read_s16(payload, cursor)
                else:
                    value = ""
            elif kind == "i32":
                value = struct.unpack_from("<i", payload, cursor)[0]
                cursor += 4
            elif kind == "bool":
                value = bool(payload[cursor])
                cursor += 1
            else:
                raise ValueError(kind)
            row[name] = value
        rows.append(row)
    if cursor != len(payload):
        raise ValueError("units table has trailing or truncated bytes")
    return rows


def encode_units_v4(rows: list[dict[str, object]]) -> bytes:
    payload = bytearray(b"\xfc\xfd\xfe\xff" + struct.pack("<i?I", 4, True, len(rows)))
    for row in rows:
        for name, kind in UNITS_V4_FIELDS:
            value = row[name]
            if kind == "s16":
                payload.extend(_encode_s16(str(value)))
            elif kind == "os16":
                payload.extend(b"\x00" if not value else b"\x01" + _encode_s16(str(value)))
            elif kind == "i32":
                payload.extend(struct.pack("<i", int(value)))
            elif kind == "bool":
                payload.extend(struct.pack("<?", bool(value)))
            else:
                raise ValueError(kind)
    return bytes(payload)


def encode_loc(rows: list[tuple[str, str, bool]]) -> bytes:
    payload = bytearray(struct.pack("<H", 0xFEFF) + b"LOC\x00" + struct.pack("<iI", 1, len(rows)))
    for key, text, tooltip in rows:
        payload.extend(_encode_s16(key))
        payload.extend(_encode_s16(text))
        payload.extend(struct.pack("<?", tooltip))
    return bytes(payload)


def decode_loc(payload: bytes) -> list[tuple[str, str, bool]]:
    if payload[:6] != struct.pack("<H", 0xFEFF) + b"LOC\x00":
        raise ValueError("expected a LOC table")
    version, row_count = struct.unpack_from("<iI", payload, 6)
    if version != 1:
        raise ValueError(f"expected LOC version 1, found {version}")
    cursor = 14
    rows: list[tuple[str, str, bool]] = []
    for _ in range(row_count):
        key, cursor = _read_s16(payload, cursor)
        text, cursor = _read_s16(payload, cursor)
        tooltip = bool(payload[cursor])
        cursor += 1
        rows.append((key, text, tooltip))
    if cursor != len(payload):
        raise ValueError("LOC table has trailing or truncated bytes")
    return rows
