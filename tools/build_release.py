#!/usr/bin/env python3
"""Build deterministic, component-separated release archives."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import stat
import zipfile


ROOT = Path(__file__).resolve().parents[1]
FIXED_ZIP_TIME = (2026, 7, 20, 0, 0, 0)

SHARED = (
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "docs/COMPATIBILITY.md",
)

ARCHIVES = {
    "NTW-All-Factions": SHARED
    + (
        "components/all-factions-unlocker",
        "installers/macos",
    ),
    "WW0-Ottoman-Naval-Parity": SHARED
    + (
        "components/ottoman-naval-parity",
        "installers/macos",
    ),
    "WW0-Middle-Eastern-Agent-Parity": SHARED
    + (
        "components/middle-eastern-agent-parity",
        "installers/macos",
    ),
    "NTW-University-Minister-Candidates": SHARED
    + (
        "components/university-minister-candidates",
        "installers/macos",
    ),
    "WW0-Agent-Cap-Startpos": SHARED
    + ("components/ww0-agent-cap-startpos",),
    "NTW-macOS-complete-suite": (
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "THIRD_PARTY_NOTICES.md",
        "components",
        "docs",
        "installers",
    ),
}


def files_for(entries: tuple[str, ...]) -> list[Path]:
    files: set[Path] = set()
    for entry in entries:
        path = ROOT / entry
        if path.is_file():
            files.add(path)
        elif path.is_dir():
            files.update(candidate for candidate in path.rglob("*") if candidate.is_file())
        else:
            raise FileNotFoundError(path)
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def add_file(archive: zipfile.ZipFile, path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    info = zipfile.ZipInfo(relative, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    mode = stat.S_IMODE(path.stat().st_mode)
    info.external_attr = (stat.S_IFREG | mode) << 16
    archive.writestr(info, path.read_bytes())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", args.version):
        parser.error("version must look like 1.0.0")

    output = args.output or ROOT / "dist" / f"v{args.version}"
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        parser.error(f"output directory must be empty: {output}")

    built: list[Path] = []
    for name, entries in ARCHIVES.items():
        destination = output / f"{name}-v{args.version}.zip"
        with zipfile.ZipFile(destination, "w") as archive:
            for path in files_for(entries):
                add_file(archive, path)
        built.append(destination)

    sums = output / "SHA256SUMS.txt"
    sums.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in built),
        encoding="utf-8",
    )
    for path in built:
        print(f"{sha256(path)}  {path}")
    print(sums)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
