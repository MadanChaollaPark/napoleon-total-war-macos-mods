from __future__ import annotations

import csv
from collections import Counter
import hashlib
from pathlib import Path
import runpy
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
            / "components/university-minister-candidates/WW0_University_Minister_Candidates.pack": "e40cecb7deeb07ef4c1b5ce14938bfa20e5cf529dad01ee9dc5eccd56b32ad0c",
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

    def test_university_pack_source_and_semantics(self) -> None:
        component = ROOT / "components/university-minister-candidates"
        builder = component / "source/build_pack.py"
        tracked = component / "WW0_University_Minister_Candidates.pack"
        source = runpy.run_path(str(builder))
        rows = source["make_rows"]()

        factions = source["FACTIONS"]
        triggers = rows["trait_triggers_tables"]
        effects = rows["trigger_effects_tables"]
        self.assertEqual(len(factions), 64)
        self.assertEqual(len(set(factions)), 64)
        self.assertEqual(len(triggers), 192)
        self.assertEqual(len(effects), 192)
        self.assertEqual(len({row[0] for row in triggers}), 192)
        self.assertEqual(len({row[0] for row in effects}), 192)
        self.assertEqual({row[1] for row in triggers}, {"CharacterCreated"})
        self.assertEqual(Counter(row[4] for row in effects), Counter({6: 64, 12: 64, 20: 64}))
        self.assertTrue(all(row[2] == "C_Minister_University_Educated" for row in effects))
        self.assertTrue(all(row[3] == 1 for row in effects))
        self.assertEqual(rows["trait_to_included_agents_tables"], [("C_Minister_University_Educated", "minister")])
        self.assertEqual(
            rows["trait_attribute_effects_tables"],
            [("C_Minister_University_Educated_1", "management", 1)],
        )
        self.assertFalse(rows["character_traits_tables"][0][2])
        conditions = "\n".join(row[2] for row in triggers)
        self.assertNotIn("CharacterCandidateBecomesMinister", conditions)
        self.assertNotIn("Civil Service", conditions)
        for trigger, _event, condition in triggers:
            if trigger.endswith("_T1"):
                self.assertEqual(condition.count(" and not [FactionBuildingExists"), 2)
            elif trigger.endswith("_T2"):
                self.assertEqual(condition.count(" and not [FactionBuildingExists"), 1)
            elif trigger.endswith("_T3"):
                self.assertEqual(condition.count(" and not [FactionBuildingExists"), 0)
            else:
                self.fail(f"Unexpected university trigger key: {trigger}")

        with tempfile.TemporaryDirectory() as temp:
            rebuilt = Path(temp) / tracked.name
            result = subprocess.run(
                ["python3", str(builder), "--output", str(rebuilt)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(rebuilt.read_bytes(), tracked.read_bytes())

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
                'mod "WW0_University_Minister_Candidates.pack";\n'
                'unlock_faction faction_ottomans;\n'
            ).encode("utf-16le")
            script.write_bytes(original)

            common = ("--app", str(root / "app"), "--support", str(support), "--state", str(state))
            self.run_manager(
                *common,
                "install",
                "--components",
                "unlock",
                "agents",
                "university",
                "naval",
            )

            installed = script.read_bytes()
            self.assertNotEqual(installed, original)
            self.assertGreater(installed.count(b"\x00"), len(installed) // 4)
            text = installed.decode("utf-16le")
            self.assertIn('mod "Unrelated.pack";', text)
            self.assertEqual(text.count('mod "WW0_Ottoman_Naval_Parity.pack";'), 1)
            self.assertEqual(text.count('mod "WW0_University_Minister_Candidates.pack";'), 1)
            self.assertEqual(text.count("unlock_faction faction_ottomans;"), 1)
            for marker in ("unlock", "agents", "university", "naval"):
                self.assertEqual(text.count(f"# BEGIN NTW-MACOS-MODS: {marker}"), 1)

            vfs = support / "VFS/Local/Napoleon Total War/data"
            self.assertEqual(
                sha256(vfs / "WW0_Middle_Eastern_Agent_Parity.pack"),
                "7115ae6cb60c5102121d81bf57bb53b92852703752a5b76a2a65f66e171d1baf",
            )
            self.assertEqual(
                sha256(vfs / "WW0_University_Minister_Candidates.pack"),
                "e40cecb7deeb07ef4c1b5ce14938bfa20e5cf529dad01ee9dc5eccd56b32ad0c",
            )
            self.assertEqual(
                sha256(vfs / "WW0_Ottoman_Naval_Parity.pack"),
                "2f18aa43cb51f970838ebd76170a49a28becac558dbb795fd945fa6bb71176b3",
            )

            self.run_manager(*common, "rollback")
            self.assertEqual(script.read_bytes(), original)
            self.assertFalse((vfs / "WW0_Middle_Eastern_Agent_Parity.pack").exists())
            self.assertFalse((vfs / "WW0_University_Minister_Candidates.pack").exists())
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

    def test_unknown_existing_university_pack_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            support = root / "support"
            target = support / "VFS/Local/Napoleon Total War/data/WW0_University_Minister_Candidates.pack"
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
                "university",
                expect=2,
            )
            self.assertIn("Unknown existing pack", result.stderr)
            self.assertEqual(target.read_bytes(), b"unknown")
            self.assertFalse((root / "state").exists())


if __name__ == "__main__":
    unittest.main()
