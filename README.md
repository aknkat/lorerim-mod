# LoreRim 5：鋭敏な感覚 / Khajiit Keen Senses

**v0.1.0 試験版。ESP・PEXのファイル検査11件に合格。Skyrim / LoreRim / ENB上での動作は未検証です。**

カジートのプレイヤーが任意に使う Lesser Power を追加します。既存のナイトアイは変更しません。ゲームに付与する操作は手動で行うため、種族・NPC・Perkを上書きする必要がありません。

| 項目 | 実装 |
|---|---|
| 対象 | プレイヤーの KhajiitRace / KhajiitRaceVampire |
| 探知 | 生存中の周囲のActor。アンデッド・ドワーフ機械・死体・プレイヤー自身を除外 |
| 範囲 | ネイティブ探知の magnitude 26.25 feet、追加の距離条件 560 units（約8m） |
| 表示時間 | 2秒 |
| 再使用制限 | 60秒の制御効果。再適用禁止と発動条件で再発動・時間の更新を防ぐ設計 |
| 費用 | マジカ・スタミナとも0。スキル経験値も付与しない |
| 場所・時刻 | 屋内外・昼夜の条件なし |
| 敵味方 | 区別する条件なし。同じ LifeDetected シェーダーを使う |

## 必要なもの

- Skyrim SE 1.6.1170（対象バージョン。実機起動は未実施）
- `Skyrim.esm`。このMOD自身のマスター依存はこれだけです。
- MO2。LoreRim v5.0.4.8 Default / Requiem / Cabbage ENBを想定しています。

このMODのスクリプトはバニラPapyrusのみを呼びます。**追加のSKSE・DLL・Address Library・Requiemパッチは同梱せず、マスター依存としても要求しません。** LoreRim自体が要求するものは通常どおり有効にしてください。LoreRim/Requiemの実ファイルを照合できていないため、最終ロードオーダーでの相性は別途確認が必要です。

## MO2で導入する

1. 導入前のセーブを別名で残します。
2. `KhajiitKeenSenses-0.1.0-MO2.zip` をMO2の「アーカイブからMODをインストール」で導入します。ZIPのルートがData相当です。
3. 左側のMODと右側の `KhajiitKeenSenses.esp` を有効にします。これは **ESLフラグ付きESP** なので、通常のESP枠を1つ消費する構成ではありません。
4. 通常のLoreRimの管理手順で配置します。最初にMO2からSSEEditでこのESPを読み込み、「Check for Errors」を実施してください。生成パッチがある場合は、4つの新規レコードの最終値も確認します。[確認手順](docs/IN_GAME_CHECKLIST.md)に詳細があります。
5. カジートのセーブを起動し、コンソールで能力を付与します。

### 付与するFormID

付与するレコードは **`LKS_KeenSensesPower`、ローカルID `800`** です。

MO2右側の「Mod Index」が `FE:xxx` の場合、ゲーム内の完全なFormIDは **`FExxx800`** になります。`xxx` は実際の16進インデックスに置き換えてください。

```text
player.addspell FExxx800
```

例えばMod Indexが `FE:123` なら `player.addspell FE123800` です。これは例であり、自分のロードオーダーのIDを使います。

英語表示の場合は `help "Keen Senses" 4` でも検索できます。結果のうち `SPEL` の能力を選び、CooldownやInternal Detection Pulseは付与しません。日本語表示で入力が難しい場合はMO2のインデックスを使ってください。

魔法メニューの特殊能力から選択し、通常の特殊能力キーで使います。60秒制限中は探知が再発動しない設計です。「有効な効果」の **Keen Senses: Cooldown / 鋭敏な感覚：再使用待ち** が終了するまで待ちます。

## 能力の解除・MODの取り外し

同じFormIDで以下を実行すれば能力の付与を解除できます。

```text
player.removespell FExxx800
```

動作中の探知と再使用待ちが消えるまで、メニューを閉じた通常のゲームプレイで最大60秒待ち、別名で保存します。その後MO2で無効化できます。制御スクリプトにはクエスト・常駐更新・イベント登録・永続的なActorValue変更がありません。ただし、MODを外したセーブに何も残らないことを実機で保証したものではありません。元の状態へ確実に戻す場合は導入前のセーブを使います。

## ファイルと競合

```text
KhajiitKeenSenses.esp
Scripts/LKS_KeenSensesEffect.pex
Scripts/Source/LKS_KeenSensesEffect.psc
Strings/KhajiitKeenSenses_English.{STRINGS,DLSTRINGS,ILSTRINGS}
Strings/KhajiitKeenSenses_Japanese.{STRINGS,DLSTRINGS,ILSTRINGS}
docs/...
README.md
KhajiitKeenSenses-LICENSE.txt
build-manifest.json
SHA256SUMS.txt
```

4件すべてがこのESP自身の新規レコードです。既存のRACE、PERK、SPEL、MGEF、NPC、クエスト、ナイトアイを上書きしません。機械とアンデッドは標準の `ActorTypeDwarven` / `ActorTypeUndead` キーワードで除外します。追加MODのActorに適切なキーワードがない場合や、LifeDetectedシェーダーが別MODで変更されている場合の挙動は未確認です。

2026-10-16：梱包上のライセンス名を `KhajiitKeenSenses-LICENSE.txt` に変更しました。初版はルートの `LICENSE` がFSMPの同名文書と重複し、MO2に文書の競合が表示されました。ESP・PEX・Stringsの内容は同一です。修正前の版を導入済みの場合は、更新ZIPをMO2で既存MODへ **Replace（置き換え）** して、古い `LICENSE` を残さず入れ替えてください。

英語・日本語の表示はゲームの言語設定に従います。その他の言語のStringsは同梱していません。

## 検証状況と再ビルド

[検証記録](docs/VALIDATION.md)に、実行した検査と未実施の実機確認を分けて記載しています。[実機チェックリスト](docs/IN_GAME_CHECKLIST.md)には8m境界・除外対象・60秒制限・セーブ/ロード・競合の確認手順があります。

ESP生成プログラム、独立したバイナリ検査器、テスト、ビルド手順はリポジトリ内の `tools/`、`tests/`、`scripts/source/` にあります。[BUILD.md](docs/BUILD.md)を参照してください。

`KhajiitKeenSenses-0.1.0-source.zip` は制作ソース一式です。こちらは開発用で、MO2へインストールするアーカイブではありません。
