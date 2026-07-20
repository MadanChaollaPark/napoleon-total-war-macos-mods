#!/usr/bin/env python3
"""Transactional installer for the Feral macOS Napoleon mod components."""

from __future__ import annotations

import argparse
import codecs
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_APP = Path("/Applications/Napoleon Total War.app")
DEFAULT_SUPPORT = Path.home() / (
    "Library/Containers/com.feralinteractive.napoleontw/Data/Library/"
    "Application Support/Feral Interactive/Napoleon Total War"
)
DEFAULT_STATE = Path.home() / "Library/Application Support/Napoleon Total War macOS Mods"

STARTPOS_UPSTREAM_HASH = "35e29a3a220eb6fede7f15bcd52af0c6338fc902ae247af803bf30ca56402394"
STARTPOS_PATCHED_HASH = "a52843a83bdbb00710ac74ac3cdf87d76f2209bae81818fdd7016395d80fdf30"
STARTPOS_PATCH_HASH = "1f9bb7cee4708983f282405e5ebff448b5a9f9359be3a2aa587382865f4cd358"
AGENT_PACK_HASH = "7115ae6cb60c5102121d81bf57bb53b92852703752a5b76a2a65f66e171d1baf"
NAVAL_PACK_HASH = "2f18aa43cb51f970838ebd76170a49a28becac558dbb795fd945fa6bb71176b3"
UNIVERSITY_PACK_HASH = "e40cecb7deeb07ef4c1b5ce14938bfa20e5cf529dad01ee9dc5eccd56b32ad0c"
RADIOUS_PACK_HASH = "55a98db54f04d47c05953a335b69706481a31290c171ba4e8de8776743eeded7"

COMPONENT_ORDER = ("radious", "unlock", "agents", "university", "naval", "startpos")
SCRIPT_COMPONENTS = frozenset(("radious", "unlock", "agents", "university", "naval"))


class InstallError(RuntimeError):
    """Raised for a safe, user-facing installer stop."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def game_is_running() -> bool:
    result = subprocess.run(
        ["pgrep", "-f", "/Applications/Napoleon Total War.app/Contents/MacOS/"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def component_artifacts() -> dict[str, Path]:
    return {
        "agents": REPO_ROOT
        / "components/middle-eastern-agent-parity/WW0_Middle_Eastern_Agent_Parity.pack",
        "naval": REPO_ROOT
        / "components/ottoman-naval-parity/WW0_Ottoman_Naval_Parity.pack",
        "university": REPO_ROOT
        / "components/university-minister-candidates/WW0_University_Minister_Candidates.pack",
        "startpos": REPO_ROOT
        / "components/ww0-agent-cap-startpos/ww0_europe_agent_caps.bsdiff",
    }


def target_paths(app: Path, support: Path) -> dict[str, Path]:
    vfs = support / "VFS/Local/Napoleon Total War/data"
    return {
        "script": support / "AppData/scripts/user.script.txt",
        "agents": vfs / "WW0_Middle_Eastern_Agent_Parity.pack",
        "naval": vfs / "WW0_Ottoman_Naval_Parity.pack",
        "university": vfs / "WW0_University_Minister_Candidates.pack",
        "radious": vfs / "Radious_CampaignAI.pack",
        "startpos": app
        / "Contents/Resources/Data/Data/campaigns/ww0_europe/startpos.esf",
    }


def decode_script(path: Path) -> tuple[str, str, bytes]:
    if not path.exists():
        return "", "utf-16le", b""
    data = path.read_bytes()
    if data.startswith(codecs.BOM_UTF16_LE):
        return data[len(codecs.BOM_UTF16_LE) :].decode("utf-16le"), "utf-16le", codecs.BOM_UTF16_LE
    if data.startswith(codecs.BOM_UTF16_BE):
        return data[len(codecs.BOM_UTF16_BE) :].decode("utf-16be"), "utf-16be", codecs.BOM_UTF16_BE
    sample = data[:200]
    if sample and sample.count(0) >= max(1, len(sample) // 4):
        return data.decode("utf-16le"), "utf-16le", b""
    return data.decode("utf-8"), "utf-8", b""


def encode_script(text: str, encoding: str, bom: bytes) -> bytes:
    return bom + text.encode(encoding)


def fragment_body(component: str) -> list[str]:
    if component == "unlock":
        fragment = REPO_ROOT / "components/all-factions-unlocker/user.script.fragment.txt"
    elif component == "agents":
        fragment = REPO_ROOT / "components/middle-eastern-agent-parity/user.script.fragment.txt"
    elif component == "naval":
        fragment = REPO_ROOT / "components/ottoman-naval-parity/user.script.fragment.txt"
    elif component == "university":
        fragment = REPO_ROOT / "components/university-minister-candidates/user.script.fragment.txt"
    elif component == "radious":
        fragment = REPO_ROOT / "components/radious-compatibility/user.script.fragment.txt"
    else:
        raise InstallError(f"No script fragment for component: {component}")
    lines = fragment.read_text(encoding="utf-8").splitlines()
    lines = [line for line in lines if not line.startswith("# BEGIN ") and not line.startswith("# END ")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def merge_component_block(text: str, component: str, install: bool) -> str:
    begin = f"# BEGIN NTW-MACOS-MODS: {component}"
    end = f"# END NTW-MACOS-MODS: {component}"
    pattern = re.compile(
        rf"(?ms)^\s*{re.escape(begin)}\n.*?^\s*{re.escape(end)}\s*\n?"
    )
    merged = pattern.sub("", text)
    body_lines = fragment_body(component)
    if install:
        for line in body_lines:
            merged = re.sub(rf"(?m)^\s*{re.escape(line)}\s*\n?", "", merged)
    merged = merged.rstrip()
    if install:
        body = "\n".join(body_lines)
        block = f"{begin}\n{body}\n{end}"
        merged = f"{merged}\n\n{block}" if merged else block
    return merged + "\n"


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def snapshot(path: Path, name: str, transaction: Path) -> dict[str, object]:
    existed = path.exists()
    entry: dict[str, object] = {"path": str(path), "existed": existed}
    if existed:
        backup = transaction / "before" / name
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        entry["before_sha256"] = sha256(path)
        entry["backup"] = str(backup)
    return entry


def restore_entry(entry: dict[str, object], transaction: Path, *, require_after: bool) -> None:
    target = Path(str(entry["path"]))
    if target.exists() and require_after:
        current = sha256(target)
        allowed = {entry.get("after_sha256"), entry.get("before_sha256")}
        if current not in allowed:
            raise InstallError(f"Refusing to overwrite later change: {target}")
    if bool(entry["existed"]):
        backup = Path(str(entry["backup"]))
        if sha256(backup) != entry["before_sha256"]:
            raise InstallError(f"Backup checksum failed: {backup}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup, target)
    elif target.exists():
        removed = transaction / "removed" / target.name
        removed.parent.mkdir(parents=True, exist_ok=True)
        if removed.exists():
            removed = removed.with_name(f"{removed.name}.{uuid.uuid4().hex[:8]}")
        shutil.move(target, removed)


def write_manifest(path: Path, manifest: dict[str, object]) -> None:
    atomic_write(path, (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())


def validate_artifacts(selected: set[str], paths: dict[str, Path]) -> None:
    artifacts = component_artifacts()
    expectations = {
        "agents": AGENT_PACK_HASH,
        "naval": NAVAL_PACK_HASH,
        "university": UNIVERSITY_PACK_HASH,
        "startpos": STARTPOS_PATCH_HASH,
    }
    for component, expected in expectations.items():
        if component in selected:
            artifact = artifacts[component]
            if not artifact.is_file() or sha256(artifact) != expected:
                raise InstallError(f"Component artifact failed verification: {artifact}")
    if "radious" in selected:
        radious = paths["radious"]
        if not radious.is_file():
            raise InstallError(
                "Radious_CampaignAI.pack is not installed. Download it from the credited ModDB page first."
            )
        if sha256(radious) != RADIOUS_PACK_HASH:
            raise InstallError("Installed Radious pack does not match the verified upstream checksum.")


def install(args: argparse.Namespace) -> None:
    if game_is_running():
        raise InstallError("Napoleon: Total War is running. Quit it first.")
    selected = set(args.components)
    app, support, state = Path(args.app), Path(args.support), Path(args.state)
    paths = target_paths(app, support)
    validate_artifacts(selected, paths)

    for component, expected in (
        ("agents", AGENT_PACK_HASH),
        ("university", UNIVERSITY_PACK_HASH),
        ("naval", NAVAL_PACK_HASH),
    ):
        if component in selected and paths[component].exists() and sha256(paths[component]) != expected:
            raise InstallError(f"Unknown existing pack would be overwritten: {paths[component]}")
    if "startpos" in selected:
        if not paths["startpos"].is_file():
            raise InstallError(f"WW0 Europe startpos not found: {paths['startpos']}")
        current = sha256(paths["startpos"])
        if current not in (STARTPOS_UPSTREAM_HASH, STARTPOS_PATCHED_HASH):
            raise InstallError("Unknown WW0 startpos version; nothing was changed.")

    script_selected = [name for name in COMPONENT_ORDER if name in selected and name in SCRIPT_COMPONENTS]
    script_text = script_encoding = ""
    script_bom = b""
    script_output = b""
    if script_selected:
        script_text, script_encoding, script_bom = decode_script(paths["script"])
        for component in script_selected:
            script_text = merge_component_block(script_text, component, True)
        script_output = encode_script(script_text, script_encoding, script_bom)

    transaction_id = f"{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    transaction = state / "transactions" / transaction_id
    transaction.mkdir(parents=True, exist_ok=False)
    entries: dict[str, dict[str, object]] = {}
    if script_selected:
        entries["script"] = snapshot(paths["script"], "user.script.txt", transaction)
    for component in ("agents", "university", "naval", "startpos"):
        if component in selected:
            entries[component] = snapshot(paths[component], paths[component].name, transaction)

    manifest: dict[str, object] = {
        "version": 1,
        "state": "prepared",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "components": [name for name in COMPONENT_ORDER if name in selected],
        "entries": entries,
    }
    manifest_path = transaction / "manifest.json"
    write_manifest(manifest_path, manifest)

    try:
        artifacts = component_artifacts()
        for component, expected in (
            ("agents", AGENT_PACK_HASH),
            ("university", UNIVERSITY_PACK_HASH),
            ("naval", NAVAL_PACK_HASH),
        ):
            if component in selected:
                atomic_write(paths[component], artifacts[component].read_bytes())
                if sha256(paths[component]) != expected:
                    raise InstallError(f"Installed pack verification failed: {paths[component]}")
                entries[component]["after_sha256"] = expected

        if script_selected:
            atomic_write(paths["script"], script_output)
            entries["script"]["after_sha256"] = sha256(paths["script"])

        if "startpos" in selected:
            before_hash = sha256(paths["startpos"])
            if before_hash == STARTPOS_UPSTREAM_HASH:
                generated = transaction / "generated-startpos.esf"
                subprocess.run(
                    ["/usr/bin/bspatch", str(paths["startpos"]), str(generated), str(artifacts["startpos"])],
                    check=True,
                )
                if sha256(generated) != STARTPOS_PATCHED_HASH:
                    raise InstallError("Generated startpos failed verification.")
                shutil.copy2(generated, paths["startpos"])
            if sha256(paths["startpos"]) != STARTPOS_PATCHED_HASH:
                raise InstallError("Installed startpos failed verification.")
            entries["startpos"]["after_sha256"] = STARTPOS_PATCHED_HASH

        manifest["state"] = "installed"
        manifest["installed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        write_manifest(manifest_path, manifest)
        atomic_write(state / "latest-transaction.txt", f"{transaction_id}\n".encode())
    except Exception:
        for entry in reversed(list(entries.values())):
            restore_entry(entry, transaction, require_after=False)
        manifest["state"] = "install_failed_rolled_back"
        write_manifest(manifest_path, manifest)
        raise

    print("Installed components:", ", ".join(manifest["components"]))
    print("Transaction:", transaction)
    if "startpos" in selected:
        print("Start a new WW0 campaign for the corrected base agent caps.")


def find_transaction(state: Path, requested: str | None) -> Path:
    if requested:
        transaction = state / "transactions" / requested
    else:
        latest = state / "latest-transaction.txt"
        if not latest.is_file():
            raise InstallError("No installation transaction was recorded.")
        transaction = state / "transactions" / latest.read_text().strip()
    if not (transaction / "manifest.json").is_file():
        raise InstallError(f"Transaction manifest is missing: {transaction}")
    return transaction


def rollback(args: argparse.Namespace) -> None:
    if game_is_running():
        raise InstallError("Napoleon: Total War is running. Quit it first.")
    state = Path(args.state)
    transaction = find_transaction(state, args.transaction)
    manifest_path = transaction / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest["state"] == "rolled_back":
        print("Transaction is already rolled back:", transaction.name)
        return
    if manifest["state"] != "installed":
        raise InstallError(f"Transaction is not in an installed state: {manifest['state']}")

    entries = manifest["entries"]
    for name in reversed(list(entries)):
        restore_entry(entries[name], transaction, require_after=True)
    for entry in entries.values():
        target = Path(entry["path"])
        if entry["existed"]:
            if not target.is_file() or sha256(target) != entry["before_sha256"]:
                raise InstallError(f"Rollback verification failed: {target}")
        elif target.exists():
            raise InstallError(f"Rollback left an added file in place: {target}")

    manifest["state"] = "rolled_back"
    manifest["rolled_back_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    write_manifest(manifest_path, manifest)
    print("Rollback complete:", transaction)


def status(args: argparse.Namespace) -> None:
    app, support = Path(args.app), Path(args.support)
    paths = target_paths(app, support)
    expected = {
        "agents": AGENT_PACK_HASH,
        "naval": NAVAL_PACK_HASH,
        "university": UNIVERSITY_PACK_HASH,
        "radious": RADIOUS_PACK_HASH,
    }
    for component, digest in expected.items():
        target = paths[component]
        state = "missing"
        if target.is_file():
            state = "installed" if sha256(target) == digest else "unknown version"
        print(f"{component:10} {state:16} {target}")
    startpos = paths["startpos"]
    startpos_state = "missing"
    if startpos.is_file():
        digest = sha256(startpos)
        startpos_state = {
            STARTPOS_UPSTREAM_HASH: "upstream",
            STARTPOS_PATCHED_HASH: "patched",
        }.get(digest, "unknown version")
    print(f"{'startpos':10} {startpos_state:16} {startpos}")
    script = paths["script"]
    if script.is_file():
        text, encoding, bom = decode_script(script)
        print(f"script     present ({encoding}, BOM={'yes' if bom else 'no'}) {script}")
        for component in sorted(SCRIPT_COMPONENTS):
            marker = f"# BEGIN NTW-MACOS-MODS: {component}"
            print(f"  {component:8} {'managed' if marker in text else 'not managed'}")
    else:
        print(f"script     missing          {script}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--app", default=os.environ.get("NTW_APP_PATH", str(DEFAULT_APP)))
    result.add_argument("--support", default=os.environ.get("NTW_SUPPORT_PATH", str(DEFAULT_SUPPORT)))
    result.add_argument("--state", default=os.environ.get("NTW_MOD_STATE_ROOT", str(DEFAULT_STATE)))
    subparsers = result.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install")
    install_parser.add_argument(
        "--components",
        nargs="+",
        choices=COMPONENT_ORDER,
        default=["unlock", "agents", "naval", "startpos"],
    )
    install_parser.set_defaults(handler=install)

    rollback_parser = subparsers.add_parser("rollback")
    rollback_parser.add_argument("--transaction")
    rollback_parser.set_defaults(handler=rollback)

    status_parser = subparsers.add_parser("status")
    status_parser.set_defaults(handler=status)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        args.handler(args)
    except InstallError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as error:
        print(f"ERROR: external command failed: {error}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
