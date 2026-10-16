# v0.1.1の修正根拠

ユーザー提供 `LKS-detection-records.txt`（3494ファイルを読み込んだSSEEditからの一括出力）を比較した。添付文書はレコードのデータとして読み、作業指示としては扱っていない。全文や第三者のプラグイン本体は配布ZIPに含めず、必要な値だけを記録する。

## 実際に表示された標準能力

`VoiceAuraWhisper1 [SPEL:0008AFCC]` はゲーム内で赤く、8mよりかなり遠くまで表示された。提供されたロードオーダーでのSPELの最終定義は `Big Tweaks.esp`。参照するMGEFの最終定義は `Requiem.esp`。

- 外用・内用の効果はいずれもMagnitude 0、Area 500、Duration 30。
- MGEFはScript archetype、Actor Value None、FX Persist有効、No Area無効、Hit ShaderはLifeDetectedEnemy `[EFSH:000DC209]`。
- 屋内外の条件がある。アンデッド・機械なども含む標準能力なので、このSPELをそのまま流用するだけでは要求を満たさない。

## 標準の生命探知

標準のFire and Forget用MGEF `001019D8`～`001019DB` と、通常のDetect Lifeが使うMGEFも取得できた。FFの4件は送付データではSkyrim.esmの定義が最終値だった。

| 項目 | 標準のFF生命探知 | v0.1.0 / probe1 | v0.1.1 |
|---|---|---|---|
| 範囲 | EFITのAreaを使う構成 | Magnitude 26.25、Area 0 | Magnitude 0、Area 27 |
| No Area | 無効 | 有効 | 無効 |
| FX Persist | 有効 | 無効 | 有効 |
| Actor Value | None | Detect Life Range | None |
| Hit Shader | 友軍146 / 敵DC209 | 146 | 敵味方共通DC209 |
| 持続 | Fire and Forget | 2秒 | 2秒 |
| 視線 | 標準SPELはArea Effect Ignores LOS有効 | 無効 | 有効 |

元の自己除外条件だけを外すprobe1では範囲0が残った。元のテストは値を期待どおり書き出したことを確認するもので、期待値そのものの誤りを検出できていなかった。

27 feetは約576 unitsを覆う範囲であり、その中を `GetDistance PlayerRef <= 560` で約8mに制限する。近い生物にも届かないNo Area/Area 0を取り除くことが主要な修正である。実効範囲と移動中の判定はゲーム内での最終確認を要する。

MGEFの除外条件はGetDead、ActorTypeUndead、ActorTypeDwarven、IsUndead、NoDetectLife。標準レコードの屋内外条件・敵味方条件・Daedraの除外は採用しない。スキル・Perkの倍率で範囲や時間を増やすフラグも採用しない。既存レコードの上書きは一切行わず、必要な値を固有レコードへ設定する。

## シェーダーと現在のIndex

`LifeDetected [EFSH:00000146]` は送付データでは `LoreRim - Armor Merges.esp` が最終定義。赤く表示できた `LifeDetectedEnemy [EFSH:000DC209]` はSkyrim.esmの定義が最終値だった。v0.1.1は後者を参照し、シェーダー本体やテクスチャを同梱・上書きしない。

自作ESPのIndexは **FE:CFD**。制御・探知・主能力・内部魔法の4件はすべて自作ESPのレコードとして解決され、VMADも内部魔法・2種のKhajiitRaceを正しく参照していた。過去のFE:CF5のコマンドを固定して使わない。

## PEX検査器の訂正

別件として、従来の独立PEXリーダーがオブジェクト長を本文だけの長さと解釈していた。実際の形式は長さフィールド自身の4バイトを含む。

Mutagenの `PexObject.Create/Write` とユーザー提供FSMP内のCK形式PEXの長さ規則を照合した。新しい補正はCapricaのlittle-endian本文長494を、big-endianで498（`000001f2`）へ直す。古い版の `000001ee` は不正として新しい検査器が拒否する。命令本体とPSCは変更しない。

v0.1.1はPythonリーダーに加え、Mutagenの独立したPEXリーダーでもファイル全体を読み込む。Champollionによるデコンパイルも行う。この修正がゲーム内の不発に寄与したかは不明だが、配布するスクリプトの構造は訂正する。
