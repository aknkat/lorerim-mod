#!/usr/bin/env python3
"""Package the read-only xEdit report script; no game/runtime assets included."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "dist/LKS-Detection-Record-Export.zip"


def package():
    members = {
        "Edit Scripts/LKS - Export detection records.pas": (
            ROOT / "tools/xedit/LKS - Export detection records.pas").read_bytes(),
        "LKS-RecordExport-README.md": (
            ROOT / "docs/EXPORT_DETECTION_RECORDS.md").read_bytes(),
    }
    checksums = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n"
                        for name, data in members.items())
    members["LKS-RecordExport-SHA256SUMS.txt"] = checksums.encode("utf-8")
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)
    with zipfile.ZipFile(OUTPUT) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(members):
            raise ValueError("Invalid helper archive")
        for name, expected in members.items():
            if archive.read(name) != expected:
                raise ValueError(f"Archive content differs: {name}")
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    OUTPUT.with_suffix(".zip.sha256").write_text(f"{digest}  {OUTPUT.name}\n")
    print(f"Verified helper ZIP: {OUTPUT.name}, {OUTPUT.stat().st_size} bytes, SHA256 {digest}")


if __name__ == "__main__":
    package()
