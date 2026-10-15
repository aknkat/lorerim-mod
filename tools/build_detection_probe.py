#!/usr/bin/env python3
"""Build probe1 by removing exactly one known CTDA from the published ESP.

Keep the production source, runtime script and FormIDs unchanged. This is a
differential diagnostic, not a claim that native Detect Life filtering works.
"""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import zipfile

from build import archive, source_archive
from formats import conditions, read_plugin
from verify_archive import verify

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "dist/KhajiitKeenSenses-0.1.0-MO2.zip"
BASE_SHA256 = "324e7fd2fa58f549241a74020bca8aa328ef3cac4888f48b5ec6013adf3cb396"
OUTPUT = ROOT / "dist/KhajiitKeenSenses-0.1.0-probe1-MO2.zip"
PACKAGE = ROOT / "build/detection-probe1"
TARGET = 0x01000802
NOTICE = """# probe1：自己除外条件の切り分け専用

通常版0.1.0で探知されず、コンソールに GetIsRef >> 1.00 と表示された
問題の診断用です。探知MGEFの GetIsReference PlayerRef == 0 の条件を
1件だけ外しています。探知が直ると確認された完成版ではありません。

MO2では元のMODを Replace（置き換え）して、同名ESPを1つだけ有効にします。
ESP名、4件のFormID、PEX、PSC、Stringsは元の版と同じです。
Indexが FE:CF5 のままなら、生きたNPCのすぐ近くで次を実行します。

    player.cast FECF5803 00000014 left

コンソールを閉じ、約2秒光るか確認してください。まず内部探知を直接試し、
表示できた場合は通常の能力を60秒制限終了後に試してください。
Indexが変わった場合は FECF5 の部分を現在のIndexに合わせます。

変更していないもの：既存レコード、自己除外以外の4条件、範囲の値、
2秒の持続、60秒の制御効果、種族・プレイヤー制限、コンパイル済みスクリプト。

未確認：実機での修正結果、探知対象のフィルター評価、半径8m、ENB描画、
吸血鬼カジート、通常能力からのスクリプト呼び出し、セーブ・ロード。
このZIPを入れただけで、元の仕様すべてが満たされたとは判断できません。
元の版は通常のカジートで再使用待ちMGEFが有効になることのみユーザー確認済みです。

以下は元の0.1.0の説明です。検証状態は上記を優先してください。

---

"""


def remove_player_condition(data):
    """Preserve all bytes except the selected subrecord and enclosing lengths."""
    removed = []

    def walk(block):
        output = bytearray()
        position = 0
        while position < len(block):
            if position + 24 > len(block):
                raise ValueError("Truncated record header")
            header = bytearray(block[position:position + 24])
            tag = bytes(header[:4])
            size = struct.unpack_from("<I", header, 4)[0]
            end = position + size if tag == b"GRUP" else position + 24 + size
            if end > len(block):
                raise ValueError("Record exceeds parent")
            body = block[position + 24:end]
            if tag == b"GRUP":
                body = walk(body)
                struct.pack_into("<I", header, 4, len(body) + 24)
            elif tag == b"MGEF" and struct.unpack_from("<I", header, 12)[0] == TARGET:
                needle = b"CTDA" + struct.pack("<H", 32) + struct.pack(
                    "<B3xfH2xIIIIi", 0, 0, 136, 0x14, 0, 0, 0, -1)
                if body.count(needle) != 1:
                    raise ValueError("Expected exact Subject/PlayerRef == 0 condition")
                removed.append(needle[6:])
                body = body.replace(needle, b"", 1)
                struct.pack_into("<I", header, 4, len(body))
            output.extend(header)
            output.extend(body)
            position = end
        return bytes(output)

    result = walk(data)
    if len(removed) != 1 or len(data) - len(result) != 38:
        raise ValueError("Expected exactly one 38-byte subrecord removal")
    return result, removed[0]


def main():
    if hashlib.sha256(BASE.read_bytes()).hexdigest() != BASE_SHA256:
        raise ValueError("Unexpected production archive; inspect before building a probe")
    verify(BASE)
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    PACKAGE.mkdir(parents=True)
    with zipfile.ZipFile(BASE) as source:
        source.extractall(PACKAGE)
    esp = PACKAGE / "KhajiitKeenSenses.esp"
    before_records, before_groups = read_plugin(esp)
    old_esp = esp.read_bytes()
    patched, removed = remove_player_condition(old_esp)
    esp.write_bytes(patched)
    after_records, after_groups = read_plugin(esp)
    expected = []
    for record in before_records:
        if record["id"] == TARGET:
            record = dict(record, fields=[entry for entry in record["fields"]
                                         if entry != ("CTDA", removed)])
        expected.append(record)
    if after_records != expected or before_groups != after_groups:
        raise ValueError("Probe changed a record beyond the single intended condition")
    detect = next(record for record in after_records if record["id"] == TARGET)
    filters = conditions(detect)
    if [(c["function"], c["p1"]) for c in filters] != [
            (46, 0), (560, 0x13796), (560, 0x1397A), (1, 0x14)]:
        raise ValueError("Unexpected remaining detection conditions")
    if any(record["id"] >> 24 != 1 for record in after_records[1:]):
        raise ValueError("Existing-record override in probe")
    # Readback alone does not prove engine behavior; also compare every installed
    # script/localization byte to the actual published ZIP.
    with zipfile.ZipFile(BASE) as source:
        native = [name for name in source.namelist()
                  if name.startswith(("Scripts/", "Strings/"))]
        for name in native:
            if (PACKAGE / name).read_bytes() != source.read(name):
                raise ValueError(f"Unexpected runtime change: {name}")
    readme = PACKAGE / "README.md"
    readme.write_text(NOTICE + (ROOT / "README.md").read_text(encoding="utf-8"), encoding="utf-8")
    for name in ("DETECTION_PROBE.md", "VALIDATION.md"):
        shutil.copy2(ROOT / "docs" / name, PACKAGE / "docs" / name)
    manifest_path = PACKAGE / "build-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(version="0.1.0-probe1", status="diagnostic_game_result_pending",
                    diagnostic_change="Remove only MGEF 000802 GetIsReference PlayerRef == 0",
                    base_archive_sha256=BASE_SHA256)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    archive(PACKAGE, OUTPUT)
    verify(OUTPUT)
    first = OUTPUT.read_bytes()
    archive(PACKAGE, OUTPUT)
    if OUTPUT.read_bytes() != first:
        raise ValueError("Non-reproducible probe archive")
    print(f"Probe delta verified: 1 CTDA removed, {len(native)} script/string files unchanged, "
          "all 4 FormIDs preserved, 0 existing-record overrides; repeat ZIP bytes match.")
    source_archive(ROOT / "dist/KhajiitKeenSenses-0.1.0-probe1-source.zip")


if __name__ == "__main__":
    main()
