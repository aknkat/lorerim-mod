#!/usr/bin/env python3
"""Independent structural/packaging checks for the script-free spell.

No import from its writer. These checks can reject broken/unsafe artifacts;
they cannot prove condition contexts or Skyrim/LoreRim runtime behavior.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import struct
import sys
import tempfile
import zipfile

from formats import conditions, field, fields, read_plugin, strings_table

PLUGIN = "KhajiitKeenSensesConcentration.esp"
META = "KhajiitKeenSensesConcentration"


def require(value, message):
    if not value:
        raise ValueError(message)


def verify_plugin(path):
    records, groups = read_plugin(path)
    require(len(records) == 4 and records[0]["type"] == "TES4", "Expected header + 3 new records")
    header = records[0]
    require(header["id"] == 0 and header["flags"] == 0x280, "Expected localized ESL ESP")
    require(fields(header, "MAST") == [b"Skyrim.esm\0"], "Skyrim.esm must be the sole master")
    version, count, next_id = struct.unpack("<fII", field(header, "HEDR"))
    require(abs(version - 1.7) < 1e-6 and count == 6 and next_id == 0x803, "Invalid HEDR counts")
    require(sorted(groups) == [("EFSH", 0), ("MGEF", 0), ("SPEL", 0)], "Unexpected group/quest/distribution")
    forms = {r["id"]: r for r in records[1:]}
    require(set(forms) == {0x01000800, 0x01000801, 0x01000802}, "Existing-record override or unexpected form")
    require(all(r["flags"] == 0 and r["version"] == 44 for r in forms.values()), "Record flags/version")
    require(all(not fields(r, "VMAD") for r in records), "VMAD/scripts must be absent")
    spell, effect = forms[0x01000800], forms[0x01000801]
    shader = forms[0x01000802]
    require(spell["type"] == "SPEL" and effect["type"] == "MGEF", "Wrong local record types")
    require(field(spell, "EDID") == b"LKSC_KeenSenses\0", "Unexpected spell editor ID")
    require(field(effect, "EDID") == b"LKSC_DetectLivingEffect\0", "Unexpected effect editor ID")
    require([n for n, _ in spell["fields"]] == ["EDID", "OBND", "FULL", "MDOB", "ETYP", "DESC",
        "SPIT", "EFID", "EFIT", "CTDA", "CTDA", "CTDA"], "Unexpected SPEL field order or extra effect")
    require([n for n, _ in effect["fields"]] == ["EDID", "FULL", "MDOB", "DATA", "SNDD", "SNDD",
        "SNDD", "DNAM"] + ["CTDA"] * 10, "Unexpected MGEF field order or extra runtime field")
    spit = struct.unpack("<IIIfIIffI", field(spell, "SPIT"))
    require(spit == (50, 0xB80001, 0, 0, 2, 0, 0, 0, 0), "Wrong base cost, type, flags, casting or half-cost perk")
    require(struct.unpack("<I", field(spell, "ETYP"))[0] == 0x13F44, "Must use EitherHand, not Voice")
    require(field(spell, "EFID") == struct.pack("<I", 0x01000801), "Broken local effect link")
    require(struct.unpack("<fII", field(spell, "EFIT")) == (0, 17, 0), "Wrong area or timed pulse")
    for r in [spell, effect]:
        require(field(r, "MDOB") == struct.pack("<I", 0x104F70), "Wrong display object")
    data = field(effect, "DATA")
    require(len(data) == 152, "Invalid SSE MGEF DATA length")
    require(struct.unpack_from("<I", data)[0] == 0x04021412, "Unsafe/wrong effect flags")
    require(struct.unpack_from("<f", data, 4)[0] == 50, "Unexpected effect base cost")
    require(struct.unpack_from("<ii", data, 12) == (18, -1), "Wrong school or resistance AV")
    require(struct.unpack_from("<I", data, 32)[0] == 0x01000802, "Must use the dedicated local shader")
    require(struct.unpack_from("<II", data, 40) == (0, 17), "Wrong minimum skill or spellmaking area")
    require(struct.unpack_from("<Ii", data, 64) == (19, -1), "Must be native Detect Life / AV None")
    require(struct.unpack_from("<IIi", data, 80) == (2, 0, -1), "Inconsistent MGEF Concentration/Self")
    require(struct.unpack_from("<I", data, 92)[0] == 0, "Hand casting art must be NULL")
    require(struct.unpack_from("<f", data, 104)[0] == 0, "Skill XP must be zero")
    require(struct.unpack_from("<f", data, 112)[0] == 1, "Unexpected dual cast scale")
    require(struct.unpack_from("<I", data, 140)[0] == 2, "Unexpected casting sound level")
    # All optional form-link slots except the private hit shader stay empty.
    for offset in [8, 24, 36, 72, 76, 92, 96, 100, 108, 116, 120, 124, 128, 132, 136]:
        require(data[offset:offset + 4] == bytes(4), f"Unexpected linked record at MGEF offset {offset}")
    require([struct.unpack("<II", b) for b in fields(effect, "SNDD")] ==
        [(0, 0x3F37A), (1, 0x7C71F), (2, 0x81189)], "Wrong native sounds")
    target = conditions(effect)[:7]
    require([(c["function"], c["p1"], c["value"], c["operator"]) for c in target] ==
        [(46, 0, 0, 0), (560, 0x13796, 0, 0), (560, 0x1397A, 0, 0),
         (560, 0x13797, 0, 0), (560, 0xF82F4, 0, 0), (715, 0, 0, 0),
         (1, 0x14, 350, 5)], "Wrong exclusion/radius conditions")
    require(all(c["run_on"] == 0 and not c["or"] for c in target), "Candidate filter context/logic")
    availability = conditions(effect)[7:]
    require([(c["function"], c["p1"], c["value"], c["operator"], c["or"])
        for c in availability] == [(300, 0, 1, 0, True), (18, 0, 19, 3, True), (18, 0, 6, 4, False)],
        "Wrong indoor/night hours or OR grouping")
    require(all(c["run_on"] == 2 and c["reference"] == 0x14 for c in availability),
        "Indoor/night conditions must run on explicit PlayerRef")
    caster = conditions(spell)
    require([(c["function"], c["p1"], c["value"], c["or"]) for c in caster] ==
        [(136, 0x14, 1, False), (69, 0x13745, 1, True), (69, 0x88845, 1, False)], "Wrong caster guards")
    require(all(c["run_on"] == 1 and c["operator"] == 0 for c in caster), "Caster must be Target-context")
    require(all(c["p2"] == 0 and c["reference"] == 0 and c["p3"] == -1 for c in caster + target), "Unexpected condition payload")
    require(all(c["p2"] == 0 and c["p3"] == -1 for c in availability), "Unexpected availability payload")
    verify_shader(shader)
    return {"records": 3, "overrides": 0, "master": "Skyrim.esm", "scripts": 0,
        "base_cost_per_second": 50, "area_feet": 17, "distance_cap_units": 350,
        "availability": "PlayerRef indoors OR game hour >= 19 OR game hour < 6",
        "skill_usage_multiplier": 0, "detection_color": "#FAAB76", "casting_art": None,
        "scope": "structural checks only; Skyrim execution not tested"}


def verify_shader(shader):
    require(shader["type"] == "EFSH", "Wrong local shader type")
    require([n for n, _ in shader["fields"]] == ["EDID", "ICON", "ICO2", "NAM7", "NAM8", "NAM9", "DATA"],
        "Unexpected shader fields")
    require(field(shader, "EDID") == b"LKSC_DetectionAmberShader\0", "Wrong shader editor ID")
    require(field(shader, "ICO2") == b"Effects\\SmallGlowSwirls.dds\0", "Unexpected particle texture")
    require(all(field(shader, t) == b"\0" for t in ["ICON", "NAM7", "NAM8", "NAM9"]), "Unused shader texture/palette must be empty")
    data = field(shader, "DATA")
    require(len(data) == 400, "Invalid complete Skyrim EFSH DATA length")
    require(all(data[o:o+4] == bytes([250, 171, 118, 0]) for o in [188, 192, 196]), "Shader RGB must be #FAAB76")
    require(struct.unpack_from("<I", data, 384)[0] == 1, "Wrong shader flags: require direct RGB, particles on, membrane off")
    baseline_path = Path(__file__).resolve().parent / "data/life_detected_enemy.json"
    baseline = bytes.fromhex(json.loads(baseline_path.read_text())["data_hex"])
    require(hashlib.sha256(baseline).hexdigest() == "1c199d7ee9487267c1b8261f655878afc0168f760df662625a25cb0d537fce7c",
        "Unexpected standard shader baseline")
    permitted = set(range(188, 200)) | set(range(384, 388))
    require(all(a == b for i, (a, b) in enumerate(zip(data, baseline)) if i not in permitted),
        "Shader changes non-color particle/alpha/blending/depth settings")


def verify_package(path):
    path = Path(path)
    names = {p.relative_to(path).as_posix() for p in path.rglob("*") if p.is_file()}
    expected = {PLUGIN} | {META + "/" + n for n in ["README.md", "LICENSE.txt", "build-manifest.json", "records.json", "SHA256SUMS.txt"]}
    expected |= {f"Strings/KhajiitKeenSensesConcentration_{language}.{ext}"
        for language in ["English", "Japanese"] for ext in ["STRINGS", "DLSTRINGS", "ILSTRINGS"]}
    require(names == expected, "Unexpected/missing file; scripts, DLLs and shared paths are forbidden")
    report = verify_plugin(path / PLUGIN)
    for language in ["English", "Japanese"]:
        stem = path / "Strings" / f"KhajiitKeenSensesConcentration_{language}"
        st = strings_table(str(stem) + ".STRINGS")
        dl = strings_table(str(stem) + ".DLSTRINGS")
        il = strings_table(str(stem) + ".ILSTRINGS")
        require(set(st) == {1, 3} and set(dl) == {2, 4} and il == {}, "Broken localization ID coverage")
        require(all(isinstance(v, str) and v for v in list(st.values()) + list(dl.values())), "Empty/invalid localization")
        require(all(s in dl[4] for s in ["50", "5", "19:00", "6:00"]), "Wrong localized specification")
        require(("daedra" in dl[2]) if language == "English" else ("デイドラ" in dl[2]), "Missing daedra exclusion text")
    manifest = json.loads((path / META / "build-manifest.json").read_text(encoding="utf-8"))
    require(manifest["plugin"] == PLUGIN and manifest["version"] == "0.2.9", "Wrong package identity")
    require(manifest["overrides"] == manifest["scripts"] == manifest["quests"] == manifest["additional_skse_plugins"] == 0,
        "Incorrect runtime dependency claims")
    require(manifest["status"] == "structurally_verified_game_validation_pending", "Unsupported runtime validation claim")
    require(manifest["detection_color"] == "#FAAB76" and manifest["hand_casting_art"] is None, "Wrong appearance metadata")
    require(manifest["native_area_feet"] == 17 and manifest["distance_cap_game_units"] == 350
        and manifest["approximate_radius_metres"] == 5 and manifest["base_magicka_per_second"] == 50,
        "Wrong balance metadata")
    require(manifest["availability"]["outdoors"] == {"start_hour_inclusive": 19, "end_hour_exclusive": 6}
        and manifest["availability"]["indoors"] == "all hours, based on PlayerRef IsInInterior"
        and manifest["availability"]["forced_cast_interruption"] is False, "Wrong availability metadata")
    require("ActorTypeDaedra" in manifest["exclusions"], "Missing daedra exclusion metadata")
    checksum = META + "/SHA256SUMS.txt"
    checked = set()
    for line in (path / checksum).read_text().splitlines():
        digest, name = line.split("  ", 1)
        require(name in names and name not in checked, "Unsafe/duplicate checksum name")
        require(hashlib.sha256((path / name).read_bytes()).hexdigest() == digest, f"Checksum mismatch: {name}")
        checked.add(name)
    require(checked == names - {checksum}, "Incomplete checksum coverage")
    return dict(report, files=len(names), localization="English + Japanese", checksum="all members passed")


def verify_zip(path):
    with zipfile.ZipFile(path) as z:
        require(z.testzip() is None, "ZIP CRC failure")
        names = z.namelist()
        require(len(names) == len(set(n.casefold() for n in names)), "Duplicate/case-colliding ZIP paths")
        for info in z.infolist():
            name = info.filename
            require(not name.startswith("/") and ".." not in PurePosixPath(name).parts
                and "\\" not in name and ":" not in name and not info.is_dir(), "Unsafe ZIP path")
            require((info.external_attr >> 16) & 0o170000 != 0o120000, "ZIP symlink")
        with tempfile.TemporaryDirectory(prefix="lksc-verify-") as temp:
            z.extractall(temp)
            return verify_package(temp)


if __name__ == "__main__":
    target = Path(sys.argv[1])
    print(json.dumps(verify_package(target) if target.is_dir() else verify_zip(target), ensure_ascii=False, indent=2))
