#!/usr/bin/env python3
"""Build the real ESP and compiled PEX, verify, then produce an MO2 ZIP."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from formats import normalize_pex, repair_caprica_skyrim_size

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "package"
CAPRICA_SHA256 = "389fef19a803c36342fa7f733c96b6e27ef10fcd0b171af10427e29cbe153ec6"
SCRIPTS = ("LKS_KeenSensesEffect", "LKS_KeenSensesController")


def windows_path(path, wine):
    path = str(Path(path).resolve())
    return "Z:" + path.replace("/", "\\") if wine else path


def archive(package, output, checksum_path="SHA256SUMS.txt"):
    paths = sorted(p for p in package.rglob("*") if p.is_file())
    checksums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(package).as_posix()}\n"
                        for p in paths if p.relative_to(package).as_posix() != checksum_path)
    (package / checksum_path).write_text(checksums, encoding="utf-8")
    paths = sorted(p for p in package.rglob("*") if p.is_file())
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in paths:
            info = zipfile.ZipInfo(path.relative_to(package).as_posix(), (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, path.read_bytes(), compresslevel=9)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n")
    print(f"MO2 ZIP: {output} ({output.stat().st_size} bytes)\nSHA256: {digest}")


def source_archive(output):
    """Separate development-source ZIP; never mix compiler API stubs into Data."""
    paths = [ROOT / name for name in ("README.md", "LICENSE", ".gitignore")]
    extensions = {".md", ".py", ".cs", ".csproj", ".json", ".psc", ".flg", ".pas"}
    for directory in ("docs", "scripts/source", "tools", "tests"):
        for path in (ROOT / directory).rglob("*"):
            relative = path.relative_to(ROOT)
            if path.is_file() and path.suffix in extensions and not (
                    {"bin", "obj", "__pycache__"} & set(relative.parts)):
                paths.append(path)
    paths = sorted(set(paths))
    hashes = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}\n"
                     for p in paths)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in [(p.relative_to(ROOT).as_posix(), p.read_bytes()) for p in paths] + [
                ("SHA256SUMS.txt", hashes.encode())]:
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data, compresslevel=9)
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None or any(name.endswith(".pex") for name in z.namelist()):
            raise ValueError("Invalid source-only ZIP")
        for line in hashes.splitlines():
            digest, name = line.split("  ", 1)
            if hashlib.sha256(z.read(name)).hexdigest() != digest:
                raise ValueError("Source ZIP checksum failure")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n")
    print(f"Development source ZIP: {output} ({output.stat().st_size} bytes)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dotnet", default="dotnet")
    parser.add_argument("--caprica", required=True, type=Path, help="Official Caprica v0.3.0 executable")
    parser.add_argument("--wine", help="Wine loader on Linux; omit on Windows")
    parser.add_argument("--api-dir", type=Path, default=ROOT / "tools" / "papyrus-api")
    args = parser.parse_args()
    compiler = args.caprica.resolve()
    if hashlib.sha256(compiler.read_bytes()).hexdigest() != CAPRICA_SHA256:
        parser.error("Caprica executable does not match the pinned upstream v0.3.0 release")
    # Only remove generated files in our dedicated ignored build directory.
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    (PACKAGE / "Scripts" / "Source").mkdir(parents=True)
    project = ROOT / "tools" / "PluginBuilder" / "PluginBuilder.csproj"
    subprocess.run([args.dotnet, "restore", str(project), "--locked-mode"], cwd=ROOT, check=True)
    subprocess.run([args.dotnet, "run", "--project", str(project), "--no-restore",
                    "--configuration", "Release", "--", str(PACKAGE)], cwd=ROOT, check=True)
    command = ([args.wine] if args.wine else []) + [str(compiler), "--game=skyrim",
               "--strict", "--champollion-compat=false", "--enable-debug-info=false",
               "--all-warnings-as-errors",
               "--flags=" + windows_path(args.api_dir / "TESV_Papyrus_Flags.flg", args.wine),
               "--import=" + windows_path(args.api_dir, args.wine),
               "--output=" + windows_path(PACKAGE / "Scripts", args.wine)]
    command += [name + ".psc" for name in SCRIPTS]
    subprocess.run(command, cwd=ROOT / "scripts" / "source", check=True)
    for name in SCRIPTS:
        pex = PACKAGE / "Scripts" / (name + ".pex")
        if repair_caprica_skyrim_size(pex):
            print(f"Normalized PEX object size: {name}; strict parse passed.")
        normalize_pex(pex)
        subprocess.run([args.dotnet, "run", "--project", str(project), "--no-build",
                        "--configuration", "Release", "--", "--verify-pex", str(pex)],
                       cwd=ROOT, check=True)
        shutil.copy2(ROOT / "scripts" / "source" / (name + ".psc"), PACKAGE / "Scripts" / "Source")
    metadata = PACKAGE / "KhajiitKeenSenses"
    for name in ("README.md", "LICENSE"):
        shutil.copy2(ROOT / name, metadata / ("LICENSE.txt" if name == "LICENSE" else name))
    shutil.copytree(ROOT / "docs", metadata / "docs", ignore=shutil.ignore_patterns(
        "DETECTION_PROBE.md", "EXPORT_DETECTION_RECORDS.md"))
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)
    archive(PACKAGE, ROOT / "dist" / "KhajiitKeenSenses-0.1.3-MO2.zip",
            checksum_path="KhajiitKeenSenses/SHA256SUMS.txt")
    subprocess.run([sys.executable, str(ROOT / "tools" / "verify_archive.py"),
                    str(ROOT / "dist" / "KhajiitKeenSenses-0.1.3-MO2.zip")], cwd=ROOT, check=True)
    source_archive(ROOT / "dist" / "KhajiitKeenSenses-0.1.3-source.zip")


if __name__ == "__main__":
    main()
