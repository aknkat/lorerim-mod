#!/usr/bin/env python3
"""Encode the prepared RGBA texture; no image color editing occurs here.

Requires ImageMagick and ispc_texcomp==1.0.1 (build tools only).
"""
import argparse
import importlib.metadata
from pathlib import Path
import struct
import subprocess
import tempfile


def encode(source, output):
    import ispc_texcomp as bc
    if importlib.metadata.version("ispc_texcomp") != "1.0.1":
        raise ValueError("Use ispc_texcomp==1.0.1")
    settings = bc.BC7EncSettings.from_profile("alpha_slow")
    levels = []
    with tempfile.TemporaryDirectory(prefix="emerald-mips-") as temp:
        for power in range(10, -1, -1):
            size = 1 << power
            # BC7 encodes blocks of 4x4, including the terminal 2x2/1x1 mips.
            # Edge-extend those terminal levels for the encoder only.
            padded = max(size, 4)
            raw = Path(temp) / f"{size}.rgba"
            subprocess.run(["convert", str(source), "-filter", "Lanczos",
                "-resize", f"{size}x{size}!", "-virtual-pixel", "edge",
                "-set", "option:distort:viewport", f"{padded}x{padded}+0+0",
                "-distort", "SRT", "0", "-depth", "8", "rgba:" + str(raw)], check=True)
            data = raw.read_bytes()
            if len(data) != padded * padded * 4:
                raise ValueError("Incorrect raw mip dimensions")
            blocks = bc.compress_blocks_bc7(bc.RGBASurface(data, padded, padded), settings)
            expected = max(1, (size + 3) // 4) ** 2 * 16
            if len(blocks) != expected:
                raise ValueError("Incorrect BC7 mip size")
            levels.append(blocks)
    # DDS + DDS_HEADER + DDS_HEADER_DXT10. Same BC7_UNORM/straight-alpha
    # format and 11 mip levels as the supplied source texture.
    header = (b"DDS " + struct.pack("<7I", 124, 0xA1007, 1024, 1024,
        1024 * 1024, 0, 11) + bytes(44)
        + struct.pack("<II4sIIIII", 32, 4, b"DX10", 0, 0, 0, 0, 0)
        + struct.pack("<5I", 0x401008, 0, 0, 0, 0)
        + struct.pack("<5I", 98, 3, 0, 1, 1))
    assert len(header) == 148
    output.write_bytes(header + b"".join(levels))
    print(f"{output}: {output.stat().st_size} bytes, BC7_UNORM, 11 mips")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    encode(args.source, args.output)
