# LoreRim 5：鋭敏な感覚 / Khajiit Keen Senses

**v0.1.3：専用コントローラーで60秒制限を管理します。既存レコードの上書き0件。ファイル・コンパイル済み制御の19検査に合格し、ユーザーから60秒ごとに再発動できたとの実機報告を受けています。セーブ・ロード後の復帰は未確認です。**

[MO2導入用ZIP](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/dist/KhajiitKeenSenses-0.1.3-MO2.zip) / [制作ソースZIP](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/dist/KhajiitKeenSenses-0.1.3-source.zip)

カジートのプレイヤー向けに、半径約8mの生物を2秒間探知する特殊能力（Lesser Power）を追加します。再使用は60秒後、マジカ・スタミナ消費は0。既存のナイトアイ、種族、Perk、NPCは変更しません。

## v0.1.3：再入力で更新されない共有クールダウン

v0.1.1は待機中の再入力後に使えず、自己参照条件だけを外したv0.1.2では毎回発動すると報告されました。No Recastフラグだけで制限できるという前提は実環境で成立しませんでした。

v0.1.3は、**入力を受ける短い効果と、60秒の状態を保持する専用クエストを分離**します。専用クエストのスクリプトが待機フラグを先に確保し、受理した1回だけ `RegisterForSingleUpdate(60)` と探知を実行します。待機中の再入力は両方を行わず終了します。期限の更新や入力効果の寿命に依存しません。

専用クエストは自作ESPの新規レコード1件で、初回の有効な発動時に開始します。起動後は残りますが、待機中以外に定期処理を登録しません。自動起動・NPCのAlias・クエスト目標・既存クエストへの変更はありません。追加のSKSE依存もありません。

コンパイル済みPEXを検査用ホストで実行し、0/30/65秒、200回の再入力、Native呼び出し途中の再入、保存したフラグと更新登録の復元を検査しました。**タイマー登録とその保存復元は模擬したもので、Skyrim本体でのイベント配送・保存ロードを確認した意味ではありません。** 詳細は [v0.1.3の構成](docs/COOLDOWN_CONTROLLER_0.1.3.md) と [検証記録](docs/VALIDATION.md)。

その後、ユーザーから「60秒ごとに発動するようになった」と報告されました。初回はお気に入りでのつけ外しが必要だったかもしれないとの報告もありますが、原因・再現性は未確認です。正確な境界時刻、長時間運用、保存・ロードの確認とは区別します。

## 保存・ロードとLoreRimの注意事項

ユーザー提供の [LoreRim Safe Savingの本文](https://v4.lorerim.com/home) は、**ロード前にゲームを終了・再起動すること**、戦闘・重いスクリプト演出中・セル移動直後の保存、短い間隔での連続保存を避けることを案内しています。リンクはv4サイトで、対象のv5現行ページと同じ文面かは未照合ですが、本MODの運用・検証にもこの注意を適用します。

この本文は、すべてのPapyrusスクリプトやタイマーの存在中に保存を禁止するものではありません。本MODは発動関数を終了した後、60秒後の単発イベントを待ちます。`Utility.Wait(60)` で処理途中のスタックを保持する構成ではありません。ただし、この違いだけでLoreRim上の保存・復元の安全性を保証することはできません。

**保存・ロード後に待機フラグと予約イベントが整合して復元されるかは未検証です。** 予約イベントが復元されなければ、待機フラグが解除されず再使用できなくなる可能性があります。確認する際は別名の検証用セーブを使い、保存後にゲームを終了・再起動してから読み込みます。進行中セッションからの直接ロードは案内しません。本文から「本能力の60秒待機中は保存禁止」という制約を追加することもしません。

## v0.1.1で修正したこと

v0.1.0とprobe1はユーザーの実機で探知が表示されませんでした。送付されたSSEEditのレコード情報から、標準探知は **Area** で範囲を指定している一方、自作版は **Area 0・No Area有効** だったことが分かりました。

修正版は標準のFire and Forget生命探知を参考に、Areaを27 feet、距離条件を560 units以下（約8m）、持続を2秒に変更しています。No Areaを解除し、FX Persistを有効、Actor ValueをNoneに修正しました。表示には同じ環境の標準能力で表示できた **LifeDetectedEnemy** を敵味方共通で使用します。想定される表示は赤色です。

自己除外条件は削除し、死体・アンデッド・ドワーフ機械の除外条件を維持します。標準のNoDetectLifeとIsUndeadも参照します。自己発光の有無、対象の除外と実効半径は修正版の実機確認待ちです。加えて、PEXの長さフィールドをCreation Kit形式に修正し、Mutagenの独立したPEXリーダーでも検査します。詳細は [レコード比較](docs/RECORD_COMPARISON_0.1.1.md)。

## 導入・更新

1. ゲームを終了し、`KhajiitKeenSenses-0.1.3-MO2.zip` をMO2の「アーカイブからMODをインストール」で導入します。
2. 旧版がある場合は **Replace（置き換え）**。同名ESPを提供する旧版・診断版を重ねず、1つだけ有効にします。置き換えにより旧版の共通名文書も取り除きます。
3. 左側のMODと、右側の `KhajiitKeenSenses.esp` を有効にします。ESLフラグ付きESPです。
4. 能力を追加済みのセーブでは、同じ能力をそのまま使います。ESP名と既存4件のローカルFormIDは維持し、専用QUSTをローカル804へ追加しています。旧プロパティ3件も互換性のため保持しています。
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
| 持続・再使用 | 探知2秒。入力効果は1秒、独立コントローラーが60秒待機を管理 |
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

`KhajiitKeenSenses-0.1.3-source.zip` はESP生成コード、PSC、検査器、テスト、文書を含む開発用ZIPで、MO2へ導入するZIPではありません。[ビルド方法](docs/BUILD.md)と [参照元](docs/SOURCES.md) を同梱しています。ゲーム本体、Requiem/LoreRimのプラグイン、第三者ツールのバイナリは同梱しません。
