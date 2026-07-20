from __future__ import annotations

import csv
from collections import Counter
import hashlib
from pathlib import Path
import runpy
import struct
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
import zipfile

from tools.ntw_pack import decode_db, decode_loc, decode_units_v4, encode_pack, read_pack


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
            ROOT / "components/basic-howitzer-parity/WW0_Basic_Howitzer_Parity.pack": "96ff592ad64c1831c129eedf57ccd72bcbe5ff15668ff13b56ade97e89341d4d",
            ROOT / "components/experimental-howitzer-parity/WW0_Experimental_Howitzer_Parity.pack": "663bd4653ed3cfd9b58b265700fb87fbcbc2b3d0d3480a77674389802cd220dd",
            ROOT / "components/rocket-corps-parity/WW0_Rocket_Corps_Parity.pack": "35ba8da230278939df9055a79dbc670655adfd106da10e520500b67bfdc33372",
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

    def test_basic_howitzer_pack_source_and_semantics(self) -> None:
        component = ROOT / "components/basic-howitzer-parity"
        builder = component / "source/build_pack.py"
        tracked = component / "WW0_Basic_Howitzer_Parity.pack"
        source = runpy.run_path(str(builder))

        factions = source["FACTIONS"]
        self.assertEqual(len(factions), 4)
        self.assertEqual(len({entry["faction"] for entry in factions}), 4)
        self.assertEqual(len({entry["unit"] for entry in factions}), 4)
        self.assertEqual(len({entry["icon"] for entry in factions}), 4)
        self.assertTrue(all(str(entry["icon"]).endswith("_icon") for entry in factions))
        self.assertTrue(all(str(entry["info"]).endswith("_info") for entry in factions))

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

        files = read_pack(tracked)
        self.assertFalse(any(path.startswith("ui/") for path in files))
        counts = {
            "db/building_units_allowed_tables/ww0_basic_howitzer_parity": 12,
            "db/cdir_unit_qualities_tables/ww0_basic_howitzer_parity": 4,
            "db/uniform_to_faction_colours_tables/ww0_basic_howitzer_parity": 4,
            "db/uniforms_tables/ww0_basic_howitzer_parity": 4,
            "db/unit_stats_land_tables/ww0_basic_howitzer_parity": 4,
            "db/units_tables/ww0_basic_howitzer_parity": 4,
            "db/units_to_exclusive_faction_permissions_tables/ww0_basic_howitzer_parity": 4,
        }
        for path, expected in counts.items():
            payload = files[path]
            offset = 9 if payload[:4] == b"\xfc\xfd\xfe\xff" else 1
            self.assertEqual(struct.unpack_from("<I", payload, offset)[0], expected, path)

        units = decode_units_v4(files["db/units_tables/ww0_basic_howitzer_parity"])
        self.assertEqual({row["key"] for row in units}, {entry["unit"] for entry in factions})
        self.assertEqual({row["icon_name"] for row in units}, {entry["icon"] for entry in factions})
        self.assertEqual({row["info_pic"] for row in units}, {entry["info"] for entry in factions})
        self.assertNotIn("placeholder_artillery", {row["icon_name"] for row in units})
        self.assertNotIn("placeholder", {row["info_pic"] for row in units})
        self.assertEqual(
            decode_loc(files["text/ww0_basic_howitzer_parity.loc"]),
            [
                (
                    f"units_on_screen_name_{entry['unit']}",
                    "7-lber Howitzer",
                    False,
                )
                for entry in factions
            ],
        )

        stats_schema = tuple(
            ("key" if index == 0 else f"field_{index}", kind)
            for index, kind in enumerate(source["STATS_SCHEMA"])
        )
        stats = decode_db(
            files["db/unit_stats_land_tables/ww0_basic_howitzer_parity"],
            stats_schema,
            version=5,
        )
        self.assertEqual({row["key"] for row in stats}, {entry["unit"] for entry in factions})
        first = {key: value for key, value in stats[0].items() if key != "key"}
        for row in stats[1:]:
            self.assertEqual({key: value for key, value in row.items() if key != "key"}, first)

    def test_new_artillery_unit_cards_are_explicit_and_reproducible(self) -> None:
        targets = {
            ROOT / "components/experimental-howitzer-parity/WW0_Experimental_Howitzer_Parity.pack": (
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
            ROOT / "components/rocket-corps-parity/WW0_Rocket_Corps_Parity.pack": (
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
        }
        for pack, (table_path, expected, loc_path, display_name) in targets.items():
            files = read_pack(pack)
            self.assertFalse(any(path.startswith("ui/") for path in files), pack)
            rows = {row["key"]: row for row in decode_units_v4(files[table_path])}
            self.assertEqual(set(rows), set(expected), pack)
            for unit, (icon, info) in expected.items():
                self.assertEqual(rows[unit]["icon_name"], icon)
                self.assertEqual(rows[unit]["info_pic"], info)
                self.assertNotIn("placeholder", str(rows[unit]["icon_name"]))
                self.assertNotIn("placeholder", str(rows[unit]["info_pic"]))
            self.assertEqual(
                decode_loc(files[loc_path]),
                [
                    (f"units_on_screen_name_{unit}", display_name, False)
                    for unit in sorted(expected)
                ],
            )

        result = subprocess.run(
            ["python3", str(ROOT / "tools/update_icon_references.py")],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_new_artillery_requirements_and_faction_coverage(self) -> None:
        building_schema = (
            ("building", "s16"),
            ("unit", "s16"),
            ("xp", "i32"),
            ("conditions", "os16"),
        )
        quality_schema = (
            ("config", "s16"),
            ("group", "s16"),
            ("unit", "s16"),
            ("quality", "i32"),
        )
        technology_schema = (("unit", "s16"), ("technology", "s16"))
        permission_schema = (("unit", "s16"), ("faction", "s16"), ("allowed", "bool"))
        uniform_schema = (
            ("uniform", "s16"),
            ("faction", "s16"),
            ("filename", "s16"),
            ("unit", "s16"),
        )
        colour_schema = (("uniform", "s16"), ("faction", "s16")) + tuple(
            (f"colour_{index}", "i32") for index in range(9)
        )
        basic_source = runpy.run_path(
            str(ROOT / "components/basic-howitzer-parity/source/build_pack.py")
        )
        stats_schema = tuple(
            ("key" if index == 0 else f"field_{index}", kind)
            for index, kind in enumerate(basic_source["STATS_SCHEMA"])
        )

        basic = read_pack(
            ROOT / "components/basic-howitzer-parity/WW0_Basic_Howitzer_Parity.pack"
        )
        basic_units = {
            row["key"]
            for row in decode_units_v4(basic["db/units_tables/ww0_basic_howitzer_parity"])
        }
        basic_buildings = decode_db(
            basic["db/building_units_allowed_tables/ww0_basic_howitzer_parity"],
            building_schema,
        )
        self.assertEqual(
            {(row["building"], row["unit"]) for row in basic_buildings},
            {
                (building, unit)
                for building in {
                    "sCannon3_great_arsenal",
                    "sCannon4_ordnance_board",
                    "sCannon5_engineer_school",
                }
                for unit in basic_units
            },
        )
        self.assertTrue(all(row["xp"] == 0 and row["conditions"] == "" for row in basic_buildings))
        basic_quality = decode_db(
            basic["db/cdir_unit_qualities_tables/ww0_basic_howitzer_parity"], quality_schema
        )
        self.assertEqual({row["unit"] for row in basic_quality}, basic_units)
        self.assertTrue(all(row["quality"] == 600 for row in basic_quality))
        basic_permissions = decode_db(
            basic[
                "db/units_to_exclusive_faction_permissions_tables/ww0_basic_howitzer_parity"
            ],
            permission_schema,
        )
        self.assertEqual(
            {row["faction"] for row in basic_permissions},
            {"spain", "portugal", "swiss_confederation", "crimean_khanate"},
        )
        self.assertEqual({row["unit"] for row in basic_permissions}, basic_units)
        self.assertTrue(all(row["allowed"] for row in basic_permissions))
        basic_uniforms = decode_db(
            basic["db/uniforms_tables/ww0_basic_howitzer_parity"], uniform_schema
        )
        self.assertEqual(
            {
                (row["faction"], row["unit"], row["uniform"], row["filename"])
                for row in basic_uniforms
            },
            {
                (
                    entry["faction"],
                    entry["unit"],
                    entry["uniform"],
                    entry["uniform_file"],
                )
                for entry in basic_source["FACTIONS"]
            },
        )
        basic_colours = decode_db(
            basic["db/uniform_to_faction_colours_tables/ww0_basic_howitzer_parity"],
            colour_schema,
        )
        self.assertEqual(
            {(row["uniform"], row["faction"]) for row in basic_colours},
            {(row["uniform"], row["faction"]) for row in basic_uniforms},
        )
        self.assertEqual(len(basic_colours), len(basic_uniforms))

        cases = (
            (
                ROOT
                / "components/experimental-howitzer-parity/WW0_Experimental_Howitzer_Parity.pack",
                "ww0_experimental_howitzer_parity",
                {"sCannon4_ordnance_board", "sCannon5_engineer_school"},
                "military3_carcass_shot",
                200,
                ROOT / "components/experimental-howitzer-parity/source/factions.txt",
            ),
            (
                ROOT / "components/rocket-corps-parity/WW0_Rocket_Corps_Parity.pack",
                "ww0_rocket_corps_parity",
                {"sCannon5_engineer_school"},
                "military5_rockets",
                800,
                ROOT / "components/rocket-corps-parity/source/factions.txt",
            ),
        )
        for pack_path, suffix, required_buildings, technology, quality, manifest in cases:
            files = read_pack(pack_path)
            units = {
                row["key"] for row in decode_units_v4(files[f"db/units_tables/{suffix}"])
            }
            building_rows = decode_db(
                files[f"db/building_units_allowed_tables/{suffix}"], building_schema
            )
            self.assertEqual(
                {(row["building"], row["unit"]) for row in building_rows},
                {(building, unit) for building in required_buildings for unit in units},
                pack_path,
            )
            self.assertTrue(
                all(row["xp"] == 0 and row["conditions"] == "" for row in building_rows)
            )
            technology_rows = decode_db(
                files[f"db/unit_required_technology_junctions_tables/{suffix}"],
                technology_schema,
            )
            self.assertEqual({row["unit"] for row in technology_rows}, units)
            self.assertEqual({row["technology"] for row in technology_rows}, {technology})
            quality_rows = decode_db(
                files[f"db/cdir_unit_qualities_tables/{suffix}"], quality_schema
            )
            self.assertEqual({row["unit"] for row in quality_rows}, units)
            self.assertEqual({row["quality"] for row in quality_rows}, {quality})
            permission_rows = decode_db(
                files[f"db/units_to_exclusive_faction_permissions_tables/{suffix}"],
                permission_schema,
            )
            expected_factions = {
                line for line in manifest.read_text().splitlines() if line.strip()
            }
            self.assertEqual({row["faction"] for row in permission_rows}, expected_factions)
            self.assertEqual(len(permission_rows), len(expected_factions))
            self.assertTrue(all(row["allowed"] for row in permission_rows))
            self.assertEqual({row["unit"] for row in permission_rows}, units)
            eastern_factions = {"ottomans", "crimean_khanate"}
            for unit in units:
                actual = {
                    row["faction"] for row in permission_rows if row["unit"] == unit
                }
                expected = (
                    eastern_factions
                    if "Eastern" in str(unit)
                    else expected_factions - eastern_factions
                )
                self.assertEqual(actual, expected, (pack_path, unit))

            uniform_rows = decode_db(
                files[f"db/uniforms_tables/{suffix}"], uniform_schema
            )
            permission_pairs = {
                (row["unit"], row["faction"]) for row in permission_rows
            }
            uniform_pairs = {(row["unit"], row["faction"]) for row in uniform_rows}
            self.assertEqual(uniform_pairs, permission_pairs)
            self.assertEqual(len(uniform_rows), len(permission_pairs))
            self.assertEqual(
                len({(row["uniform"], row["faction"]) for row in uniform_rows}),
                len(uniform_rows),
            )
            self.assertTrue(all(row["filename"] for row in uniform_rows))

            colour_rows = decode_db(
                files[f"db/uniform_to_faction_colours_tables/{suffix}"], colour_schema
            )
            self.assertEqual(
                {(row["uniform"], row["faction"]) for row in colour_rows},
                {(row["uniform"], row["faction"]) for row in uniform_rows},
            )
            self.assertEqual(len(colour_rows), len(uniform_rows))
            self.assertTrue(
                all(
                    0 <= int(row[f"colour_{index}"]) <= 255
                    for row in colour_rows
                    for index in range(9)
                )
            )

            stats_rows = decode_db(
                files[f"db/unit_stats_land_tables/{suffix}"], stats_schema, version=5
            )
            self.assertEqual({row["key"] for row in stats_rows}, units)
            self.assertEqual(len(stats_rows), len(units))

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

    def test_pack_reader_rejects_unsafe_or_malformed_members(self) -> None:
        def raw_pack(entries: list[tuple[str, bytes]]) -> bytes:
            index = bytearray()
            data = bytearray()
            for name, payload in entries:
                index.extend(struct.pack("<I", len(payload)))
                index.extend(name.encode("utf-8") + b"\x00")
                data.extend(payload)
            return (
                b"PFH0"
                + struct.pack("<IIIII", 3, 0, 0, len(entries), len(index))
                + index
                + data
            )

        bad_packs = {
            "duplicate": raw_pack([("db/a", b"1"), ("db/a", b"2")]),
            "case_collision": raw_pack([("db/A", b"1"), ("db/a", b"2")]),
            "parent_path": raw_pack([("../outside", b"1")]),
            "absolute_path": raw_pack([("/outside", b"1")]),
            "truncated": encode_pack({"db/a": b"payload"})[:-1],
        }
        with tempfile.TemporaryDirectory() as temp:
            for name, payload in bad_packs.items():
                with self.subTest(name=name):
                    path = Path(temp) / f"{name}.pack"
                    path.write_bytes(payload)
                    with self.assertRaises(ValueError):
                        read_pack(path)

    def test_release_archives_are_complete_and_clean_installable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "release"
            result = subprocess.run(
                [
                    "python3",
                    str(ROOT / "tools/build_release.py"),
                    "9.9.9",
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            archives = sorted(output.glob("*.zip"))
            release_source = runpy.run_path(str(ROOT / "tools/build_release.py"))
            self.assertEqual(len(archives), len(release_source["ARCHIVES"]))
            sums = {}
            for line in (output / "SHA256SUMS.txt").read_text().splitlines():
                digest, name = line.split("  ", 1)
                sums[name] = digest
            self.assertEqual(set(sums), {archive.name for archive in archives})
            for archive_path in archives:
                self.assertEqual(sha256(archive_path), sums[archive_path.name])
                with zipfile.ZipFile(archive_path) as archive:
                    self.assertIsNone(archive.testzip(), archive_path)
                    self.assertFalse(
                        any(
                            "__pycache__" in name
                            or name.endswith(".pyc")
                            or name.endswith(".DS_Store")
                            for name in archive.namelist()
                        )
                    )

            complete = output / "NTW-macOS-complete-suite-v9.9.9.zip"
            with zipfile.ZipFile(complete) as archive:
                names = set(archive.namelist())
                self.assertIn("tools/ntw_pack.py", names)
                self.assertIn("tools/verify_installed_parity.py", names)
                self.assertIn("installers/macos/INSTALL_ALL.command", names)

            basic = output / "WW0-Basic-Howitzer-Parity-v9.9.9.zip"
            with zipfile.ZipFile(basic) as archive:
                names = set(archive.namelist())
                self.assertNotIn("installers/macos/INSTALL_ALL.command", names)
                self.assertNotIn(
                    "installers/macos/INSTALL_ALL_WITH_RADIOUS.command", names
                )
                self.assertIn("INSTALL_THIS_COMPONENT.command", names)
                launcher = archive.getinfo("INSTALL_THIS_COMPONENT.command")
                self.assertEqual((launcher.external_attr >> 16) & 0o777, 0o755)
                self.assertEqual(
                    [name for name in names if name.endswith(".pack")],
                    [
                        "components/basic-howitzer-parity/"
                        "WW0_Basic_Howitzer_Parity.pack"
                    ],
                )

                extracted = Path(temp) / "extracted"
                archive.extractall(extracted)

            support = Path(temp) / "clean-support"
            state = Path(temp) / "clean-state"
            clean_install = subprocess.run(
                [
                    "python3",
                    str(extracted / "installers/macos/mod_manager.py"),
                    "--app",
                    str(Path(temp) / "clean-app"),
                    "--support",
                    str(support),
                    "--state",
                    str(state),
                    "install",
                    "--components",
                    "basic-howitzers",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(
                clean_install.returncode, 0, clean_install.stdout + clean_install.stderr
            )
            installed = (
                support
                / "VFS/Local/Napoleon Total War/data/WW0_Basic_Howitzer_Parity.pack"
            )
            self.assertEqual(
                sha256(installed),
                "96ff592ad64c1831c129eedf57ccd72bcbe5ff15668ff13b56ade97e89341d4d",
            )


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
                "96ff592ad64c1831c129eedf57ccd72bcbe5ff15668ff13b56ade97e89341d4d",
            )
            self.assertEqual(
                sha256(vfs / "WW0_Experimental_Howitzer_Parity.pack"),
                "663bd4653ed3cfd9b58b265700fb87fbcbc2b3d0d3480a77674389802cd220dd",
            )
            self.assertEqual(
                sha256(vfs / "WW0_Rocket_Corps_Parity.pack"),
                "35ba8da230278939df9055a79dbc670655adfd106da10e520500b67bfdc33372",
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

    def test_known_legacy_pack_upgrade_and_rollback(self) -> None:
        manager = runpy.run_path(str(MANAGER))
        self.assertEqual(
            manager["LEGACY_PACK_HASHES"],
            {
                "basic-howitzers": frozenset(
                    {"268ac5222d1713bf54667d228515e96ced7c42b773d2859909ee19125ce2fb44"}
                ),
                "experimental-howitzers": frozenset(
                    {"3d30b0054c13dd7255b0c7b712991bffc66f0a167eb8ba6e26e9092883708c0d"}
                ),
                "rockets": frozenset(
                    {"2fd7eba010fe7254af0d9c7f1d9f0b3fa068f0a993ca2bfc3243fb4fec9e7b5a"}
                ),
            },
        )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            support = root / "support"
            state = root / "state"
            component = "basic-howitzers"
            old_payload = b"known legacy pack bytes"
            new_payload = b"current repaired pack bytes"
            old_hash = hashlib.sha256(old_payload).hexdigest()
            new_hash = hashlib.sha256(new_payload).hexdigest()
            artifact = (
                repo
                / "components/basic-howitzer-parity/WW0_Basic_Howitzer_Parity.pack"
            )
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(new_payload)
            target = (
                support
                / "VFS/Local/Napoleon Total War/data/WW0_Basic_Howitzer_Parity.pack"
            )
            target.parent.mkdir(parents=True)
            target.write_bytes(old_payload)

            globals_dict = manager["install"].__globals__
            globals_dict["REPO_ROOT"] = repo
            globals_dict["PACK_HASHES"] = {component: new_hash}
            globals_dict["LEGACY_PACK_HASHES"] = {
                component: frozenset({old_hash})
            }
            globals_dict["SCRIPT_COMPONENTS"] = frozenset()
            globals_dict["game_is_running"] = lambda: False
            args = SimpleNamespace(
                components=(component,),
                app=str(root / "app"),
                support=str(support),
                state=str(state),
            )
            manager["install"](args)
            self.assertEqual(target.read_bytes(), new_payload)
            manager["rollback"](
                SimpleNamespace(state=str(state), transaction=None)
            )
            self.assertEqual(target.read_bytes(), old_payload)

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
