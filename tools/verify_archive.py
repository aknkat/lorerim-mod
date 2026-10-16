#!/usr/bin/env python3
"""Verify MO2 root layout, CRCs and every archived file's SHA256."""
import hashlib
from pathlib import PurePosixPath
import sys
import zipfile


def verify(path):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC failure")
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP member")
        for name in names:
            parts = PurePosixPath(name).parts
            if name.startswith("/") or ".." in parts or "\\" in name:
                raise ValueError("Unsafe archive path")
        runtime = {"KhajiitKeenSenses.esp", "Scripts/LKS_KeenSensesEffect.pex",
                   "Scripts/Source/LKS_KeenSensesEffect.psc"}
        namespaced = "KhajiitKeenSenses/README.md" in names
        # Keep verifying the archived v0.1.0/probe1 artifacts as historical files.
        if namespaced:
            metadata = "KhajiitKeenSenses/"
            expected = runtime | {metadata + name for name in (
                "README.md", "LICENSE.txt", "build-manifest.json", "SHA256SUMS.txt")}
            if any(name not in runtime and not name.startswith((metadata,
                   "Strings/KhajiitKeenSenses_")) for name in names):
                raise ValueError("Unexpected shared file path outside the mod namespace")
        else:
            metadata = ""
            expected = runtime | {"README.md", "KhajiitKeenSenses-LICENSE.txt",
                                  "build-manifest.json", "SHA256SUMS.txt"}
        if not expected.issubset(names):
            raise ValueError("Incomplete MO2 data-root layout")
        if any(name.lower() == "license" for name in names):
            raise ValueError("Generic root LICENSE would conflict with other MO2 mods")
        if [n for n in names if n.lower().endswith(".pex")] != ["Scripts/LKS_KeenSensesEffect.pex"]:
            raise ValueError("Unexpected bundled runtime/SDK script")
        if len([n for n in names if n.startswith("Strings/")]) != 6:
            raise ValueError("Missing English/Japanese localization tables")
        checked = set()
        checksum_path = metadata + "SHA256SUMS.txt"
        for line in archive.read(checksum_path).decode().splitlines():
            digest, name = line.split("  ", 1)
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError(f"Checksum mismatch: {name}")
            if name in checked:
                raise ValueError("Duplicate checksum entry")
            checked.add(name)
        if checked != set(names) - {checksum_path}:
            raise ValueError("Incomplete checksum coverage")
    print(f"ZIP verified: {len(names)} files, safe MO2 root layout, CRC and SHA256 passed.")


if __name__ == "__main__":
    verify(sys.argv[1])
