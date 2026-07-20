from __future__ import annotations

import csv
from collections import Counter
import hashlib
from pathlib import Path
import runpy
import struct
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
            ROOT / "components/minor-naval-parity/WW0_Minor_Naval_Parity_Fix.pack": "beae236d8621aab0fdbef95d15ecf05e30235e269a254d52b831c34c62bb67e2",
            ROOT / "components/basic-howitzer-parity/WW0_Basic_Howitzer_Parity.pack": "268ac5222d1713bf54667d228515e96ced7c42b773d2859909ee19125ce2fb44",
            ROOT / "components/experimental-howitzer-parity/WW0_Experimental_Howitzer_Parity.pack": "3d30b0054c13dd7255b0c7b712991bffc66f0a167eb8ba6e26e9092883708c0d",
            ROOT / "components/rocket-corps-parity/WW0_Rocket_Corps_Parity.pack": "2fd7eba010fe7254af0d9c7f1d9f0b3fa068f0a993ca2bfc3243fb4fec9e7b5a",
            ROOT / "components/fair-autoresolve/NTW_Fair_Very_Hard_Autoresolve.pack": "060b90d40dcccbea2922536cf19b5d3eb13759be9ac007997cdad98a71849f85",
            ROOT / "components/ww0-agent-cap-startpos/ww0_europe_agent_caps.bsdiff": "faa5903265d5308b2a212a6073bbec8b9fb76d77b04e938d157d35521a484ede",
            ROOT / "components/ww0-agent-cap-startpos/ww0_italian_agent_caps_upgrade.bsdiff": "9f7110e56b85cadbf8c794d1a05f3d4d9adb90c44693f104cb14187ae304ab3b",
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
        patches = (
            ROOT / "components/ww0-agent-cap-startpos/ww0_europe_agent_caps.bsdiff",
            ROOT / "components/ww0-agent-cap-startpos/ww0_italian_agent_caps_upgrade.bsdiff",
        )
        for patch in patches:
            self.assertEqual(patch.read_bytes()[:8], b"BSDIFF40")
            self.assertLess(patch.stat().st_size, 200_000)

    def test_fair_autoresolve_pack_source_and_semantics(self) -> None:
        component = ROOT / "components/fair-autoresolve"
        builder = component / "source/build_pack.py"
        tracked = component / "NTW_Fair_Very_Hard_Autoresolve.pack"
        source = runpy.run_path(str(builder))

        self.assertEqual(
            source["ROWS"],
            (
                ("autoresolve_very_hard_campaign_AI_percent_increase", 0.0),
                ("autoresolve_very_hard_difficulty_AI_advantage", 0.0),
            ),
        )
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

        payload = tracked.read_bytes()
        self.assertEqual(payload[:4], b"PFH0")
        _flags, _packs, packs_size, file_count, index_size = struct.unpack_from(
            "<IIIII", payload, 4
        )
        self.assertEqual(file_count, 1)
        cursor = 24 + packs_size
        table_size = struct.unpack_from("<I", payload, cursor)[0]
        cursor += 4
        end = payload.index(0, cursor)
        path = payload[cursor:end].decode().replace("\\", "/")
        self.assertEqual(path, source["TABLE_PATH"])
        table = payload[24 + packs_size + index_size :]
        self.assertEqual(len(table), table_size)
        self.assertEqual(table[:5], struct.pack("<?I", True, 2))
        cursor = 5
        rows = []
        for _ in range(2):
            length = struct.unpack_from("<H", table, cursor)[0]
            cursor += 2
            key = table[cursor : cursor + length * 2].decode("utf-16le")
            cursor += length * 2
            value = struct.unpack_from("<f", table, cursor)[0]
            cursor += 4
            rows.append((key, value))
        self.assertEqual(tuple(rows), source["ROWS"])
        self.assertEqual(cursor, len(table))

    def test_new_component_faction_manifests(self) -> None:
        expected = {
            ROOT / "components/basic-howitzer-parity/source/factions.txt": 4,
            ROOT / "components/experimental-howitzer-parity/source/factions.txt": 36,
            ROOT / "components/rocket-corps-parity/source/factions.txt": 36,
        }
        for manifest, count in expected.items():
            factions = [line for line in manifest.read_text().splitlines() if line.strip()]
            self.assertEqual(len(factions), count, manifest)
            self.assertEqual(len(set(factions)), count, manifest)

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
                'mod "NTW_Fair_Very_Hard_Autoresolve.pack";\n'
                'unlock_faction faction_ottomans;\n'
            ).encode("utf-16le")
            script.write_bytes(original)

            common = ("--app", str(root / "app"), "--support", str(support), "--state", str(state))
            selected = (
                "unlock",
                "agents",
                "university",
                "naval",
                "minor-naval",
                "basic-howitzers",
                "experimental-howitzers",
                "rockets",
                "fair-autoresolve",
            )
            self.run_manager(*common, "install", "--components", *selected)

            installed = script.read_bytes()
            self.assertNotEqual(installed, original)
            self.assertGreater(installed.count(b"\x00"), len(installed) // 4)
            text = installed.decode("utf-16le")
            self.assertIn('mod "Unrelated.pack";', text)
            self.assertEqual(text.count('mod "WW0_Ottoman_Naval_Parity.pack";'), 1)
            self.assertEqual(text.count('mod "WW0_University_Minister_Candidates.pack";'), 1)
            self.assertEqual(text.count('mod "NTW_Fair_Very_Hard_Autoresolve.pack";'), 1)
            self.assertEqual(text.count("unlock_faction faction_ottomans;"), 1)
            for marker in selected:
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
            self.assertEqual(
                sha256(vfs / "WW0_Minor_Naval_Parity_Fix.pack"),
                "beae236d8621aab0fdbef95d15ecf05e30235e269a254d52b831c34c62bb67e2",
            )
            self.assertEqual(
                sha256(vfs / "WW0_Basic_Howitzer_Parity.pack"),
                "268ac5222d1713bf54667d228515e96ced7c42b773d2859909ee19125ce2fb44",
            )
            self.assertEqual(
                sha256(vfs / "WW0_Experimental_Howitzer_Parity.pack"),
                "3d30b0054c13dd7255b0c7b712991bffc66f0a167eb8ba6e26e9092883708c0d",
            )
            self.assertEqual(
                sha256(vfs / "WW0_Rocket_Corps_Parity.pack"),
                "2fd7eba010fe7254af0d9c7f1d9f0b3fa068f0a993ca2bfc3243fb4fec9e7b5a",
            )
            self.assertEqual(
                sha256(vfs / "NTW_Fair_Very_Hard_Autoresolve.pack"),
                "060b90d40dcccbea2922536cf19b5d3eb13759be9ac007997cdad98a71849f85",
            )

            self.run_manager(*common, "rollback")
            self.assertEqual(script.read_bytes(), original)
            self.assertFalse((vfs / "WW0_Middle_Eastern_Agent_Parity.pack").exists())
            self.assertFalse((vfs / "WW0_University_Minister_Candidates.pack").exists())
            self.assertFalse((vfs / "WW0_Ottoman_Naval_Parity.pack").exists())
            self.assertFalse((vfs / "WW0_Minor_Naval_Parity_Fix.pack").exists())
            self.assertFalse((vfs / "WW0_Basic_Howitzer_Parity.pack").exists())
            self.assertFalse((vfs / "WW0_Experimental_Howitzer_Parity.pack").exists())
            self.assertFalse((vfs / "WW0_Rocket_Corps_Parity.pack").exists())
            self.assertFalse((vfs / "NTW_Fair_Very_Hard_Autoresolve.pack").exists())

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

    def test_unknown_existing_fair_autoresolve_pack_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            support = root / "support"
            target = (
                support
                / "VFS/Local/Napoleon Total War/data/NTW_Fair_Very_Hard_Autoresolve.pack"
            )
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
                "fair-autoresolve",
                expect=2,
            )
            self.assertIn("Unknown existing pack", result.stderr)
            self.assertEqual(target.read_bytes(), b"unknown")
            self.assertFalse((root / "state").exists())


if __name__ == "__main__":
    unittest.main()
