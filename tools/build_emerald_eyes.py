#!/usr/bin/env python3
"""Package one private male Khajiit eye option; standard library only."""
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.0.0"
PLUGIN = "EsteeEmeraldEyes.esp"
META = "EsteeEmeraldEyes"
TEX = "textures/actors/character/esteeemerald/estee_emerald_2edb91.dds"
ASSET = ROOT / "assets/estee-emerald/estee_emerald_2edb91.dds"
HDPT, TXST, FLST = 0x01000800, 0x01000801, 0x01000802


def sub(tag, data):
    if len(data) > 65535:
        raise ValueError("Unexpected oversized subrecord")
    return tag.encode("ascii") + struct.pack("<H", len(data)) + data


def text(value):
    return value.encode("utf-8") + b"\0"


def record(tag, form, payload, flags=0):
    return struct.pack("<4sIIIIHH", tag.encode(), len(payload), flags,
        form, 0, 44, 0) + payload


def group(tag, payload):
    return struct.pack("<4sI4sIHHHH", b"GRUP", len(payload) + 24,
        tag.encode(), 0, 0, 0, 0, 0) + payload


def plugin_bytes():
    baseline = json.loads((ROOT / "tools/data/kala_estee_eye_baseline.json").read_text())
    header = (sub("HEDR", struct.pack("<fII", 1.7, 6, 0x803))
        + sub("CNAM", text("aknkat"))
        + sub("SNAM", text("Estee Emerald Eyes 1.0.0: male Khajiit; private 2EDB91 texture; no overrides or scripts; runtime untested."))
        + sub("MAST", text("Skyrim.esm")) + sub("DATA", bytes(8)))
    hp = {"EDID": text("LKEE_MaleKhajiitEmerald2EDB91"),
        "FULL": text("Estee Emerald 2EDB91"),
        "TNAM": struct.pack("<I", TXST), "RNAM": struct.pack("<I", FLST)}
    tx = {"EDID": text("LKEE_Emerald2EDB91Texture"),
        "TX00": text(TEX.removeprefix("textures/").replace("/", "\\"))}
    def clone(kind, changes):
        return b"".join(sub(tag, changes.get(tag, bytes.fromhex(data)))
            for tag, data in baseline["records"][kind]["fields"])
    races = (sub("EDID", text("LKEE_ValidKhajiitRaces"))
        + sub("LNAM", struct.pack("<I", 0x13745))
        + sub("LNAM", struct.pack("<I", 0x88845)))
    return (record("TES4", 0, header, flags=0x200)
        + group("TXST", record("TXST", TXST, clone("TXST", tx)))
        + group("HDPT", record("HDPT", HDPT, clone("HDPT", hp)))
        + group("FLST", record("FLST", FLST, races)))


def manifest():
    return {"name": "Estee Emerald Eyes", "version": VERSION, "plugin": PLUGIN,
        "source_color_reference": "#2EDB91", "sex": "male",
        "races": ["KhajiitRace", "KhajiitRaceVampire"],
        "new_records": {"HDPT": "800", "TXST": "801", "FLST": "802"},
        "overrides": 0, "masters": ["Skyrim.esm"], "scripts": 0,
        "texture": TEX, "texture_sha256": hashlib.sha256(ASSET.read_bytes()).hexdigest(),
        "texture_format": "BC7_UNORM / 1024x1024 / 11 mipmaps",
        "normal_and_specular": "existing EyeArgonian_msn.dds / EyeArgonian_s.dds",
        "model": "existing Actors/Character/Character Assets/EyesKhajiit.nif",
        "npc_distribution": False, "game_validation": "not performed"}


def package_files():
    files = {PLUGIN: plugin_bytes(), TEX: ASSET.read_bytes(),
        META + "/README.md": (ROOT / "docs/EMERALD_EYES.md").read_bytes(),
        META + "/CREDITS.txt": (ROOT / "assets/estee-emerald/CREDITS.txt").read_bytes(),
        META + "/build-manifest.json": (json.dumps(manifest(), ensure_ascii=False, indent=2) + "\n").encode()}
    files[META + "/SHA256SUMS.txt"] = checksum_bytes(files)
    return files


def checksum_bytes(files):
    return "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n"
        for name, data in sorted(files.items())).encode()


def archive(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data, compresslevel=9)
    return stream.getvalue()


def publish(path, data):
    path.parent.mkdir(exist_ok=True, parents=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"Refusing to replace versioned artifact: {path}")
    path.write_bytes(data)


def main():
    from verify_emerald_eyes import verify_directory, verify_zip
    files = package_files()
    stage = ROOT / "build" / f"emerald-eyes-{VERSION}"
    stage.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        path = stage / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    report = verify_directory(stage)
    mo2 = archive(files)
    with tempfile.TemporaryDirectory() as temp:
        candidate = Path(temp) / "candidate.zip"
        candidate.write_bytes(mo2)
        verify_zip(candidate)
    source_names = ["tools/build_emerald_eyes.py", "tools/verify_emerald_eyes.py",
        "tools/encode_emerald_dds.py", "tools/verify_emerald_third_party.cjs", "tools/formats.py",
        "tools/data/kala_estee_eye_baseline.json", "docs/EMERALD_EYES.md",
        "docs/EMERALD_EYES_BUILD.md", "assets/estee-emerald/CREDITS.txt",
        "assets/estee-emerald/estee_emerald_2edb91.png",
        "assets/estee-emerald/estee_emerald_2edb91.dds"]
    source = {name: (ROOT / name).read_bytes() for name in source_names}
    source["README.md"] = source["docs/EMERALD_EYES_BUILD.md"]
    source["SHA256SUMS.txt"] = checksum_bytes(source)
    for suffix, data in [("MO2", mo2), ("source", archive(source))]:
        output = ROOT / "dist" / f"EsteeEmeraldEyes-{VERSION}-{suffix}.zip"
        publish(output, data)
        digest = hashlib.sha256(data).hexdigest()
        publish(output.with_suffix(".zip.sha256"), f"{digest}  {output.name}\n".encode())
        print(f"{output.name}: {len(data)} bytes, SHA256 {digest}")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
