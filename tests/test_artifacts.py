"""Tests of emitted files, condition truth tables and compiled script guards.

Mocked PEX execution tests script branches, not the Skyrim engine's rendering,
native clock or condition-evaluation context. Those need the in-game checklist.
"""
import struct
import sys
import unittest
import hashlib
import json
from pex_host import Host
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


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = ROOT / "package"
        cls.records, cls.groups = read_plugin(cls.package / "KhajiitKeenSenses.esp")
        cls.header = cls.records[0]
        cls.forms = {r["id"] & 0xFFFFFF: r for r in cls.records[1:]}
        cls.pex = read_pex(cls.package / "Scripts" / "LKS_KeenSensesEffect.pex")
        cls.manager_pex = read_pex(cls.package / "Scripts" / "LKS_KeenSensesController.pex")
        cls.effect_bindings = vmad(cls.forms[0x801])["LKS_KeenSensesEffect"]["properties"]
        cls.manager_bindings = vmad(cls.forms[0x804])["LKS_KeenSensesController"]["properties"]

    def host(self):
        return Host(self.pex["objects"][0], self.manager_pex["objects"][0],
                    dict(self.effect_bindings), dict(self.manager_bindings))

    def test_esl_new_records_only_and_master(self):
        self.assertEqual(self.header["type"], "TES4")
        self.assertEqual(self.header["flags"] & (0x200 | 0x80), 0x280)
        self.assertEqual(fields(self.header, "MAST"), [b"Skyrim.esm\0"])
        self.assertEqual(set(self.forms), {0x800, 0x801, 0x802, 0x803, 0x804})
        self.assertEqual(set(self.groups), {("MGEF", 0), ("SPEL", 0), ("QUST", 0)})
        for record in self.records[1:]:
            self.assertEqual(record["id"] >> 24, 1, "Master-record override")
            self.assertEqual(record["version"], 44)
            self.assertEqual(record["flags"], 0)

    def test_header_counts_and_no_existing_actor_record_changes(self):
        version, count, next_id = struct.unpack("<fII", field(self.header, "HEDR"))
        self.assertAlmostEqual(version, 1.7)
        self.assertEqual(count, len(self.records) - 1 + len(self.groups))
        self.assertEqual(next_id, 0x805)
        self.assertEqual(sorted(r["type"] for r in self.records[1:]), ["MGEF", "MGEF", "QUST", "SPEL", "SPEL"])

    def test_lesser_power_and_zero_cost(self):
        spit = struct.unpack("<IIIfIIffI", field(self.forms[0x800], "SPIT"))
        self.assertEqual((spit[0], spit[2], spit[4], spit[5]), (0, 3, 1, 0))
        self.assertEqual(spit[1], 0xB00001)
        self.assertEqual(struct.unpack("<I", field(self.forms[0x800], "ETYP"))[0], 0x25BEE)
        self.assertEqual(field(self.forms[0x800], "EFID"), struct.pack("<I", 0x01000801))
        self.assertEqual(struct.unpack("<fII", field(self.forms[0x800], "EFIT")), (0, 0, 1))

    def test_repeatable_trigger_has_no_native_cooldown_or_self_gate(self):
        data = field(self.forms[0x801], "DATA")
        self.assertEqual(len(data), 152)
        flags = struct.unpack_from("<I", data)[0]
        self.assertFalse(flags & 0x20000, "Do not rely on NoRecast for the shared timer")
        self.assertTrue(flags & 0x8000, "Short trigger should be hidden")
        self.assertFalse(flags & (0x1 | 0x4 | 0x200), "Hostile/detrimental/no-duration flag")
        self.assertEqual(struct.unpack_from("<I", data, 64)[0], 1)
        self.assertEqual(fields(self.forms[0x801], "CTDA"), [], "Circular active-effect gate")
        gate = conditions(self.forms[0x800])
        self.assertEqual([(c["function"], c["p1"], c["value"], c["or"]) for c in gate],
                         [(136, 0x14, 1, False), (69, 0x13745, 1, True),
                          (69, 0x88845, 1, False)])
        # Both SPEL and MGEF conditions may enter active-effect evaluation.
        # Never reject an active timer because that same timer exists.
        for form in (0x800, 0x801):
            self.assertFalse(any(c["function"] == 214 and c["p1"] == 0x01000801
                                 for c in conditions(self.forms[form])),
                             "Self-referential cooldown condition")
        for is_player, race, expected in [
            (True, 0x13745, True), (True, 0x88845, True),
            (False, 0x13745, False), (True, 0x13746, False)]:
            with self.subTest(player=is_player, race=race):
                values = {(136, 0x14): is_player, (69, 0x13745): race == 0x13745,
                          (69, 0x88845): race == 0x88845}
                self.assertEqual(passes(gate, values), expected)

    def test_preserves_user_confirmed_detection_records(self):
        baseline = json.loads((ROOT / "tests/fixtures/v011-detection-signatures.json").read_text())
        for local_id, digest in baseline["record_fields_sha256"].items():
            if local_id == "801":  # This record is now a repeatable trigger.
                continue
            record = self.forms[int(local_id, 16)]
            raw = b"".join(name.encode("ascii") + struct.pack("<H", len(data)) + data
                           for name, data in record["fields"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest,
                             f"Changed already-working v0.1.1 record {local_id}")

    def test_preserves_all_v013_records_and_activation_pex(self):
        baseline = json.loads((ROOT / 'tests/fixtures/v013-record-signatures.json').read_text())
        for local_id, digest in baseline['record_fields_sha256'].items():
            record = self.forms[int(local_id, 16)]
            raw = b''.join(name.encode('ascii') + struct.pack('<H', len(data)) + data
                           for name, data in record['fields'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
        self.assertEqual(hashlib.sha256((self.package / 'Scripts/LKS_KeenSensesEffect.pex')
                                       .read_bytes()).hexdigest(), baseline['activation_pex_sha256'])

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
                                   "KhajiitRace": 0x13745, "KhajiitVampireRace": 0x88845,
                                   "CooldownController": 0x01000804})
        self.assertEqual({p: d["type"].lower() for p, d in obj["properties"].items()},
                         {"DetectionSpell": "spell", "KhajiitRace": "race", "KhajiitVampireRace": "race",
                          "CooldownController": "quest"})
        self.assertEqual(obj["states"][""]["OnEffectStart"]["parameters"],
                         [("akTarget", "actor"), ("akCaster", "actor")])

    def test_controller_is_owned_and_started_on_demand(self):
        quest = self.forms[0x804]
        self.assertEqual(quest["type"], "QUST")
        self.assertEqual(len(field(quest, "DNAM")), 12)
        flags, priority = struct.unpack_from("<HB", field(quest, "DNAM"))
        self.assertEqual((flags, priority), (0, 0))  # no StartGameEnabled / SEQ
        self.assertFalse(fields(quest, "ALST") or fields(quest, "INDX") or fields(quest, "QOBJ"))
        self.assertEqual(fields(quest, "FULL"), [])  # no journal entry/name
        self.assertEqual(self.manager_bindings, {"DetectionSpell": 0x01000803,
                         "KhajiitRace": 0x13745, "KhajiitVampireRace": 0x88845})
        obj = self.manager_pex["objects"][0]
        self.assertEqual(obj["parent"].lower(), "quest")
        self.assertIn("TryActivate", obj["states"][""])
        self.assertIn("OnUpdate", obj["states"][""])
        self.assertNotIn("OnInit", obj["states"][""])  # no load/start lock reset

    def test_compiled_player_and_race_guards(self):
        for race, target, caster, expected in [
            (0x13745, "player", "player", True), (0x88845, "player", "player", True),
            (0x13746, "player", "player", False), (0x13745, "npc", "npc", False),
            (0x13745, "player", "npc", False), (0x13745, "npc", "player", False),
            (0x13745, "player", None, False)]:
            with self.subTest(race=race, target=target, caster=caster):
                host = self.host()
                host.race = race
                host.activate(target, caster)
                self.assertEqual(len(host.casts), int(expected))
                self.assertEqual(host.registrations, [])

    def test_missing_bindings_and_failed_start_do_not_lock_or_cast(self):
        for kind in ("controller", "pulse", "start"):
            with self.subTest(kind=kind):
                host = self.host()
                if kind == "controller":
                    host.effect_bindings["CooldownController"] = None
                elif kind == "pulse":
                    variable = host.manager.obj["properties"]["DetectionSpell"]["variable"].lower()
                    host.manager.fields[variable] = None
                else:
                    host.start_ok = False
                host.activate()
                self.assertEqual(host.casts, [])
                self.assertEqual(host.registrations, [])
                self.assertFalse(host.manager.fields["coolingdown"])

    def test_compiled_cooldown_zero_thirty_sixty_five(self):
        host = self.host()
        host.activate()
        self.assertEqual(host.registrations, [])
        deadline = host.manager.fields['readyathours']
        self.assertEqual(host.casts, [(0.0, 0x01000803, "player", "player")])
        host.advance(30)
        host.activate()
        self.assertEqual(len(host.casts), 1)
        self.assertEqual(host.manager.fields['readyathours'], deadline)
        self.assertEqual(host.registrations, [])
        host.advance(35)
        host.activate()
        self.assertEqual(len(host.casts), 2)
        self.assertAlmostEqual((host.manager.fields['readyathours'] - host.play_hours) * 3600,
                               60.0, delta=0.1)
        self.assertEqual(host.starts, 1)

    def test_rapid_fresh_effect_instances_cannot_extend_or_bypass_lock(self):
        host = self.host()
        host.activate()
        deadline = host.manager.fields['readyathours']
        for _ in range(100):
            host.activate()
        host.advance(59.9)
        for _ in range(100):
            host.activate()
        self.assertEqual(len(host.casts), 1)
        self.assertEqual(host.registrations, [])
        self.assertEqual(host.manager.fields['readyathours'], deadline)
        host.advance(0.2)
        host.activate()
        self.assertEqual(len(host.casts), 2)

    def test_reentry_during_native_calls_cannot_cast_twice(self):
        for phase in ("getrace_hook", "clock_hook", "cast_hook"):
            with self.subTest(phase=phase):
                host = self.host()
                setattr(host, phase, lambda game: game.activate())
                host.activate()
                self.assertEqual(len(host.casts), 1)
                self.assertEqual(host.registrations, [])

    def test_saved_deadline_survives_reload_without_any_update_registration(self):
        host = self.host()
        host.activate()
        host.advance(15)
        snapshot = host.save()
        loaded = self.host()
        loaded.load(snapshot)
        loaded.activate()
        loaded.advance(44)
        loaded.activate()
        self.assertEqual(loaded.casts, [])
        self.assertEqual(loaded.registrations, [])
        self.assertIsNone(loaded.due)
        loaded.advance(1.1)
        loaded.activate()
        self.assertEqual(len(loaded.casts), 1)
        self.assertAlmostEqual(loaded.casts[0][0], 45.1)
        self.assertEqual(loaded.registrations, [])

    def test_saved_ready_state_does_not_replay_or_schedule(self):
        host = self.host()
        host.activate()
        host.advance(60)
        self.assertIsNone(host.due)
        loaded = self.host()
        loaded.load(host.save())
        self.assertEqual(loaded.casts, [])
        self.assertIsNone(loaded.due)
        loaded.activate()
        self.assertEqual(len(loaded.casts), 1)

    def test_pending_legacy_update_cannot_unlock_a_new_deadline(self):
        host = self.host()
        host.activate()
        deadline = host.manager.fields['readyathours']
        host.manager.fields['coolingdown'] = True
        host.manager.invoke('OnUpdate', [], host)
        self.assertEqual(host.manager.fields['readyathours'], deadline)
        host.activate()
        self.assertEqual(len(host.casts), 1)

    def test_old_save_with_stuck_boolean_migrates_without_equipment_changes(self):
        host = self.host()
        host.activate()
        saved = json.loads(host.save())
        del saved['fields']['readyathours']
        saved['fields']['coolingdown'] = True
        saved['remaining_update'] = None
        loaded = self.host()
        loaded.load(json.dumps(saved))
        loaded.activate()
        self.assertEqual(len(loaded.casts), 1)
        self.assertFalse(loaded.manager.fields['coolingdown'])
        loaded.activate()
        self.assertEqual(len(loaded.casts), 1)
        self.assertEqual(loaded.registrations, [])

    def test_backward_native_clock_rebases_once_then_recovers(self):
        host = self.host()
        host.activate()
        host.play_hours = 5.0
        host.activate()
        deadline = host.manager.fields['readyathours']
        self.assertAlmostEqual((deadline - 5.0) * 3600, 60.0, delta=0.1)
        for _ in range(100):
            host.activate()
        self.assertEqual(host.manager.fields['readyathours'], deadline)
        self.assertEqual(len(host.casts), 1)
        host.advance(60.1)
        host.activate()
        self.assertEqual(len(host.casts), 2)

    def test_deadline_precision_at_long_play_times(self):
        for hours in (0.0, 100.0, 1000.0, 10000.0):
            with self.subTest(hours=hours):
                host = self.host()
                host.play_hours = hours
                host.activate()
                host.advance(58)
                host.activate()
                self.assertEqual(len(host.casts), 1)
                host.advance(4)
                host.activate()
                self.assertEqual(len(host.casts), 2)

    def test_controller_has_no_update_registration_or_equipment_apis(self):
        calls = []
        for fn in self.manager_pex['objects'][0]['states'][''].values():
            for inst in fn['code']:
                if inst['op'] in (23, 25):
                    calls.append(inst['args'][0][1].lower() if inst['op'] == 23
                                 else inst['args'][1][1].lower())
        self.assertIn('getrealhourspassed', calls)
        self.assertFalse(set(calls) & {'registerforsingleupdate', 'registerforupdate',
                                     'wait', 'equipspell', 'unequipspell'})

    def test_localized_strings_complete(self):
        for language, name in [("English", "Keen Senses"), ("Japanese", "鋭敏な感覚")]:
            prefix = self.package / "Strings" / f"KhajiitKeenSenses_{language}"
            normal = strings_table(str(prefix) + ".STRINGS")
            descriptions = strings_table(str(prefix) + ".DLSTRINGS")
            self.assertEqual(strings_table(str(prefix) + ".ILSTRINGS"), {})
            key = struct.unpack("<I", field(self.forms[0x800], "FULL"))[0]
            self.assertEqual(normal[key], name)
            for record in self.records[1:]:
                # DNAM is a translated description only for MGEF; for QUST
                # it is the binary quest-data struct, not a strings-table ID.
                names = fields(record, "FULL")
                if record["type"] == "MGEF":
                    names += fields(record, "DNAM")
                for raw in names:
                    key = struct.unpack("<I", raw)[0]
                    self.assertIn(key, normal)
                for raw in fields(record, "DESC") + fields(record, "NNAM"):
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
        for script in ("LKS_KeenSensesEffect", "LKS_KeenSensesController"):
            raw = (self.package / "Scripts" / (script + ".pex")).read_bytes()
            parsed = read_pex(raw)
            obj = parsed["objects"][0]
            position, size = obj["size_offset"], obj["encoded_size"]
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "compiler-output.pex"
                bad = raw[:position] + struct.pack("<I", size - 4) + raw[position + 4:]
                path.write_bytes(bad)
                with self.assertRaises(ValueError):
                    read_pex(path)
                self.assertTrue(repair_caprica_skyrim_size(path))
                self.assertEqual(path.read_bytes(), raw)
                self.assertFalse(repair_caprica_skyrim_size(path))
                old_body_only = raw[:position] + struct.pack(">I", size - 4) + raw[position + 4:]
                path.write_bytes(old_body_only)
                with self.assertRaises(ValueError):
                    read_pex(path)
                wrong = raw[:position] + struct.pack("<I", size - 5) + raw[position + 4:]
                path.write_bytes(wrong)
                with self.assertRaises(ValueError):
                    repair_caprica_skyrim_size(path)
                self.assertEqual(path.read_bytes(), wrong)


if __name__ == "__main__":
    unittest.main()
