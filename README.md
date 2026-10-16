# LoreRim 5：鋭敏な感覚 / Khajiit Keen Senses

**v0.1.1 修正版。既存レコードの上書き0件。近距離の赤い表示と、待ち時間を置いた再使用のユーザー報告あり。範囲・対象除外・待機中の挙動などは確認中です。**

[MO2導入用ZIP](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/dist/KhajiitKeenSenses-0.1.1-MO2.zip) / [制作ソースZIP](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/dist/KhajiitKeenSenses-0.1.1-source.zip)

カジートのプレイヤー向けに、半径約8mの生物を2秒間探知する特殊能力（Lesser Power）を追加します。再使用は60秒後、マジカ・スタミナ消費は0。既存のナイトアイ、種族、Perk、NPCは変更しません。

## v0.1.1で修正したこと

v0.1.0とprobe1はユーザーの実機で探知が表示されませんでした。送付されたSSEEditのレコード情報から、標準探知は **Area** で範囲を指定している一方、自作版は **Area 0・No Area有効** だったことが分かりました。

修正版は標準のFire and Forget生命探知を参考に、Areaを27 feet、距離条件を560 units以下（約8m）、持続を2秒に変更しています。No Areaを解除し、FX Persistを有効、Actor ValueをNoneに修正しました。表示には同じ環境の標準能力で表示できた **LifeDetectedEnemy** を敵味方共通で使用します。想定される表示は赤色です。

自己除外条件は削除し、死体・アンデッド・ドワーフ機械の除外条件を維持します。標準のNoDetectLifeとIsUndeadも参照します。自己発光の有無、対象の除外と実効半径は修正版の実機確認待ちです。加えて、PEXの長さフィールドをCreation Kit形式に修正し、Mutagenの独立したPEXリーダーでも検査します。詳細は [レコード比較](docs/RECORD_COMPARISON_0.1.1.md)。

## 導入・更新

1. ゲームを終了し、`KhajiitKeenSenses-0.1.1-MO2.zip` をMO2の「アーカイブからMODをインストール」で導入します。
2. 旧版がある場合は **Replace（置き換え）**。同名ESPを提供する旧版・診断版を重ねず、1つだけ有効にします。置き換えにより旧版の共通名文書も取り除きます。
3. 左側のMODと、右側の `KhajiitKeenSenses.esp` を有効にします。ESLフラグ付きESPです。
4. 能力を追加済みのセーブでは、同じ能力をそのまま使います。ESP名・4件のローカルFormID・Papyrusプロパティ名は維持しています。
5. 初回のみ、カジートのセーブでコンソールから能力を追加します。

送付されたロードオーダーではIndexは **FE:CFD** でした。このままなら、追加コマンドは次です。

```text
player.addspell FECFD800
```

Indexが変わった場合はMO2右側の現在値を使います。`FE:xxx` なら完全なFormIDは `FExxx800`。古い案内の `FE:CF5` を固定して使わないでください。

魔法メニューの特殊能力から「鋭敏な感覚」を選び、通常の特殊能力キーで発動します。生きたNPCの近くで使い、約2秒の表示と60秒の再使用制限をまとめて確認してください。クールダウンは「有効な効果」の **鋭敏な感覚：再使用待ち / Keen Senses: Cooldown** です。表示が消えるまで再発動を防ぐ設計です。

確認する点は [実機確認手順](docs/IN_GAME_CHECKLIST.md) にまとめています。近距離のNPCが赤く表示され、60秒待つと再使用できたとの報告があります。一方、待ち時間中にキーを押すと採取・飲食のような音と「no items to interact with」が出て、待ち時間が延長されるように感じるという報告もあります。通知の発生元と、残り時間が本当に60秒へ戻るかは未確認です。このMODのスクリプトにはその通知や音を出す処理はなく、ゲーム側の発動失敗処理や他の機能のどれが原因かは特定していません。

## 仕様と依存

| 項目 | 設計 |
|---|---|
| 使用者 | プレイヤーのKhajiitRace / KhajiitRaceVampireのみ |
| 能力 | 任意発動のLesser Power |
| 範囲 | Area 27 feetの範囲をGetDistance PlayerRef <= 560 unitsで制限。約8m |
| 持続・再使用 | 探知2秒、制御効果60秒 |
| 費用 | マジカ・スタミナ0、スキル経験値0 |
| 除外 | 死体、ActorTypeUndead / IsUndead、ActorTypeDwarven、標準のNoDetectLife |
| 場所・時刻 | 屋内外・昼夜による条件なし |
| 敵味方 | 識別せず、共通の赤い探知シェーダーを参照 |

対象はSkyrim SE 1.6.1170 / LoreRim v5.0.4.8 Default / Requiem / Cabbage ENB。直接のマスターは **Skyrim.esmのみ**。バニラPapyrusだけを使い、追加のSKSE・DLL・Address Library・Requiemマスターは要求しません。LoreRim自体の依存は通常どおり有効にします。

## 競合を避ける構成

- 2 MGEF + 2 SPELの4件すべてがこのESP固有の新規レコード。既存の種族・ナイトアイ・Perk・NPC・魔法・シェーダーの上書きは0件。
- Papyrusは固有名の `LKS_KeenSensesEffect` 1件。既存スクリプトの置き換えや常駐クエストはありません。
- 生命探知シェーダーと標準キーワードは参照のみ。今回は送付されたロードオーダーでの定義を照合済みです。
- README・ライセンス・検査記録は `KhajiitKeenSenses/` 以下にまとめ、他MODの共通名文書と重複するパスを避けます。
- ユーザー提供のFSMPアーカイブとのファイルパス重複も検査します。

```text
KhajiitKeenSenses.esp
Scripts/LKS_KeenSensesEffect.pex
Scripts/Source/LKS_KeenSensesEffect.psc
Strings/KhajiitKeenSenses_English.{STRINGS,DLSTRINGS,ILSTRINGS}
Strings/KhajiitKeenSenses_Japanese.{STRINGS,DLSTRINGS,ILSTRINGS}
KhajiitKeenSenses/README.md
KhajiitKeenSenses/LICENSE.txt
KhajiitKeenSenses/build-manifest.json
KhajiitKeenSenses/SHA256SUMS.txt
KhajiitKeenSenses/docs/...
```

特別なActorや他MODの将来の変更まで含む互換性の保証ではありません。実効半径、探知対象、60秒制限とセーブ・ロードは [検証記録](docs/VALIDATION.md) の未確認項目として残しています。

## 解除

現在のIndexに合わせて能力を外します。送付されたIndexのままなら次です。

```text
player.removespell FECFD800
```

探知と再使用待ちの終了後、別名で保存してからMODを無効化します。確実に導入前へ戻す場合は導入前のセーブを使います。セーブからの完全な除去は制作環境では検証できていません。

## 制作ソース

`KhajiitKeenSenses-0.1.1-source.zip` はESP生成コード、PSC、検査器、テスト、文書を含む開発用ZIPで、MO2へ導入するZIPではありません。[ビルド方法](docs/BUILD.md)と [参照元](docs/SOURCES.md) を同梱しています。ゲーム本体、Requiem/LoreRimのプラグイン、第三者ツールのバイナリは同梱しません。
