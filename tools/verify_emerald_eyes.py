#!/usr/bin/env python3
"""Independent structural/readback verification; does not execute Skyrim."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import zipfile

from formats import field, fields, read_plugin

PLUGIN = "EsteeEmeraldEyes.esp"
TEX = "textures/actors/character/esteeemerald/estee_emerald_2edb91.dds"
META = "EsteeEmeraldEyes"
EXPECTED = {PLUGIN, TEX, META + "/README.md", META + "/CREDITS.txt",
    META + "/build-manifest.json", META + "/SHA256SUMS.txt"}


def require(test, message):
    if not test:
        raise ValueError(message)


def verify_dds(data):
    require(len(data) >= 148 and data[:4] == b"DDS ", "Invalid DDS")
    require(struct.unpack_from("<I", data, 4)[0] == 124, "DDS header size")
    flags, height, width, linear, depth, mips = struct.unpack_from("<6I", data, 8)
    require((height, width, linear, depth, mips) == (1024, 1024, 1048576, 0, 11), "DDS dimensions/mips")
    require(flags == 0xA1007, "DDS flags")
    require(struct.unpack_from("<II4s", data, 76) == (32, 4, b"DX10"), "DDS pixel format")
    require(struct.unpack_from("<5I", data, 128) == (98, 3, 0, 1, 1), "BC7_UNORM / straight alpha required")
    require(struct.unpack_from("<5I", data, 108) == (0x401008, 0, 0, 0, 0), "DDS caps")
    length = 148
    for power in range(10, -1, -1):
        length += max(1, ((1 << power) + 3) // 4) ** 2 * 16
    require(length == len(data), "Truncated or trailing mip data")


def verify_plugin(path):
    records, groups = read_plugin(path)
    require(groups == [("TXST", 0), ("HDPT", 0), ("FLST", 0)], "Unexpected groups")
    require([(r["type"], r["id"]) for r in records] ==
        [("TES4", 0), ("TXST", 0x01000801), ("HDPT", 0x01000800), ("FLST", 0x01000802)], "Unexpected records or overrides")
    header, tx, hp, races = records
    require(header["flags"] == 0x200, "Expected unlocalized ESL-flagged ESP")
    require(fields(header, "MAST") == [b"Skyrim.esm\0"], "Unexpected masters")
    version, count, nextid = struct.unpack("<fII", field(header, "HEDR"))
    require(abs(version - 1.7) < 0.00001 and count == 6 and nextid == 0x803, "Invalid HEDR")
    require(all(r["version"] == 44 for r in records), "Unexpected record version")
    require(all(r["flags"] == 0 for r in records[1:]), "Unexpected data record flags")
    require(not any(n == "VMAD" for r in records for n, _ in r["fields"]), "Unexpected Papyrus")
    require(field(hp, "DATA") == b"\x03", "Must be playable male")
    require(field(hp, "PNAM") == struct.pack("<I", 2), "Must be eyes")
    require(field(hp, "FULL") == b"Estee Emerald 2EDB91\0", "Unexpected name")
    require(field(hp, "TNAM") == struct.pack("<I", tx["id"]), "Unresolved TXST")
    require(field(hp, "RNAM") == struct.pack("<I", races["id"]), "Unresolved valid races")
    require(field(tx, "TX00") == TEX.removeprefix("textures/").replace("/", "\\").encode() + b"\0", "Not a private texture path")
    require(fields(races, "LNAM") == [struct.pack("<I", r) for r in (0x13745, 0x88845)], "Unexpected races")
    require([n for n, _ in races["fields"]] == ["EDID", "LNAM", "LNAM"], "Unexpected FLST fields")
    baseline = json.loads((Path(__file__).resolve().parent / "data/kala_estee_eye_baseline.json").read_text())
    for kind, rec, allowed in [("HDPT", hp, {"EDID", "FULL", "TNAM", "RNAM"}),
                               ("TXST", tx, {"EDID", "TX00"})]:
        original = [(n, bytes.fromhex(d)) for n, d in baseline["records"][kind]["fields"]]
        require([n for n, _ in rec["fields"]] == [n for n, _ in original], f"{kind} fields changed")
        require([(n, d) for n, d in rec["fields"] if n not in allowed] ==
            [(n, d) for n, d in original if n not in allowed], f"Shared {kind} settings changed")


def verify_directory(directory):
    directory = Path(directory)
    names = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
    require(names == EXPECTED, "Unexpected or missing package members")
    verify_plugin(directory / PLUGIN)
    data = (directory / TEX).read_bytes()
    verify_dds(data)
    manifest = json.loads((directory / META / "build-manifest.json").read_text())
    require(manifest["version"] == "1.0.0" and manifest["plugin"] == PLUGIN, "Manifest identity")
    require(manifest["source_color_reference"] == "#2EDB91" and manifest["overrides"] == 0, "Manifest settings")
    require(manifest["texture_sha256"] == hashlib.sha256(data).hexdigest(), "Texture checksum")
    require(manifest["npc_distribution"] is False and manifest["scripts"] == 0, "Unexpected runtime features")
    checksumfile = META + "/SHA256SUMS.txt"
    checks = {}
    for line in (directory / checksumfile).read_text().splitlines():
        digest, name = line.split("  ", 1)
        require(name in names and name not in checks, "Unexpected checksum member")
        require(hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest, "File checksum mismatch")
        checks[name] = digest
    require(set(checks) == names - {checksumfile}, "Missing checksums")
    return {"records": {"HDPT": 1, "TXST": 1, "FLST": 1}, "overrides": 0,
        "masters": ["Skyrim.esm"], "scripts": 0, "files": len(names),
        "color_reference": "#2EDB91", "texture": "BC7_UNORM / 1024x1024 / 11 mips",
        "shared_model_normal_specular": "unchanged from source eye option",
        "scope": "structural checks; game/ENB/save-load untested"}


def verify_zip(path):
    with zipfile.ZipFile(path) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())), "Duplicate ZIP member")
        require(set(archive.namelist()) == EXPECTED, "Unexpected ZIP paths")
        require(archive.testzip() is None, "ZIP CRC failure")
        with tempfile.TemporaryDirectory() as temp:
            for name in archive.namelist():
                target = Path(temp) / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(name))
            return verify_directory(temp)


def decode_dds(directory):
    """Optional independent BC7 decode of every mip using Pillow."""
    from PIL import Image
    data = (Path(directory) / TEX).read_bytes()
    verify_dds(data)
    import io
    offset = 148
    decoded = []
    for power in range(10, -1, -1):
        size = 1 << power
        length = max(1, (size + 3) // 4) ** 2 * 16
        header = bytearray(data[:148])
        struct.pack_into("<IIIIII", header, 8, 0x81007, size, size, length, 0, 1)
        struct.pack_into("<I", header, 108, 0x1000)
        image = Image.open(io.BytesIO(bytes(header) + data[offset:offset+length]))
        image.load()
        require(image.size == (size, size) and image.mode == "RGBA", "Mip decode failed")
        if power == 10:
            source = Image.open(Path(__file__).resolve().parent.parent /
                "assets/estee-emerald/estee_emerald_2edb91.png").convert("RGBA")
            raw, output = source.tobytes(), image.tobytes()
            errors = [sum(abs(a - b) for a, b in zip(raw[i::4], output[i::4])) /
                (size * size) for i in range(4)]
            max_alpha = max(abs(a - b) for a, b in zip(raw[3::4], output[3::4]))
            require(max(errors[:3]) < 2 and errors[3] < 0.1 and max_alpha <= 8,
                f"Excessive BC7 error: {errors}, alpha max {max_alpha}")
            decoded.append({"rgba_mean_absolute_error": errors, "alpha_max_error": max_alpha})
        offset += length
    return {"decoded_mips": 11, "top_mip_comparison": decoded[0]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--decode-dds", action="store_true")
    args = parser.parse_args()
    report = verify_zip(args.path) if args.path.is_file() else verify_directory(args.path)
    if args.decode_dds:
        require(args.path.is_dir(), "Use a directory for optional DDS decoding")
        report["dds_decode"] = decode_dds(args.path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
