#!/usr/bin/env python3
"""Build the script-free 0.2.0 spell without touching any historical archive.

Only Python's standard library is needed. This writer follows xEdit's TES5
SPEL/MGEF schema, not a patched or redistributed game record. Readback uses
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
VERSION = "0.2.0"
META = "KhajiitKeenSensesConcentration"
SPELL_ID, EFFECT_ID = 0x01000800, 0x01000801


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


def condition(function, p1=0, *, value=0, operator=0, run_on=0, or_next=False):
    return sub("CTDA", struct.pack("<B3xfH2xIIIIi",
        (operator << 5) | int(or_next), value, function, p1, 0, run_on, 0, -1))


def make_plugin():
    header = (sub("HEDR", struct.pack("<fII", 1.7, 4, 0x802))
        + sub("CNAM", ztext("aknkat"))
        + sub("SNAM", ztext("Keen Senses Concentration 0.2.0: 6m, base 25/s, no scripts; game validation pending."))
        + sub("MAST", ztext("Skyrim.esm")) + sub("DATA", bytes(8)))

    data = bytearray(152)
    # Native Concentration Detect Life shape. No PowerAffectsMagnitude/Duration,
    # NoArea, hostile, detrimental, script archetype, or runtime VMAD.
    struct.pack_into("<I", data, 0, 0x04021412)
    struct.pack_into("<f", data, 4, 25)
    struct.pack_into("<ii", data, 12, 18, -1)  # Alteration; no resistance AV.
    struct.pack_into("<I", data, 32, 0xDC209)  # Native red LifeDetectedEnemy.
    struct.pack_into("<I", data, 44, 20)      # Feet, not magnitude/metres.
    struct.pack_into("<Ii", data, 64, 19, -1)  # Detect Life, ActorValue None.
    struct.pack_into("<IIi", data, 80, 2, 0, -1)  # Concentration, Self, AV None.
    struct.pack_into("<I", data, 92, 0x2FB1C)  # DetectLifeFXHand01, reference only.
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
    for keyword in (0x13796, 0x1397A, 0xF82F4):
        effect += condition(560, keyword)  # Undead, Dwarven, NoDetectLife.
    effect += condition(715)  # IsUndead == 0.
    effect += condition(1, 0x14, value=420, operator=5)  # <= ~6m from PlayerRef.

    # Keep native concentration spell handling and hand casting, not Voice.
    # ManualCostCalc overrides auto-calculation, NOT the engine's actor/perk
    # cost adjustments. No castingPerk reference and no free-cost flags.
    spit = struct.pack("<IIIfIIffI", 25, 0x00B80001, 0, 0, 2, 0, 0, 0, 0)
    spell = (sub("EDID", ztext("LKSC_KeenSenses")) + sub("OBND", bytes(12))
        + sub("FULL", struct.pack("<I", 3))
        + sub("MDOB", struct.pack("<I", 0x104F70))
        + sub("ETYP", struct.pack("<I", 0x13F44))
        + sub("DESC", struct.pack("<I", 4)) + sub("SPIT", spit)
        + sub("EFID", struct.pack("<I", EFFECT_ID))
        + sub("EFIT", struct.pack("<fII", 0, 20, 0)))
    # In magic-effect conditions Target is the caster. Subject is the effect
    # target/candidate. Never put the Khajiit/player restriction on candidates:
    # doing so would hide ordinary NPCs. No circular HasMagicEffect condition.
    spell += condition(136, 0x14, value=1, run_on=1)
    spell += condition(69, 0x13745, value=1, run_on=1, or_next=True)
    spell += condition(69, 0x88845, value=1, run_on=1)
    return (record("TES4", 0, header, flags=0x280)
        + group("MGEF", record("MGEF", EFFECT_ID, effect))
        + group("SPEL", record("SPEL", SPELL_ID, spell)))


TEXT = {
    "English": {
        1: "Keen Senses: Detection",
        2: "Detect living creatures within about 6 metres while casting. All targets appear red. Excludes corpses, undead and machines.",
        3: "Keen Senses (Concentration)",
        4: "Khajiit player only. Detect nearby living creatures through walls while casting. Range: about 6 metres. Base cost: 25 Magicka per second before modifiers. No skill experience or cooldown.",
    },
    "Japanese": {
        1: "鋭敏な感覚：探知",
        2: "詠唱中、半径約6mの生物を共通の赤色で探知する。死体・アンデッド・機械は対象外。",
        3: "鋭敏な感覚（集中）",
        4: "カジートのプレイヤー専用。詠唱中、壁越しに半径約6mの生物を探知する。基礎消費は毎秒25マジカ（補正前）。スキル経験値・再使用待ちなし。",
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
                    {"id": "000801", "type": "MGEF", "editor_id": "LKSC_DetectLivingEffect"}],
        "overrides": 0, "scripts": 0, "quests": 0, "additional_skse_plugins": 0,
        "cast_type": "Concentration", "delivery": "Self", "equip": "EitherHand",
        "native_area_feet": 20, "distance_cap_game_units": 420,
        "approximate_radius_metres": 6, "base_magicka_per_second": 25,
        "actual_cost": "Engine and LoreRim modifiers may change the base cost.",
        "school": "Alteration", "skill_usage_multiplier": 0, "half_cost_perk": None,
        "cooldown": None, "duration": "while casting; no timed pulse",
        "caster": "player, normal Khajiit or vampire Khajiit; Target-context CTDA",
        "distribution": "manual player.addspell only",
        "exclusions": ["GetDead", "ActorTypeUndead", "IsUndead", "ActorTypeDwarven", "NoDetectLife"],
        "shader": "Skyrim.esm:000DC209 LifeDetectedEnemy, same for all targets",
        "external_references": {
            "00000014": "PLYR PlayerRef", "00013745": "RACE KhajiitRace",
            "00088845": "RACE KhajiitRaceVampire", "00013796": "KYWD ActorTypeUndead",
            "0001397A": "KYWD ActorTypeDwarven", "000F82F4": "KYWD NoDetectLife",
            "000DC209": "EFSH LifeDetectedEnemy", "00013F44": "EQUP EitherHand",
            "00104F70": "STAT MAGInvDetectLife", "0002FB1C": "ARTO DetectLifeFXHand01",
            "0003F37A": "SNDR MAGAlterationDrawSheatheLPMSD",
            "0007C71F": "SNDR MAGIllusionChargeSD",
            "00081189": "SNDR MAGAlterationDetectLifeCast2DLPM",
        },
        "schema": "TES5Edit Core/wbDefinitionsTES5.pas @ 9fb016884bec138ea6c7b872cec831537d464c3e",
        "runtime_validation": "NOT RUN: Skyrim, full LoreRim profile, radius/filter contexts, real cost, skill XP, release and full-restart load",
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
    stage = ROOT / "build/concentration-0.2.0"
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
        "tools/verify_concentration_third_party.cjs", "tests/test_concentration.py"]
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
