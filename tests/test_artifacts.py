"""Tests of emitted files, condition truth tables and compiled script guards.

Mocked PEX execution tests script branches, not the Skyrim engine's rendering,
native timer or condition-evaluation context. Those need the in-game checklist.
"""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from formats import conditions, field, fields, read_pex, read_plugin, repair_caprica_skyrim_size, strings_table, vmad


def passes(items, values):
    """Evaluate the Boolean grouping actually encoded in the CTDA chain."""
    group = False
    for item in items:
        actual = values[(item["function"], item["p1"])]
        operators = {0: lambda a, b: a == b, 1: lambda a, b: a != b,
                     2: lambda a, b: a > b, 3: lambda a, b: a >= b,
                     4: lambda a, b: a < b, 5: lambda a, b: a <= b}
        result = operators[item["operator"]](actual, item["value"])
        group = group or result
        if not item["or"]:
            if not group:
                return False
            group = False
    if items and items[-1]["or"]:
        raise ValueError("Unterminated condition OR group")
    return True


def execute_event(obj, bindings, race=0x13745, target="player", caster="player"):
    """Small test VM: execute compiled guard branches with mocked vanilla APIs."""
    event = obj["states"][""]["OnEffectStart"]
    env = {name.lower(): None for name in obj["variables"]}
    for prop, details in obj["properties"].items():
        env[details["variable"].lower()] = bindings.get(prop)
    env.update({"self": "effect", "aktarget": target, "akcaster": caster})
    calls = []

    def get(value):
        kind, raw = value
        return env[raw.lower()] if kind == 1 else raw

    def put(value, data):
        if value[0] != 1:
            raise ValueError("Invalid variable destination")
        env[value[1].lower()] = data

    code, pc, count = event["code"], 0, 0
    while pc < len(code):
        count += 1
        if count > 1000:
            raise ValueError("Unexpected script loop")
        inst = code[pc]
        op, args, extra = inst["op"], inst["args"], inst["variadic"]
        if op == 0:
            pass
        elif op == 10:
            put(args[0], not get(args[1]))
        elif op in (13, 14):
            put(args[0], get(args[1]))
        elif op == 15:
            put(args[0], get(args[1]) == get(args[2]))
        elif op == 20:
            pc += get(args[0])
            continue
        elif op in (21, 22):
            if bool(get(args[0])) == (op == 21):
                pc += get(args[1])
                continue
        elif op == 25:
            if [a[1].lower() for a in args[:2]] != ["game", "getplayer"] or extra:
                raise ValueError("Unexpected global/native dependency")
            put(args[2], "player")
        elif op == 23:
            method, receiver = args[0][1].lower(), get(args[1])
            if method == "getrace" and receiver == "player" and not extra:
                put(args[2], race)
            elif method == "cast" and receiver == bindings["DetectionSpell"]:
                calls.append((receiver, *(get(a) for a in extra)))
                put(args[2], None)
            else:
                raise ValueError("Unexpected method/native dependency")
        elif op == 28:
            prop = args[0][1]
            if get(args[1]) != "effect":
                raise ValueError("Unexpected property target")
            put(args[2], bindings[prop])
        elif op == 26:
            return calls
        else:
            raise ValueError(f"Unsupported guard-test opcode {op}")
        pc += 1
    return calls


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = ROOT / "package"
        cls.records, cls.groups = read_plugin(cls.package / "KhajiitKeenSenses.esp")
        cls.header = cls.records[0]
        cls.forms = {r["id"] & 0xFFFFFF: r for r in cls.records[1:]}
        cls.pex = read_pex(cls.package / "Scripts" / "LKS_KeenSensesEffect.pex")

    def test_esl_new_records_only_and_master(self):
        self.assertEqual(self.header["type"], "TES4")
        self.assertEqual(self.header["flags"] & (0x200 | 0x80), 0x280)
        self.assertEqual(fields(self.header, "MAST"), [b"Skyrim.esm\0"])
        self.assertEqual(set(self.forms), {0x800, 0x801, 0x802, 0x803})
        self.assertEqual(self.groups, [("MGEF", 0), ("SPEL", 0)])
        for record in self.records[1:]:
            self.assertEqual(record["id"] >> 24, 1, "Master-record override")
            self.assertEqual(record["version"], 44)
            self.assertEqual(record["flags"], 0)

    def test_header_counts_and_no_race_perk_quest_changes(self):
        version, count, next_id = struct.unpack("<fII", field(self.header, "HEDR"))
        self.assertAlmostEqual(version, 1.7)
        self.assertEqual(count, len(self.records) - 1 + len(self.groups))
        self.assertEqual(next_id, 0x804)
        self.assertEqual([r["type"] for r in self.records[1:]], ["MGEF", "MGEF", "SPEL", "SPEL"])

    def test_lesser_power_and_zero_cost(self):
        spit = struct.unpack("<IIIfIIffI", field(self.forms[0x800], "SPIT"))
        self.assertEqual((spit[0], spit[2], spit[4], spit[5]), (0, 3, 1, 0))
        self.assertEqual(spit[1], 0xB00001)
        self.assertEqual(struct.unpack("<I", field(self.forms[0x800], "ETYP"))[0], 0x25BEE)
        self.assertEqual(field(self.forms[0x800], "EFID"), struct.pack("<I", 0x01000801))
        self.assertEqual(struct.unpack("<fII", field(self.forms[0x800], "EFIT")), (0, 0, 60))

    def test_native_cooldown_flags_and_entry_gate(self):
        data = field(self.forms[0x801], "DATA")
        self.assertEqual(len(data), 152)
        flags = struct.unpack_from("<I", data)[0]
        self.assertTrue(flags & 0x20000, "NoRecast absent")
        self.assertTrue(flags & 0x10000000, "NoDeathDispel absent")
        self.assertFalse(flags & (0x1 | 0x4 | 0x200), "Hostile/detrimental/no-duration flag")
        self.assertEqual(struct.unpack_from("<I", data, 64)[0], 1)
        self.assertEqual(fields(self.forms[0x801], "CTDA"), [], "Circular active-effect gate")
        gate = conditions(self.forms[0x800])
        self.assertEqual([(c["function"], c["p1"], c["value"], c["or"]) for c in gate],
                         [(136, 0x14, 1, False), (69, 0x13745, 1, True),
                          (69, 0x88845, 1, False), (214, 0x01000801, 0, False)])
        for is_player, race, cooldown, expected in [
            (True, 0x13745, False, True), (True, 0x88845, False, True),
            (False, 0x13745, False, False), (True, 0x13746, False, False),
            (True, 0x13745, True, False), (True, 0x88845, True, False)]:
            with self.subTest(player=is_player, race=race, cooldown=cooldown):
                values = {(136, 0x14): is_player, (69, 0x13745): race == 0x13745,
                          (69, 0x88845): race == 0x88845, (214, 0x01000801): cooldown}
                self.assertEqual(passes(gate, values), expected)

    def test_detection_native_shader_range_and_duration(self):
        data = field(self.forms[0x802], "DATA")
        self.assertEqual(len(data), 152)
        self.assertEqual(struct.unpack_from("<I", data, 32)[0], 0xDC209)
        self.assertEqual(struct.unpack_from("<Ii", data, 64), (19, -1))
        flags = struct.unpack_from("<I", data)[0]
        self.assertFalse(flags & (0x800 | 0x200), "NoArea/NoDuration would disable the intended pulse")
        self.assertTrue(flags & 0x1000, "FXPersist absent")
        self.assertTrue(flags & 0x400, "NoMagnitude absent")
        self.assertEqual(struct.unpack_from("<II", data, 80), (1, 0))
        self.assertEqual(struct.unpack_from("<f", data, 104)[0], 0)
        self.assertEqual(struct.unpack("<fII", field(self.forms[0x803], "EFIT")), (0, 27, 2))
        self.assertGreaterEqual(27 * 64 / 3, 560, "Area sphere must cover the distance filter")
        self.assertTrue(struct.unpack_from("<I", field(self.forms[0x803], "SPIT"), 4)[0] & 0x80000,
                        "AreaEffectIgnoresLOS absent")
        self.assertEqual(field(self.forms[0x803], "EFID"), struct.pack("<I", 0x01000802))
        self.assertEqual(struct.unpack_from("<I", field(self.forms[0x803], "SPIT"), 0)[0], 0)
        self.assertEqual(fields(self.forms[0x802], "VMAD"), [])

    def test_emitted_detection_filter_truth_table(self):
        filters = conditions(self.forms[0x802])
        self.assertEqual([(c["function"], c["p1"]) for c in filters],
                         [(46, 0), (560, 0x13796), (560, 0x1397A),
                          (560, 0xF82F4), (715, 0), (1, 0x14)])
        self.assertEqual(filters[-1]["operator"], 5)
        self.assertEqual(filters[-1]["value"], 560)
        for distance, dead, undead, machine, hidden, is_undead, expected in [
            (0, 0, 0, 0, 0, 0, True), (559.9, 0, 0, 0, 0, 0, True),
            (560, 0, 0, 0, 0, 0, True), (560.1, 0, 0, 0, 0, 0, False),
            (100, 1, 0, 0, 0, 0, False), (100, 0, 1, 0, 0, 0, False),
            (100, 0, 0, 1, 0, 0, False), (100, 0, 0, 0, 1, 0, False),
            (100, 0, 0, 0, 0, 1, False)]:
            with self.subTest(distance=distance, dead=dead, undead=undead, machine=machine,
                              hidden=hidden, is_undead=is_undead):
                values = {(46, 0): dead, (560, 0x13796): undead, (560, 0x1397A): machine,
                          (560, 0xF82F4): hidden, (715, 0): is_undead, (1, 0x14): distance}
                self.assertEqual(passes(filters, values), expected)
        self.assertTrue(all(c["run_on"] == 0 and not c["or"] for c in filters))
        self.assertNotIn(59, [c["function"] for c in filters])  # hostility
        self.assertNotIn(136, [c["function"] for c in filters])  # do not block self delivery

    def test_real_pex_matches_esp_bindings(self):
        self.assertEqual(self.pex["timestamp"], 0)
        self.assertEqual(len(self.pex["objects"]), 1)
        obj = self.pex["objects"][0]
        self.assertEqual(obj["name"], "LKS_KeenSensesEffect")
        self.assertEqual(obj["parent"].lower(), "activemagiceffect")
        bindings = vmad(self.forms[0x801])[obj["name"]]["properties"]
        self.assertEqual(bindings, {"DetectionSpell": 0x01000803,
                                   "KhajiitRace": 0x13745, "KhajiitVampireRace": 0x88845})
        self.assertEqual({p: d["type"].lower() for p, d in obj["properties"].items()},
                         {"DetectionSpell": "spell", "KhajiitRace": "race", "KhajiitVampireRace": "race"})
        self.assertEqual(obj["states"][""]["OnEffectStart"]["parameters"],
                         [("akTarget", "actor"), ("akCaster", "actor")])

    def test_compiled_player_and_race_guards(self):
        obj = self.pex["objects"][0]
        bindings = vmad(self.forms[0x801])[obj["name"]]["properties"]
        for race, target, caster, expected in [
            (0x13745, "player", "player", True), (0x88845, "player", "player", True),
            (0x13746, "player", "player", False), (0x13745, "npc", "npc", False),
            (0x13745, "player", "npc", False), (0x13745, "npc", "player", False),
            (0x13745, "player", None, False)]:
            with self.subTest(race=race, target=target, caster=caster):
                calls = execute_event(obj, bindings, race, target, caster)
                self.assertEqual(calls, [(0x01000803, "player", "player")] if expected else [])
        unbound = dict(bindings, DetectionSpell=None)
        self.assertEqual(execute_event(obj, unbound), [])

    def test_localized_strings_complete(self):
        for language, name in [("English", "Keen Senses"), ("Japanese", "鋭敏な感覚")]:
            prefix = self.package / "Strings" / f"KhajiitKeenSenses_{language}"
            normal = strings_table(str(prefix) + ".STRINGS")
            descriptions = strings_table(str(prefix) + ".DLSTRINGS")
            self.assertEqual(strings_table(str(prefix) + ".ILSTRINGS"), {})
            key = struct.unpack("<I", field(self.forms[0x800], "FULL"))[0]
            self.assertEqual(normal[key], name)
            for record in self.records[1:]:
                for raw in fields(record, "FULL") + fields(record, "DNAM"):
                    key = struct.unpack("<I", raw)[0]
                    self.assertIn(key, normal)
                for raw in fields(record, "DESC"):
                    key = struct.unpack("<I", raw)[0]
                    if key:
                        self.assertIn(key, descriptions)

    def test_readers_reject_truncated_or_wrong_game_files(self):
        import tempfile
        raw = (self.package / "Scripts" / "LKS_KeenSensesEffect.pex").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corrupt.pex"
            for data in (raw[:20], raw[:-1], bytes(8) + raw[8:]):
                path.write_bytes(data)
                with self.subTest(length=len(data)), self.assertRaises((ValueError, IndexError)):
                    read_pex(path)

    def test_size_repair_changes_only_known_marker_and_rejects_other_damage(self):
        import tempfile
        raw = (self.package / "Scripts" / "LKS_KeenSensesEffect.pex").read_bytes()
        # Body is 494 bytes; canonical size includes its own four-byte marker.
        marker = bytes.fromhex("000001f2")
        self.assertEqual(raw.count(marker), 1)
        position = raw.index(marker)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "compiler-output.pex"
            bad = raw[:position] + bytes.fromhex("ee010000") + raw[position + 4:]
            path.write_bytes(bad)
            with self.assertRaises(ValueError):
                read_pex(path)
            self.assertTrue(repair_caprica_skyrim_size(path))
            self.assertEqual(path.read_bytes(), raw)
            self.assertFalse(repair_caprica_skyrim_size(path))
            old_body_only = raw[:position] + bytes.fromhex("000001ee") + raw[position + 4:]
            path.write_bytes(old_body_only)
            with self.assertRaises(ValueError):
                read_pex(path)
            wrong = raw[:position] + bytes.fromhex("ed010000") + raw[position + 4:]
            path.write_bytes(wrong)
            with self.assertRaises(ValueError):
                repair_caprica_skyrim_size(path)
            self.assertEqual(path.read_bytes(), wrong)


if __name__ == "__main__":
    unittest.main()
