from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANAGER = ROOT / "installers/macos/mod_manager.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ArtifactTests(unittest.TestCase):
    def test_artifact_checksums(self) -> None:
        expected = {
            ROOT
            / "components/ottoman-naval-parity/WW0_Ottoman_Naval_Parity.pack": "2f18aa43cb51f970838ebd76170a49a28becac558dbb795fd945fa6bb71176b3",
            ROOT
            / "components/middle-eastern-agent-parity/WW0_Middle_Eastern_Agent_Parity.pack": "7115ae6cb60c5102121d81bf57bb53b92852703752a5b76a2a65f66e171d1baf",
            ROOT
            / "components/ww0-agent-cap-startpos/ww0_europe_agent_caps.bsdiff": "1f9bb7cee4708983f282405e5ebff448b5a9f9359be3a2aa587382865f4cd358",
        }
        for artifact, digest in expected.items():
            self.assertEqual(sha256(artifact), digest, artifact)

    def test_source_row_counts(self) -> None:
        sources = {
            ROOT
            / "components/ottoman-naval-parity/source/units_to_exclusive_faction_permissions.tsv": 5,
            ROOT
            / "components/middle-eastern-agent-parity/source/building_effects_junction.tsv": 6,
            ROOT
            / "components/middle-eastern-agent-parity/source/building_factionwide_effects_junctions.tsv": 6,
            ROOT
            / "components/middle-eastern-agent-parity/source/technology_effects_junction.tsv": 2,
        }
        for source, count in sources.items():
            with source.open(newline="") as handle:
                rows = [
                    row
                    for row in csv.reader(handle, delimiter="\t")
                    if any(cell.strip() for cell in row)
                ]
            self.assertEqual(len(rows) - 1, count, source)

    def test_startpos_delta_is_compact_bsdiff(self) -> None:
        patch = ROOT / "components/ww0-agent-cap-startpos/ww0_europe_agent_caps.bsdiff"
        self.assertEqual(patch.read_bytes()[:8], b"BSDIFF40")
        self.assertLess(patch.stat().st_size, 200_000)

    def test_no_upstream_or_personal_binary_dump(self) -> None:
        forbidden = {
            "startpos.esf",
            "Radious_CampaignAI.pack",
            "WW0_battle.pack",
            "WW0_ui.pack",
            "data.pack",
        }
        personal_path = b"/Users/" + b"madan"
        for path in ROOT.rglob("*"):
            if ".git" in path.parts or "__pycache__" in path.parts or not path.is_file():
                continue
            self.assertNotIn(path.name, forbidden, path)
            self.assertNotIn(personal_path, path.read_bytes(), path)


class TransactionTests(unittest.TestCase):
    def run_manager(self, *arguments: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["python3", str(MANAGER), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def test_utf16_merge_and_exact_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            support = root / "support"
            state = root / "state"
            script = support / "AppData/scripts/user.script.txt"
            script.parent.mkdir(parents=True)
            original = (
                'mod "Unrelated.pack";\n'
                'mod "WW0_Ottoman_Naval_Parity.pack";\n'
                'unlock_faction faction_ottomans;\n'
            ).encode("utf-16le")
            script.write_bytes(original)

            common = ("--app", str(root / "app"), "--support", str(support), "--state", str(state))
            self.run_manager(*common, "install", "--components", "unlock", "agents", "naval")

            installed = script.read_bytes()
            self.assertNotEqual(installed, original)
            self.assertGreater(installed.count(b"\x00"), len(installed) // 4)
            text = installed.decode("utf-16le")
            self.assertIn('mod "Unrelated.pack";', text)
            self.assertEqual(text.count('mod "WW0_Ottoman_Naval_Parity.pack";'), 1)
            self.assertEqual(text.count("unlock_faction faction_ottomans;"), 1)
            for marker in ("unlock", "agents", "naval"):
                self.assertEqual(text.count(f"# BEGIN NTW-MACOS-MODS: {marker}"), 1)

            vfs = support / "VFS/Local/Napoleon Total War/data"
            self.assertEqual(
                sha256(vfs / "WW0_Middle_Eastern_Agent_Parity.pack"),
                "7115ae6cb60c5102121d81bf57bb53b92852703752a5b76a2a65f66e171d1baf",
            )
            self.assertEqual(
                sha256(vfs / "WW0_Ottoman_Naval_Parity.pack"),
                "2f18aa43cb51f970838ebd76170a49a28becac558dbb795fd945fa6bb71176b3",
            )

            self.run_manager(*common, "rollback")
            self.assertEqual(script.read_bytes(), original)
            self.assertFalse((vfs / "WW0_Middle_Eastern_Agent_Parity.pack").exists())
            self.assertFalse((vfs / "WW0_Ottoman_Naval_Parity.pack").exists())

    def test_unknown_existing_pack_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            support = root / "support"
            target = support / "VFS/Local/Napoleon Total War/data/WW0_Ottoman_Naval_Parity.pack"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"unknown")
            result = self.run_manager(
                "--app",
                str(root / "app"),
                "--support",
                str(support),
                "--state",
                str(root / "state"),
                "install",
                "--components",
                "naval",
                expect=2,
            )
            self.assertIn("Unknown existing pack", result.stderr)
            self.assertEqual(target.read_bytes(), b"unknown")
            self.assertFalse((root / "state").exists())


if __name__ == "__main__":
    unittest.main()
