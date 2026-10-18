"""Artifact requirements and rejection tests, not Skyrim engine emulation."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from build_concentration import archive_bytes, build_package, publish_file
from formats import conditions, field, read_plugin
from verify_concentration import verify_package, verify_plugin, verify_zip


def evaluate(items, candidate, caster, *, hour=0, player=None):
    # Exercise stored CTDA grouping, with independent caller-provided contexts.
    # Whether Skyrim supplies these contexts is an explicit runtime open item.
    group = False
    if player is None:
        player = {"ref": 0x14, "interior": False}
    for c in items:
        if c["run_on"] == 0:
            actor = candidate
        elif c["run_on"] == 1:
            actor = caster
        elif c["run_on"] == 2 and c["reference"] == player["ref"]:
            actor = player
        else:
            raise AssertionError("Unexpected condition context")
        if c["function"] == 136:
            actual = int(actor["ref"] == c["p1"])
        elif c["function"] == 69:
            actual = int(actor["race"] == c["p1"])
        elif c["function"] == 46:
            actual = int(actor["dead"])
        elif c["function"] == 560:
            actual = int(c["p1"] in actor["keywords"])
        elif c["function"] == 715:
            actual = int(actor["undead"])
        elif c["function"] == 1:
            actual = actor["distance"]
        elif c["function"] == 18:
            actual = hour
        elif c["function"] == 300:
            actual = int(actor["interior"])
        else:
            raise AssertionError("Unexpected condition function")
        op, value = c["operator"], c["value"]
        ok = {0: actual == value, 1: actual != value, 2: actual > value,
              3: actual >= value, 4: actual < value, 5: actual <= value}[op]
        group |= ok
        if not c["or"]:
            if not group:
                return False
            group = False
    return True


class ConcentrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.package = Path(self.temp.name) / "package"
        build_package(self.package)
        self.plugin = self.package / "KhajiitKeenSensesConcentration.esp"
        records, _ = read_plugin(self.plugin)
        self.spell = next(r for r in records if r["type"] == "SPEL")
        self.effect = next(r for r in records if r["type"] == "MGEF")

    def test_real_output_satisfies_entire_structural_contract(self):
        result = verify_package(self.package)
        self.assertEqual((result["records"], result["overrides"], result["scripts"]), (3, 0, 0))

    def test_published_023_only_approved_balance_condition_and_color_fields_change(self):
        baseline = json.loads((ROOT / "tests/fixtures/v023-concentration.json").read_text())
        old_spell = [(n, bytes.fromhex(d)) for n, d in baseline["records"]["SPEL"]]
        old_effect = [(n, bytes.fromhex(d)) for n, d in baseline["records"]["MGEF"]]
        expected = []
        for name, raw in old_spell:
            if name == "SPIT":
                raw = struct.pack("<I", 50) + raw[4:]
            elif name == "EFIT":
                raw = raw[:4] + struct.pack("<I", 17) + raw[8:]
            expected.append((name, raw))
        self.assertEqual(self.spell["fields"], expected)
        expected = []
        for name, raw in old_effect:
            if name == "CTDA":
                continue  # Conditions are checked independently below/in verifier.
            if name == "DATA":
                data = bytearray(raw)
                struct.pack_into("<f", data, 4, 50)
                struct.pack_into("<I", data, 44, 17)
                raw = bytes(data)
            expected.append((name, raw))
        self.assertEqual([(n, b) for n, b in self.effect["fields"] if n != "CTDA"], expected)
        records, _ = read_plugin(self.plugin)
        shader = next(r for r in records if r["type"] == "EFSH")
        expected_shader = []
        for name, raw in baseline["records"]["EFSH"]:
            raw = bytes.fromhex(raw)
            if name == "DATA":
                data = bytearray(raw)
                for offset in (188, 192, 196):
                    data[offset:offset+4] = bytes((245, 140, 115, 0))
                raw = bytes(data)
            expected_shader.append((name, raw))
        self.assertEqual(shader["fields"], expected_shader)

    def test_private_shader_direct_color_and_native_particle_behavior(self):
        records, _ = read_plugin(self.plugin)
        shader = next(r for r in records if r["type"] == "EFSH")
        data = field(shader, "DATA")
        self.assertEqual([tuple(data[o:o+3]) for o in [188, 192, 196]], [(245, 140, 115)] * 3)
        self.assertEqual(struct.unpack_from("<I", data, 384)[0], 1)
        self.assertEqual(field(shader, "NAM9"), b"\0")
        # Real native behavior requirements independent of the writer:
        # particles must remain visible through walls, with the original count,
        # lifetime, alpha curve and scale curve instead of an unrelated fire FX.
        self.assertEqual(struct.unpack_from("<I", data, 104)[0], 8)
        self.assertEqual(struct.unpack_from("<ff", data, 124), (300, 300))
        self.assertAlmostEqual(struct.unpack_from("<f", data, 132)[0], 0.4)
        self.assertEqual(struct.unpack_from("<ff", data, 172), (10, 36))
        self.assertEqual(struct.unpack_from("<fff", data, 200), (0, 1, 1))

    def test_wrong_shader_color_palette_mode_and_depth_changes_are_rejected(self):
        original = self.plugin.read_bytes()
        marker = b"DATA" + struct.pack("<H", 400)
        self.assertEqual(original.count(marker), 1)
        start = original.index(marker) + 6
        for offset, value in [(188, bytes([0, 0, 255, 0])), (384, struct.pack("<I", 0x10001)),
                              (104, struct.pack("<I", 3)), (132, struct.pack("<f", 99))]:
            with self.subTest(offset=offset):
                changed = bytearray(original)
                changed[start + offset:start + offset + len(value)] = value
                self.plugin.write_bytes(changed)
                with self.assertRaises(ValueError):
                    verify_plugin(self.plugin)

    def test_caster_guards_do_not_filter_the_detected_npc_race(self):
        gates = conditions(self.spell)
        target = {"ref": 0x123456, "race": 0x13746}
        for ref, race, expected in [(0x14, 0x13745, True), (0x14, 0x88845, True),
                (0x14, 0x13746, False), (0x777, 0x13745, False), (0x777, 0x88845, False)]:
            with self.subTest(ref=ref, race=race):
                self.assertEqual(evaluate(gates, target, {"ref":ref,"race":race}), expected)

    def test_candidate_exclusions_and_exact_encoded_range_boundary(self):
        filters = conditions(self.effect)
        alive = {"dead":False,"undead":False,"keywords":set(),"distance":100}
        cases = [({},True), ({"distance":0},True), ({"distance":350},True),
            ({"distance":350.01},False), ({"distance":1000},False), ({"dead":True},False),
            ({"undead":True},False), ({"keywords":{0x13796}},False),
            ({"keywords":{0x1397A}},False), ({"keywords":{0x13797}},False),
            ({"keywords":{0xF82F4}},False)]
        for changes, expected in cases:
            with self.subTest(changes=changes):
                self.assertEqual(evaluate(filters, dict(alive, **changes), {}), expected)

    def test_night_boundaries_and_all_day_player_interior(self):
        filters = conditions(self.effect)
        candidate = {"dead":False, "undead":False, "keywords":set(), "distance":100,
                     "interior":True}
        # Include the last second before 06:00, exact 06:00, exact 19:00,
        # and both sides of midnight. All are GAME hours, not real-world time.
        cases = [(0,True), (5,True), (5 + 59/60 + 59/3600,True), (6,False),
                 (8,False), (12,False), (18 + 59/60 + 59/3600,False),
                 (19,True), (21,True), (23 + 59/60 + 59/3600,True)]
        for hour, expected in cases:
            with self.subTest(hour=hour):
                self.assertEqual(evaluate(filters, candidate, {}, hour=hour), expected)
                self.assertTrue(evaluate(filters, candidate, {}, hour=hour,
                    player={"ref":0x14, "interior":True}))

    def test_indoor_guard_uses_player_not_candidate(self):
        filters = conditions(self.effect)
        alive = {"dead":False, "undead":False, "keywords":set(), "distance":100}
        self.assertFalse(evaluate(filters, dict(alive, interior=True), {}, hour=12,
            player={"ref":0x14, "interior":False}))
        self.assertTrue(evaluate(filters, dict(alive, interior=False), {}, hour=12,
            player={"ref":0x14, "interior":True}))

    def test_indoor_or_night_never_bypasses_exclusions_or_distance(self):
        filters = conditions(self.effect)
        alive = {"dead":False, "undead":False, "keywords":set(), "distance":100}
        for hour, indoor in [(0,False), (12,True), (19,False)]:
            for changes in [{"dead":True}, {"undead":True}, {"keywords":{0x13797}},
                            {"keywords":{0x1397A}}, {"distance":351}]:
                with self.subTest(hour=hour, indoor=indoor, changes=changes):
                    self.assertFalse(evaluate(filters, dict(alive, **changes), {}, hour=hour,
                        player={"ref":0x14, "interior":indoor}))

    def test_wrong_hours_reference_and_or_group_are_rejected(self):
        original = self.plugin.read_bytes()
        ctda = [raw for name, raw in self.effect["fields"] if name == "CTDA"]
        # Condition records are unique; modify serialized fields independently
        # of the writer so wrong boundaries or a lost OR cannot pass packaging.
        mutations = [(7,24,struct.pack("<I",0x15)), (8,0,bytes([0x60])),
                     (8,4,struct.pack("<f",18)), (9,0,bytes([0xA0])),
                     (9,4,struct.pack("<f",6.01))]
        for index, offset, replacement in mutations:
            with self.subTest(condition=index, offset=offset):
                old = ctda[index]
                self.assertEqual(original.count(old), 1)
                modified = old[:offset] + replacement + old[offset+len(replacement):]
                self.plugin.write_bytes(original.replace(old, modified, 1))
                with self.assertRaises(ValueError):
                    verify_plugin(self.plugin)

    def test_repeat_build_produces_identical_package_and_archive(self):
        other = self.package.parent / "second"
        build_package(other)
        def contents(p):
            return {f.relative_to(p).as_posix():f.read_bytes() for f in p.rglob("*") if f.is_file()}
        self.assertEqual(contents(self.package), contents(other))
        self.assertEqual(archive_bytes(contents(self.package)), archive_bytes(contents(other)))

    def test_no_runtime_path_overlap_with_published_legacy_mod(self):
        legacy = ROOT / "dist/KhajiitKeenSenses-0.1.4-MO2.zip"
        if not legacy.exists():
            self.skipTest("Historical archive is not part of the source-only ZIP")
        with zipfile.ZipFile(legacy) as z:
            old = {n.casefold() for n in z.namelist()}
        new = {p.relative_to(self.package).as_posix().casefold() for p in self.package.rglob("*") if p.is_file()}
        self.assertFalse(old & new)

    def test_valid_archive_and_full_checksum_coverage(self):
        files = {p.relative_to(self.package).as_posix():p.read_bytes() for p in self.package.rglob("*") if p.is_file()}
        archive = self.package.parent / "candidate.zip"
        archive.write_bytes(archive_bytes(files))
        self.assertEqual(verify_zip(archive)["files"], 12)

    def test_modified_member_fails_checksum(self):
        readme = self.package / "KhajiitKeenSensesConcentration/README.md"
        readme.write_bytes(readme.read_bytes() + b"\nmodified\n")
        with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
            verify_package(self.package)

    def test_extra_script_or_dll_rejected_even_in_other_directory(self):
        for name in ["Scripts/example.pex", "SKSE/Plugins/example.dll"]:
            with self.subTest(name=name):
                extra = self.package / name
                extra.parent.mkdir(parents=True,exist_ok=True)
                extra.write_bytes(b"unwanted")
                with self.assertRaisesRegex(ValueError, "Unexpected/missing file"):
                    verify_package(self.package)
                extra.unlink()

    def test_wrong_local_link_and_cost_are_rejected(self):
        original = self.plugin.read_bytes()
        for old, new in [(b"EFID\x04\x00" + struct.pack("<I",0x01000801), b"EFID\x04\x00" + struct.pack("<I",0x01000809)),
                (b"SPIT\x24\x00" + struct.pack("<I",50), b"SPIT\x24\x00" + struct.pack("<I",0))]:
            with self.subTest(field=old[:4]):
                self.assertEqual(original.count(old), 1)
                self.plugin.write_bytes(original.replace(old,new,1))
                with self.assertRaises(ValueError):
                    verify_plugin(self.plugin)

    def test_malformed_lengths_fail_bounded_reader(self):
        original = self.plugin.read_bytes()
        for invalid in [original[:-1], original[:30], original + b"GRUP"]:
            with self.subTest(length=len(invalid)):
                self.plugin.write_bytes(invalid)
                with self.assertRaises(ValueError):
                    verify_plugin(self.plugin)

    def test_archive_path_traversal_is_rejected_before_extraction(self):
        archive = self.package.parent / "bad.zip"
        archive.write_bytes(archive_bytes({"../escape.txt": b"bad"}))
        with self.assertRaisesRegex(ValueError, "Unsafe ZIP path"):
            verify_zip(archive)

    def test_published_artifact_cannot_be_silently_replaced(self):
        output = self.package.parent / "published.zip"
        publish_file(output,b"first")
        publish_file(output,b"first")
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
            publish_file(output,b"second")
        self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(),digest)


if __name__ == "__main__":
    unittest.main()
