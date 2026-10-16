# LoreRim 5：鋭敏な感覚 / Khajiit Keen Senses

**v0.1.4：保存した期限を入力時に確認する方式へ変更。待機解除イベントへの依存を廃止しました。既存レコードの上書き0件。実機での修正結果は未確認です。**

[MO2導入用ZIP](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/dist/KhajiitKeenSenses-0.1.4-MO2.zip) / [制作ソースZIP](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/dist/KhajiitKeenSenses-0.1.4-source.zip)

カジートのプレイヤー向けに、半径約8mの生物を2秒間探知する特殊能力（Lesser Power）を追加します。再使用は60秒後、マジカ・スタミナ消費は0。既存のナイトアイ、種族、Perk、NPCは変更しません。

## v0.1.4：ロード後に待機が解除されない問題への変更

v0.1.1は待機中の再入力後に使えず、自己参照条件だけを外したv0.1.2では毎回発動すると報告されました。No Recastフラグだけで制限できるという前提は実環境で成立しませんでした。

v0.1.3では通常の60秒間隔の発動は確認できましたが、完全終了後でも、クールダウン中のセーブをロードすると1分以上待っても発動しないと報告されました。付け直しても即座や正確な60秒後ではなく、途中で復帰するとの補足があります。待機フラグを更新イベントだけで解除する構成には、そのイベントが復元・配送されなければ使用不能になる弱点がありました。装備が原因だったとも、イベントの欠落を実機ログで証明できたとも断定しません。

v0.1.4は、専用クエスト上の期限を、入力ごとにバニラAPI `Game.GetRealHoursPassed()` の標準プレイ時間と比較します。受理した発動だけが期限を約60秒先（1/60時間）に設定し、待機中の入力は期限を延ばしません。**新しい更新イベント登録、Wait、常駐監視、ロード時の装備変更は行いません。** 時計が大きく巻き戻り、残り時間が63秒を超える異常値になった場合だけ、その入力から60秒へ一度補正します。

専用クエスト自体は初回発動時に開始し、その後もRunningのまま残ります。NPC Alias・目標・自動起動や、既存クエストへの変更はありません。保存状態を追加する点は変わらず、スクリプト不要・セーブへの影響なしという意味ではありません。

コンパイル済みPEXを模擬APIで実行し、更新登録を一切復元しないロード、再入力、旧版の待機フラグ、遅れて届く旧イベント、時計の巻き戻りを検査します。**標準プレイ時計の保存・進行は模擬しており、Skyrim本体の保存・復元、メニュー中の時間計測と装備入力は実機未確認です。** 詳細は [v0.1.4の変更](docs/RELOAD_FIX_0.1.4.md) と [検証記録](docs/VALIDATION.md)。

## 保存・ロードとLoreRimの注意事項

ユーザー提供の [LoreRim Safe Savingの本文](https://v4.lorerim.com/home) は、**ロード前にゲームを終了・再起動すること**、戦闘・重いスクリプト演出中・セル移動直後の保存、短い間隔での連続保存を避けることを案内しています。リンクはv4サイトで、対象のv5現行ページと同じ文面かは未照合ですが、本MODの運用・検証にもこの注意を適用します。

本MODは短い発動関数を終了し、次の入力で期限を確認します。更新イベントの復元には依存しませんが、保存した期限と標準プレイ時計の整合性には依存します。低負荷や上書き0件は、セーブの安全性を保証する根拠にはなりません。

**v0.1.4も保存・ロード後の正常復帰は実機未確認です。** 確認は別名の検証用セーブを使い、保存後にゲームを終了・再起動してから読み込みます。進行中セッションから直接ロードしません。本文を理由に、能力使用後60秒間を一律に保存禁止にする制約は設けません。

## v0.1.1で修正したこと

v0.1.0とprobe1はユーザーの実機で探知が表示されませんでした。送付されたSSEEditのレコード情報から、標準探知は **Area** で範囲を指定している一方、自作版は **Area 0・No Area有効** だったことが分かりました。

修正版は標準のFire and Forget生命探知を参考に、Areaを27 feet、距離条件を560 units以下（約8m）、持続を2秒に変更しています。No Areaを解除し、FX Persistを有効、Actor ValueをNoneに修正しました。表示には同じ環境の標準能力で表示できた **LifeDetectedEnemy** を敵味方共通で使用します。想定される表示は赤色です。

自己除外条件は削除し、死体・アンデッド・ドワーフ機械の除外条件を維持します。標準のNoDetectLifeとIsUndeadも参照します。自己発光の有無、対象の除外と実効半径は修正版の実機確認待ちです。加えて、PEXの長さフィールドをCreation Kit形式に修正し、Mutagenの独立したPEXリーダーでも検査します。詳細は [レコード比較](docs/RECORD_COMPARISON_0.1.1.md)。

## 導入・更新

1. ゲームを終了し、`KhajiitKeenSenses-0.1.4-MO2.zip` をMO2の「アーカイブからMODをインストール」で導入します。
2. 旧版がある場合は **Replace（置き換え）**。同名ESPを提供する旧版・診断版を重ねず、1つだけ有効にします。置き換えにより旧版の共通名文書も取り除きます。
3. 左側のMODと、右側の `KhajiitKeenSenses.esp` を有効にします。ESLフラグ付きESPです。
4. 能力を追加済みなら再付与は不要。v0.1.3と同じESP名・5レコード・プロパティを維持します。旧版のフラグから残り時間は復元できないため、**更新後の初回は旧クールダウンをリセットし、その発動から新しい60秒を開始**します。付け外しで期限を変更する処理はありません。
5. 初回のみ、カジートのセーブでコンソールから能力を追加します。

送付されたロードオーダーではIndexは **FE:CFD** でした。このままなら、追加コマンドは次です。

```text
player.addspell FECFD800
```

Indexが変わった場合はMO2右側の現在値を使います。`FE:xxx` なら完全なFormIDは `FExxx800`。古い案内の `FE:CF5` を固定して使わないでください。

魔法メニューの特殊能力から「鋭敏な感覚」を選び、使用中の操作設定で発動します。ユーザーのコントローラー操作は **Y＋RT**。Y長押しだけは別操作として「no items to interact with」が出ると報告されています。操作設定は変更しません。再使用まで通常のゲーム画面で60秒待つ設計です。この環境では有効な効果に残り時間が表示されていないため、その画面を確認の前提にしません。

確認点は [実機確認手順](docs/IN_GAME_CHECKLIST.md) にまとめています。Y＋RT連打時の音と、Y長押し時の通知は別々の報告です。このMODには音・通知・採取・飲食の処理がなく、発生元は未特定です。音だけを根拠に他MODやキー設定の競合と断定していません。

## 仕様と依存

| 項目 | 設計 |
|---|---|
| 使用者 | プレイヤーのKhajiitRace / KhajiitRaceVampireのみ |
| 能力 | 任意発動のLesser Power |
| 範囲 | Area 27 feetの範囲をGetDistance PlayerRef <= 560 unitsで制限。約8m |
| 持続・再使用 | 探知2秒。入力効果は1秒。標準プレイ時計の期限差で約60秒を判定 |
| 費用 | マジカ・スタミナ0、スキル経験値0 |
| 除外 | 死体、ActorTypeUndead / IsUndead、ActorTypeDwarven、標準のNoDetectLife |
| 場所・時刻 | 屋内外・昼夜による条件なし |
| 敵味方 | 識別せず、共通の赤い探知シェーダーを参照 |

対象はSkyrim SE 1.6.1170 / LoreRim v5.0.4.8 Default / Requiem / Cabbage ENB。直接のマスターは **Skyrim.esmのみ**。バニラPapyrusだけを使い、追加のSKSE・DLL・Address Library・Requiemマスターは要求しません。LoreRim自体の依存は通常どおり有効にします。

## 競合を避ける構成

- 2 MGEF + 2 SPEL + 1 QUSTの5件すべてがこのESP固有の新規レコード。既存の種族・ナイトアイ・Perk・NPC・魔法・シェーダー・クエストの上書きは0件。
- Papyrusは固有名の `LKS_KeenSensesEffect` と `LKS_KeenSensesController` の2件。前者は入力、後者は専用クエストに属する状態管理です。既存スクリプトの置き換えはありません。
- 生命探知シェーダーと標準キーワードは参照のみ。今回は送付されたロードオーダーでの定義を照合済みです。
- README・ライセンス・検査記録は `KhajiitKeenSenses/` 以下にまとめ、他MODの共通名文書と重複するパスを避けます。
- ユーザー提供のFSMPアーカイブとのファイルパス重複も検査します。

```text
KhajiitKeenSenses.esp
Scripts/LKS_KeenSensesEffect.pex
Scripts/LKS_KeenSensesController.pex
Scripts/Source/LKS_KeenSensesEffect.psc
Scripts/Source/LKS_KeenSensesController.psc
Strings/KhajiitKeenSenses_English.{STRINGS,DLSTRINGS,ILSTRINGS}
Strings/KhajiitKeenSenses_Japanese.{STRINGS,DLSTRINGS,ILSTRINGS}
KhajiitKeenSenses/README.md
KhajiitKeenSenses/LICENSE.txt
KhajiitKeenSenses/build-manifest.json
KhajiitKeenSenses/SHA256SUMS.txt
KhajiitKeenSenses/docs/...
```

特別なActorや他MODの将来の変更まで含む互換性の保証ではありません。実効半径、探知対象、制限時間の厳密な境界とセーブ・ロードは [検証記録](docs/VALIDATION.md) の未確認項目として残しています。

## 解除

現在のIndexに合わせて能力を外します。送付されたIndexのままなら次です。

```text
player.removespell FECFD800
```

最後の発動から通常画面で60秒以上待ち、専用クエストを停止して別名で保存してからMODを無効化します。現在のIndexがFE:CFDなら停止コマンドは `stopquest FECFD804`。このコマンドは本MODの専用クエストだけを対象とします。確実に導入前へ戻す場合は導入前のセーブを使います。セーブからの完全な除去は制作環境では検証できていません。

## 制作ソース

`KhajiitKeenSenses-0.1.4-source.zip` はESP生成コード、PSC、検査器、テスト、文書を含む開発用ZIPで、MO2へ導入するZIPではありません。[ビルド方法](docs/BUILD.md)と [参照元](docs/SOURCES.md) を同梱しています。ゲーム本体、Requiem/LoreRimのプラグイン、第三者ツールのバイナリは同梱しません。
