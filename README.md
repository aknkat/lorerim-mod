# LoreRim 5：鋭敏な感覚 / Khajiit Keen Senses

**新しい制作物：鋭敏な感覚（集中）0.2.7。色を#E91E63へ差し替え、屋内常時・屋外19:00以上～翌6:00未満、半径約5m・基礎50マジカ／秒、デイドラ除外の版です。** 探知色#E91E63・手元の光なし・使用によるスキル経験値なしは維持します。新規SPEL・MGEF・専用EFSHの3件で構成し、既存レコードの上書き、独自スクリプト、クエスト、DLL、追加SKSEプラグインはありません。条件・配布構造の検査とゲーム内動作確認は区別します。実機未検証です。

[集中呪文版のMO2導入ZIP](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/dist/KhajiitKeenSensesConcentration-0.2.7-MO2.zip) / [制作ソースZIP](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/dist/KhajiitKeenSensesConcentration-0.2.7-source.zip) / [導入・解除・検証状況のREADME](docs/CONCENTRATION.md) / [ビルド方法](docs/CONCENTRATION_BUILD.md)

新ESPは **`KhajiitKeenSensesConcentration.esp`**。旧特殊能力版と別MODとして導入し、「鋭敏な感覚（集中）」を手に装備して通常の魔法として使用します。独自の60秒制限はありません。変性に分類し、経験値倍率0・半減Perk未設定ですが、他の方法で育てた変性や一般の消費補正の影響は受け得ます。50／秒は補正前の値です。屋外の6:00～18:59台は探知が無効でも詠唱・消費が続く可能性があります。時刻はゲーム内時計の固定判定で、照度やENBとは連動しません。

集中版0.2.0～0.2.4からは、ゲームを完全終了してMO2でReplace（置き換え）します。同じESP名と呪文IDを維持し、魔法の取得し直しは不要です。0.2.4からは専用シェーダーのRGBのみ変更し、腕の装備・詠唱動作は維持します。指定色は入力RGBであり、ENB・背景・透明度・加算合成で実際の見え方は変わります。0.2.1で報告されたロード後の装備解除の原因は未特定で、この版で修正した扱いにはしていません。既存の配布ZIPは変更していません。

旧版のセーブ情報の移行・削除は行いません。旧版を使っている場合の扱いと、新ESPの現在のIndexから `player.addspell` する方法は上記READMEに記載しています。過去のIndexを新ESPへ転用しません。

[LoreRim全体を踏まえた強度再評価・調整案](docs/CONCENTRATION_BALANCE_REVIEW.md)：非魔法特化でも日中の壁越し索敵・短時間使用・隠密との相乗効果を考慮し、以前の「ナイトアイと同程度〜やや控えめ」という評価を撤回。0.2.4では約5m・基礎50マジカ／秒・デイドラ除外に加え、ユーザー指定の屋外19:00～翌6:00未満／屋内常時を採用しました。ナイトアイとの等価を実証したという意味ではありません。

## 旧特殊能力版0.1.xの経緯・配布物

以下は旧方式の履歴です。集中呪文版の導入には使いません。旧ZIPは変更せず保管しています。

**v0.1.4でもロード後に発動しないとの実機報告があり、保存・ロードの問題は未解決です。** 保存した期限を入力時に確認する方式へ変更しましたが、これだけでは解消を確認できていません。既存レコードの上書きは0件です。

[MO2導入用ZIP](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/dist/KhajiitKeenSenses-0.1.4-MO2.zip) / [制作ソースZIP](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/dist/KhajiitKeenSenses-0.1.4-source.zip)

**現在の診断：** 診断4は通知関数へ余分な引数を渡していたため撤回します。[診断用追加MOD diagnostic5](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/dist/KhajiitKeenSenses-0.1.4-diagnostic5-MO2.zip) で修正し、公開されたSkyrimのAPI宣言と実際のPEXの引数を照合します。コマンド入力不要で、通常のY＋RTから通知で起動・受理を表示します。本体のロード後の不発は未解決です。[診断手順](docs/RELOAD_DIAGNOSTIC.md) と [診断用ソースZIP](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/dist/KhajiitKeenSenses-0.1.4-diagnostic5-source.zip)。

diagnostic3では、数値画面まで到達し、保存期限は満了、`TryActivate accepted: TRUE` を実機画像で確認できました。発光は見逃しており未確認です。診断4に見つかったAPIの誤りは、こちらの制作・検査の不備です。**診断5ではINPUTとACCEPTEDが出ても光らず、その状態で内部探知803を直接Castすると光ったと確認できました。** 現在のIndexは **FE:CF5**、SQVで表示されたDetectionSpellも正しい **FECF5803** でした。参照違いを原因とは扱いません。他MODの実行時処理を含む呼び出し経路の差を調べるため、試験版の追加を保留し、実際の有効MODと設定を照合します。診断MODが無効だった試行は診断5の結果には含めません。

**使用中プロファイルの照合結果：** 提供されたMO2の3一覧では、有効プラグイン3413件の順序は一致し、診断5が本体より優先され、LKSのESPは最後でした。後続ESPによる上書きや診断版の優先順位違いを示す証拠はありません。関連する入力・魔法処理のMODも有効ですが、特定MODが不発の原因とは確定していません。新しい試験版やゲーム内テストは追加していません。[調査の根拠と限界](docs/RUNTIME_INTERACTION_AUDIT.md)。

添付されたPapyrusTweaks.dllのPE版情報は4.1.1.0。ユーザーが `mods/LoreRim - MCM and INI Settings/SKSE/Plugins/PapyrusTweaks.ini` で見つけた設定では、**Native高速化はfalse、Castも除外リストに含まれていました。** この設定を読む場合、調べた高速化フックは導入されないため、この機能を不発の原因とは扱いません。DLLTweaks.iniは別MODの設定です。設定変更や追加テストを求める根拠は得られておらず、不発の原因と修正方針は未確定です。

直接競合だけでなくゲーム内の挙動の評価も必要との指摘を受け、[挙動からの調査順位](docs/RUNTIME_INTERACTION_AUDIT.md#挙動の重なりから付ける調査の優先順位)を整理しました。音・通知については入力と別行動の重複、詠唱についてはDynamic Animation CastingやSTB Quick Hotkey Castの動作条件を資料から調べる候補です。主能力のコンソールCastも不発なので、キーの取り合いだけでは全症状を説明できません。本MOD自身の発動経路も引き続き対象で、特定MODが原因とは確定していません。

**別方式の設計検証：** [直接探知＋専用SKSE DLLの候補](docs/DIRECT_DESIGN_FEASIBILITY.md)を整理しました。探知は能力自身へ直接持たせ、60秒の残時間を独立して保存する案です。待機ロジックの単独C++コアは5群・20万操作の検査を通過しましたが、Skyrimの発動前処理・時間入力・保存コールバックとの接続は未実装です。新方式のESP・DLL・導入ZIPはまだなく、実機合格や従来版より安全との判定ではありません。既存ZIPは変更していません。

カジートのプレイヤー向けに、半径約8mの生物を2秒間探知する特殊能力（Lesser Power）を追加します。再使用は60秒後、マジカ・スタミナ消費は0。既存のナイトアイ、種族、Perk、NPCは変更しません。

## v0.1.4：ロード後に待機が解除されない問題への変更

v0.1.1は待機中の再入力後に使えず、自己参照条件だけを外したv0.1.2では毎回発動すると報告されました。No Recastフラグだけで制限できるという前提は実環境で成立しませんでした。

v0.1.3では通常の60秒間隔の発動は確認できましたが、完全終了後でも、クールダウン中のセーブをロードすると1分以上待っても発動しないと報告されました。付け直しても即座や正確な60秒後ではなく、途中で復帰するとの補足があります。待機フラグを更新イベントだけで解除する構成には、そのイベントが復元・配送されなければ使用不能になる弱点がありました。装備が原因だったとも、イベントの欠落を実機ログで証明できたとも断定しません。

v0.1.4は、専用クエスト上の期限を、入力ごとにバニラAPI `Game.GetRealHoursPassed()` の標準プレイ時間と比較します。受理した発動だけが期限を約60秒先（1/60時間）に設定し、待機中の入力は期限を延ばしません。**新しい更新イベント登録、Wait、常駐監視、ロード時の装備変更は行いません。** 時計が大きく巻き戻り、残り時間が63秒を超える異常値になった場合だけ、その入力から60秒へ一度補正します。

専用クエスト自体は初回発動時に開始し、その後もRunningのまま残ります。NPC Alias・目標・自動起動や、既存クエストへの変更はありません。保存状態を追加する点は変わらず、スクリプト不要・セーブへの影響なしという意味ではありません。

コンパイル済みPEXを模擬APIで実行し、更新登録を一切復元しないロード、再入力、旧版の待機フラグ、遅れて届く旧イベント、時計の巻き戻りを検査します。**標準プレイ時計の保存・進行は模擬しており、Skyrim本体の保存・復元、メニュー中の時間計測と装備入力は実機未確認です。** 詳細は [v0.1.4の変更](docs/RELOAD_FIX_0.1.4.md) と [検証記録](docs/VALIDATION.md)。

その後、v0.1.4でもロード後に発動せず、付け外し後にクールダウン時間を経て発動するような挙動が報告されました。待機解除イベントの廃止だけで問題を解決したとは扱いません。主能力の直接Castも不発、内部探知の直接Castは表示できたため、現在は入力スクリプトと制御の診断へ進んでいます。新たな自動装備処理は追加しません。

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

現在ユーザーが確認したIndexは **FE:CF5** です。この値なら、追加コマンドは次です。以前のxEdit出力のFE:CFDとは異なります。

```text
player.addspell FECF5800
```

Indexが変わった場合はMO2右側の現在値を使います。`FE:xxx` なら完全なFormIDは `FExxx800`。どのIndexも将来にわたって固定とは扱いません。スクリプトの参照はVMADで指定しており、ロード時のIndexをコードへ直書きしていません。

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
player.removespell FECF5800
```

最後の発動から通常画面で60秒以上待ち、専用クエストを停止して別名で保存してからMODを無効化します。現在のIndexがFE:CF5なら停止コマンドは `stopquest FECF5804`。このコマンドは本MODの専用クエストだけを対象とします。確実に導入前へ戻す場合は導入前のセーブを使います。セーブからの完全な除去は制作環境では検証できていません。

## 制作ソース

`KhajiitKeenSenses-0.1.4-source.zip` はESP生成コード、PSC、検査器、テスト、文書を含む開発用ZIPで、MO2へ導入するZIPではありません。[ビルド方法](docs/BUILD.md)と [参照元](docs/SOURCES.md) を同梱しています。ゲーム本体、Requiem/LoreRimのプラグイン、第三者ツールのバイナリは同梱しません。
