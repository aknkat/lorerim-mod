# Estee Emerald Eyes 1.0.0 の制作・検査

このソースZIPだけでESPとMO2用ZIPを再生成できます。完成DDSと圧縮前PNGを同梱しています。元MODのBSA・ESP、ユーザーのプリセットは同梱しません。

## 標準の再ビルド

Python 3の標準ライブラリだけを使用します。解凍したルートで実行します。

```bash
python3 tools/build_emerald_eyes.py
python3 tools/verify_emerald_eyes.py dist/EsteeEmeraldEyes-1.0.0-MO2.zip
```

生成先は `build/emerald-eyes-1.0.0/` と `dist/`。同じ版のZIPがあり内容が異なる場合は上書きを拒否します。配布後の内容変更は新しい版として行います。

## DDSをPNGから再圧縮する場合だけ必要なもの

- ImageMagick 7（制作時7.1.1-43）
- `ispc_texcomp==1.0.1`（BC7エンコーダー。ゲームへの導入不要）

```bash
python3 -m pip install --target /tmp/emerald-encoder ispc_texcomp==1.0.1
PYTHONPATH=/tmp/emerald-encoder python3 tools/encode_emerald_dds.py assets/estee-emerald/estee_emerald_2edb91.png assets/estee-emerald/estee_emerald_2edb91.dds
```

RGBA対応のalpha_slowプロファイル、BC7_UNORM=98、straight alpha、11ミップを使用。ミップはImageMagickのLanczosで縮小し、最後の2×2と1×1はBC7の4×4ブロックへ端の画素を延長して圧縮します。圧縮前画像のアルファは元画像と同じですが、再圧縮による数値差は生じます。

圧縮前PNGは、元の `KH_9 Low Light.dds` の配置・HSL明度・アルファを維持して基準色の色相・彩度に合わせたものです。画像生成による色調整の参考画像を確認した後、元の瞳孔や模様を描き直さない色変換へ確定しました。元ファイルはユーザー提供MODのBSAから読み出しました。原画像自体はこのZIPに含めません。

再調整が必要な場合のImageMagick手順（`original-eye.png` は元DDSをPNGへデコードした画像）：

```bash
convert original-eye.png -colorspace HSL -channel R -evaluate set 42.8709055877% -channel G -evaluate set 70.6122448979% +channel -colorspace sRGB PNG32:assets/estee-emerald/estee_emerald_2edb91.png
```

元DDSのSHA256と元HDPT/TXSTの基準値は `tools/data/kala_estee_eye_baseline.json` にあります。

## 追加の独立した読み戻し

全11ミップをPillowで独立してデコードし、最上位ミップを圧縮前PNGと比較します（Pillowは検査用のみ）。

```bash
python3 tools/verify_emerald_eyes.py build/emerald-eyes-1.0.0 --decode-dds
```

別作者のESPパーサーでも読み戻し、4レコード（ヘッダーを含む）のバイト一致を確認します。

```bash
npm install --prefix /tmp/emerald-reader @fcrick/tes-data@0.0.1
node tools/verify_emerald_third_party.cjs /tmp/emerald-reader/node_modules/@fcrick/tes-data build/emerald-eyes-1.0.0/EsteeEmeraldEyes.esp
```

HDPTで元から変えるのはEDID・FULL・TNAM・RNAM、TXSTではEDID・TX00のみ。共有のモデル・モーフ・法線・反射・フラグは元のままです。専用FLSTはSkyrimの通常カジート13745と吸血鬼カジート88845だけを参照します。必須マスターはSkyrim.esmだけです。

これらは形式・参照・圧縮の検査です。ゲームの描画・RaceMenuの列挙・外見のセーブ復元・変身処理を実行したものではありません。実機未検証の範囲は `docs/EMERALD_EYES.md` を参照してください。
