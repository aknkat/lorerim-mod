#!/usr/bin/env python3
"""Build the script-free 0.2.7 spell without touching any historical archive.

Only Python's standard library is needed. This writer follows xEdit's TES5
SPEL/MGEF/EFSH schema. The dedicated shader uses normalized standard settings
from an xEdit export; no shared game record is overridden. Readback uses
the separately maintained formats.py reader and verify_concentration.py.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = "KhajiitKeenSensesConcentration.esp"
VERSION = "0.2.7"
META = "KhajiitKeenSensesConcentration"
SPELL_ID, EFFECT_ID = 0x01000800, 0x01000801
SHADER_ID = 0x01000802
COLOR = bytes((233, 30, 99, 0))  # #E91E63, fourth byte unused, not opacity.
SHADER_BASELINE_SHA256 = "1c199d7ee9487267c1b8261f655878afc0168f760df662625a25cb0d537fce7c"


def sub(tag, data):
    if len(data) > 0xFFFF:
        raise ValueError("Extended subrecords are deliberately unsupported")
    return tag.encode("ascii") + struct.pack("<H", len(data)) + data


def ztext(value):
    return value.encode("utf-8") + b"\0"


def record(tag, form, payload, flags=0):
    return struct.pack("<4sIIIIHH", tag.encode("ascii"), len(payload), flags,
                       form, 0, 44, 0) + payload


def group(tag, data):
    return struct.pack("<4sI4sIHHHH", b"GRUP", len(data) + 24,
                       tag.encode("ascii"), 0, 0, 0, 0, 0) + data


def condition(function, p1=0, *, value=0, operator=0, run_on=0, reference=0, or_next=False):
    return sub("CTDA", struct.pack("<B3xfH2xIIIIi",
        (operator << 5) | int(or_next), value, function, p1, 0, run_on, reference, -1))


def shader_payload():
    baseline = json.loads((ROOT / "tools/data/life_detected_enemy.json").read_text())
    original = bytes.fromhex(baseline["data_hex"])
    if len(original) != 400 or hashlib.sha256(original).hexdigest() != SHADER_BASELINE_SHA256:
        raise ValueError("Unexpected native shader baseline")
    data = bytearray(original)
    for offset in (188, 192, 196):
        data[offset:offset + 4] = COLOR
    # Direct particle RGB, not grayscale-to-palette mapping. Keep the native
    # No Membrane Shader flag and ALL particle timing/alpha/depth settings.
    flags = struct.unpack_from("<I", original, 384)[0]
    struct.pack_into("<I", data, 384, flags & ~(1 << 16))
    result = sub("EDID", ztext("LKSC_DetectionAmberShader"))
    for tag in ("ICON", "ICO2", "NAM7", "NAM8", "NAM9"):
        value = "" if tag == "NAM9" else baseline["textures"][tag]
        result += sub(tag, ztext(value))
    return result + sub("DATA", data)


def make_plugin():
    header = (sub("HEDR", struct.pack("<fII", 1.7, 6, 0x803))
        + sub("CNAM", ztext("aknkat"))
        + sub("SNAM", ztext("Keen Senses Concentration 0.2.7: 5m, base 50/s, indoors or 19:00-06:00 exclusive, no daedra; game validation pending."))
        + sub("MAST", ztext("Skyrim.esm")) + sub("DATA", bytes(8)))

    data = bytearray(152)
    # Native Concentration Detect Life shape. No PowerAffectsMagnitude/Duration,
    # NoArea, hostile, detrimental, script archetype, or runtime VMAD.
    struct.pack_into("<I", data, 0, 0x04021412)
    struct.pack_into("<f", data, 4, 50)
    struct.pack_into("<ii", data, 12, 18, -1)  # Alteration; no resistance AV.
    struct.pack_into("<I", data, 32, SHADER_ID)  # Dedicated private-color EFSH.
    struct.pack_into("<I", data, 44, 17)      # Feet, covering the ~5m cap.
    struct.pack_into("<Ii", data, 64, 19, -1)  # Detect Life, ActorValue None.
    struct.pack_into("<IIi", data, 80, 2, 0, -1)  # Concentration, Self, AV None.
    # Casting Art stays NULL: remove the hand glow, not casting animations.
    struct.pack_into("<f", data, 104, 0)      # No skill XP from this spell.
    struct.pack_into("<f", data, 112, 1)
    struct.pack_into("<I", data, 140, 2)      # Silent to AI, native Detect Life.
    effect = (sub("EDID", ztext("LKSC_DetectLivingEffect"))
        + sub("FULL", struct.pack("<I", 1))
        + sub("MDOB", struct.pack("<I", 0x104F70))
        + sub("DATA", data))
    for kind, sound in [(0, 0x3F37A), (1, 0x7C71F), (2, 0x81189)]:
        effect += sub("SNDD", struct.pack("<II", kind, sound))
    effect += sub("DNAM", struct.pack("<I", 2))
    # These run on each candidate being detected, not on its race/faction.
    effect += condition(46)  # GetDead == 0.
    for keyword in (0x13796, 0x1397A, 0x13797, 0xF82F4):
        effect += condition(560, keyword)  # Undead, Dwarven, Daedra, NoDetectLife.
    effect += condition(715)  # IsUndead == 0.
    effect += condition(1, 0x14, value=350, operator=5)  # <= ~5m from PlayerRef.
    # A single OR group, ANDed with ALL candidate filters above:
    # PlayerRef indoors OR game hour >= 19 OR game hour < 6.
    # Use an explicit PlayerRef for the indoor check, never the detected NPC.
    # Put availability on MGEF for native condition evaluation, not a script,
    # quest timer, or forced caster interruption. Boundary runtime is untested.
    effect += condition(300, value=1, run_on=2, reference=0x14, or_next=True)
    effect += condition(18, value=19, operator=3, run_on=2, reference=0x14, or_next=True)
    effect += condition(18, value=6, operator=4, run_on=2, reference=0x14)

    # Keep native concentration spell handling and hand casting, not Voice.
    # ManualCostCalc overrides auto-calculation, NOT the engine's actor/perk
    # cost adjustments. No castingPerk reference and no free-cost flags.
    spit = struct.pack("<IIIfIIffI", 50, 0x00B80001, 0, 0, 2, 0, 0, 0, 0)
    spell = (sub("EDID", ztext("LKSC_KeenSenses")) + sub("OBND", bytes(12))
        + sub("FULL", struct.pack("<I", 3))
        + sub("MDOB", struct.pack("<I", 0x104F70))
        + sub("ETYP", struct.pack("<I", 0x13F44))
        + sub("DESC", struct.pack("<I", 4)) + sub("SPIT", spit)
        + sub("EFID", struct.pack("<I", EFFECT_ID))
        + sub("EFIT", struct.pack("<fII", 0, 17, 0)))
    # In magic-effect conditions Target is the caster. Subject is the effect
    # target/candidate. Never put the Khajiit/player restriction on candidates:
    # doing so would hide ordinary NPCs. No circular HasMagicEffect condition.
    spell += condition(136, 0x14, value=1, run_on=1)
    spell += condition(69, 0x13745, value=1, run_on=1, or_next=True)
    spell += condition(69, 0x88845, value=1, run_on=1)
    return (record("TES4", 0, header, flags=0x280)
        + group("EFSH", record("EFSH", SHADER_ID, shader_payload()))
        + group("MGEF", record("MGEF", EFFECT_ID, effect))
        + group("SPEL", record("SPEL", SPELL_ID, spell)))


TEXT = {
    "English": {
        1: "Keen Senses: Detection",
        2: "Detect living creatures within about 5 metres while casting, indoors at any hour or outdoors from 19:00 to before 06:00. Excludes corpses, undead, machines and daedra. All targets share a warm amber glow.",
        3: "Keen Senses (Concentration)",
        4: "Khajiit player only. Detect living creatures through walls within about 5 metres. Indoors at any hour; outdoors 19:00 to before 06:00. Base cost: 50 Magicka per second before modifiers. No skill experience or cooldown. Casting may consume Magicka even when detection is inactive.",
    },
    "Japanese": {
        1: "鋭敏な感覚：探知",
        2: "詠唱中、半径約5mの生物を共通の淡い黄橙色で探知する。屋内は常時、屋外は19:00から翌6:00未満に有効。死体・アンデッド・機械・デイドラは対象外。",
        3: "鋭敏な感覚（集中）",
        4: "カジートのプレイヤー専用。詠唱中、壁越しに半径約5mの生物を探知する。屋内は常時、屋外は19:00から翌6:00未満に有効。基礎消費は毎秒50マジカ（補正前）。スキル経験値・再使用待ちなし。探知が無効な時間帯も詠唱でマジカを消費する場合がある。",
    },
}


def string_table(items, length_prefixed=False):
    body, directory = bytearray(), bytearray()
    for key, value in sorted(items.items()):
        directory += struct.pack("<II", key, len(body))
        raw = ztext(value)
        body += (struct.pack("<I", len(raw)) if length_prefixed else b"") + raw
    return struct.pack("<II", len(items), len(body)) + directory + body


def make_manifest():
    return {
        "plugin": PLUGIN, "version": VERSION,
        "status": "structurally_verified_game_validation_pending",
        "master": "Skyrim.esm", "esl": True, "localized": True,
        "records": [{"id": "000800", "type": "SPEL", "editor_id": "LKSC_KeenSenses"},
                    {"id": "000801", "type": "MGEF", "editor_id": "LKSC_DetectLivingEffect"},
                    {"id": "000802", "type": "EFSH", "editor_id": "LKSC_DetectionAmberShader"}],
        "overrides": 0, "scripts": 0, "quests": 0, "additional_skse_plugins": 0,
        "cast_type": "Concentration", "delivery": "Self", "equip": "EitherHand",
        "native_area_feet": 17, "distance_cap_game_units": 350,
        "approximate_radius_metres": 5, "base_magicka_per_second": 50,
        "actual_cost": "Engine and LoreRim modifiers may change the base cost.",
        "school": "Alteration", "skill_usage_multiplier": 0, "half_cost_perk": None,
        "cooldown": None, "duration": "while casting; no timed pulse",
        "caster": "player, normal Khajiit or vampire Khajiit; Target-context CTDA",
        "distribution": "manual player.addspell only",
        "exclusions": ["GetDead", "ActorTypeUndead", "IsUndead", "ActorTypeDwarven", "ActorTypeDaedra", "NoDetectLife"],
        "availability": {
            "indoors": "all hours, based on PlayerRef IsInInterior",
            "outdoors": {"start_hour_inclusive": 19, "end_hour_exclusive": 6},
            "clock": "game time; user-selected fixed hours, not ENB brightness tracking",
            "condition_location": "MGEF; (PlayerRef indoors OR hour >= 19 OR hour < 6)",
            "forced_cast_interruption": False,
            "inactive_cast_cost": "May still consume Magicka; boundary behavior is runtime-unverified",
        },
        "shader": "local 000802 LKSC_DetectionAmberShader, same for all targets",
        "detection_color": "#E91E63", "particle_color_rgb": [233, 30, 99],
        "particle_color_mode": "direct RGB; grayscale color mapping off; palette path empty",
        "shader_baseline": "Skyrim.esm:000DC209 LifeDetectedEnemy, normalized exported settings",
        "shader_baseline_data_sha256": SHADER_BASELINE_SHA256,
        "shader_non_color_settings": "unchanged: particle count, scale, timing, alpha, blending, Z test",
        "hand_casting_art": None, "casting_animations": "unchanged",
        "display_note": "#E91E63 is the source particle RGB; ENB, additive blending and alpha affect the final screen color.",
        "external_references": {
            "00000014": "PLYR PlayerRef", "00013745": "RACE KhajiitRace",
            "00088845": "RACE KhajiitRaceVampire", "00013796": "KYWD ActorTypeUndead",
            "0001397A": "KYWD ActorTypeDwarven", "00013797": "KYWD ActorTypeDaedra",
            "000F82F4": "KYWD NoDetectLife",
            "00013F44": "EQUP EitherHand", "00104F70": "STAT MAGInvDetectLife",
            "0003F37A": "SNDR MAGAlterationDrawSheatheLPMSD",
            "0007C71F": "SNDR MAGIllusionChargeSD",
            "00081189": "SNDR MAGAlterationDetectLifeCast2DLPM",
        },
        "schema": "TES5Edit Core/wbDefinitionsTES5.pas @ 9fb016884bec138ea6c7b872cec831537d464c3e",
        "runtime_validation": "NOT RUN: Skyrim, full LoreRim profile, 19:00/06:00 transitions during casting, indoor context, inactive casting cost, daedra filtering, radius, appearance and full-restart load",
        "legacy_save_migration": "No migration or removal of old KhajiitKeenSenses script/quest state.",
        "languages": ["English", "Japanese"],
    }


def build_package(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    (path / META).mkdir(exist_ok=True)
    (path / "Strings").mkdir(exist_ok=True)
    (path / PLUGIN).write_bytes(make_plugin())
    for language, texts in TEXT.items():
        for extension, ids, prefixed in [("STRINGS", (1, 3), False),
                                         ("DLSTRINGS", (2, 4), True),
                                         ("ILSTRINGS", (), True)]:
            (path / "Strings" / f"{Path(PLUGIN).stem}_{language}.{extension}").write_bytes(
                string_table({key: texts[key] for key in ids}, prefixed))
    shutil.copyfile(ROOT / "docs/CONCENTRATION.md", path / META / "README.md")
    shutil.copyfile(ROOT / "LICENSE", path / META / "LICENSE.txt")
    (path / META / "build-manifest.json").write_text(
        json.dumps(make_manifest(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (path / META / "records.json").write_text(
        json.dumps(record_report(path / PLUGIN), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checksums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(path).as_posix()}\n"
        for p in sorted(path.rglob("*")) if p.is_file()
        and p.relative_to(path).as_posix() != META + "/SHA256SUMS.txt")
    (path / META / "SHA256SUMS.txt").write_text(checksums, encoding="utf-8")


def record_report(plugin):
    from formats import conditions, read_plugin
    records, groups = read_plugin(plugin)
    return {"validation_scope": "decoded records, not Skyrim execution", "groups": groups,
        "records": [{"type": r["type"], "file_form_id": f'{r["id"]:08X}',
            "flags": f'{r["flags"]:08X}', "subrecords": [n for n, _ in r["fields"]],
            "conditions": conditions(r)} for r in records]}


def archive_bytes(files):
    import io
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, content, compresslevel=9)
    return output.getvalue()


def publish_file(path, content):
    """Never replace an existing versioned artifact with different bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != content:
        raise ValueError(f"Refusing to overwrite a versioned artifact: {path}")
    path.write_bytes(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-only", action="store_true")
    args = parser.parse_args()
    from verify_concentration import verify_package, verify_zip
    stage = ROOT / "build" / f"concentration-{VERSION}"
    stage.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lksc-", dir=stage.parent) as temp:
        package = Path(temp)
        build_package(package)
        report = verify_package(package)
        # Only replace this dedicated generated stage after successful readback.
        if stage.exists():
            shutil.rmtree(stage)
        shutil.copytree(package, stage)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.package_only:
        return
    data = archive_bytes({p.relative_to(stage).as_posix(): p.read_bytes()
                          for p in stage.rglob("*") if p.is_file()})
    output = ROOT / "dist" / f"KhajiitKeenSensesConcentration-{VERSION}-MO2.zip"
    # Validate before installing the archive in dist/.
    with tempfile.TemporaryDirectory(dir=stage.parent) as temp:
        candidate = Path(temp) / output.name
        candidate.write_bytes(data)
        verify_zip(candidate)
    source_names = ["LICENSE", "docs/CONCENTRATION.md", "docs/CONCENTRATION_BUILD.md",
        "tools/build_concentration.py", "tools/verify_concentration.py", "tools/formats.py",
        "tools/verify_concentration_third_party.cjs", "tools/data/life_detected_enemy.json",
        "tests/test_concentration.py", "tests/fixtures/v023-concentration.json"]
    source = {name: (ROOT / name).read_bytes() for name in source_names}
    source["README.md"] = source["docs/CONCENTRATION_BUILD.md"]
    source["SHA256SUMS.txt"] = "".join(f"{hashlib.sha256(b).hexdigest()}  {n}\n"
        for n, b in sorted(source.items())).encode()
    outputs = {output: data,
        ROOT / "dist" / f"KhajiitKeenSensesConcentration-{VERSION}-source.zip": archive_bytes(source)}
    for path, content in outputs.items():
        publish_file(path, content)
        digest = hashlib.sha256(content).hexdigest()
        publish_file(path.with_suffix(".zip.sha256"), f"{digest}  {path.name}\n".encode())
        print(f"{path.name}: {len(content)} bytes; SHA256 {digest}")


if __name__ == "__main__":
    main()
