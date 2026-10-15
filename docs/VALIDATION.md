# 検証記録

制作日：2026-10-15（日本時間）。対象：Skyrim SE 1.6.1170 / LoreRim v5.0.4.8 Default / Requiem / Cabbage ENB。

これは**実機未検証の試験版**です。ファイル作成とゲーム内の動作確認を区別します。

## 合格したファイル検査

- MutagenでESPを書き出し、別の読み込み経路で再読み込みする。
- 独立したPythonリーダーでTES4/GRUP/MGEF/SPEL/VMAD/CTDA、ローカル参照、英語・日本語Stringsを検査する。
- CapricaのSkyrimモードで実際にPSCからPEXをコンパイルする。
- PEXの形式、全オブジェクトと命令、分岐先、プロパティとESPのVMADの対応を検査する。
- コンパイル済みガードと出力された条件表を、対象外の種族・NPC・死体・機械・距離境界のケースで検査する。
- 独立したChampollionでPEXをデコンパイルする。
- 再ビルドのバイト一致、ZIPのルート配置・CRC・SHA256を検査する。

`python3 -m unittest discover -s tests -v`：**11 tests / OK**。対象は次のとおりです。

1. ESLフラグ・マスター・新規レコードのみであること。
2. ヘッダーの件数・FormIDと、RACE/PERK/QUST等の変更がないこと。
3. Lesser Power・Self・Fire and Forget・ゼロコスト・制御効果60秒。
4. NoRecast/NoDeathDispel・クールダウン条件・カジート/吸血鬼カジートの条件ORグループ。
5. Detect Life archetype・共通シェーダー・範囲・探知2秒。
6. 出力CTDAの距離境界560 units、死体/アンデッド/機械/自身の除外条件表。
7. 実際のPEXとESPのプロパティ・FormID対応。
8. コンパイル済みPEXのガードをモックAPIで実行：正しいプレイヤー、吸血鬼カジート、別種族、NPC、異なるcaster、未設定プロパティ。
9. 英語・日本語の全表示文字列への参照が解決すること。
10. 切れたPEX・異なるゲーム形式を検査器が拒否すること。
11. コンパイラの既知の長さフィールド補正が4バイトだけで済み、それ以外の破損を拒否すること。

Caprica v0.3.0：Skyrimモード、strict、全警告をエラー扱いにして**コンパイル成功**。出力はSkyrim PEX 3.2 / Game ID 1です。

独立したChampollion v1.3.2：**1 file processed / デコンパイル成功**。オブジェクト長補正の前後で、デコンパイルしたPSCと命令の逆アセンブルがそれぞれバイト一致しました。処理はGame.GetPlayer、Actor.GetRaceでのガード、DetectionSpell.Castの1回呼び出しです。

初回の独立検査では、Capricaのオブジェクト長フィールドのバイト順不一致と、内部魔法の空の説明文に日本語の項目がなかった点を検出しました。前者は実長と一致する場合だけ長さマーカーを補正し、後者は両言語を明示して再生成しました。検査を弱めず、修正後に全11件が合格しています。

MO2 ZIP：**17 files / Dataルート構造、ZIP CRC、全ファイルのSHA256が合格**。他MODのスクリプト、ビルド用APIスタブ、DLLは含みません。

条件表のテストは記録された判定内容の検査です。SkyrimがDetect Lifeの条件を評価する対象・タイミング、実際の距離、描画、残時間を証明するものではありません。

## 再現性

同一ソースでの連続ビルドを検査し、ESP、補正/メタデータ固定後のPEX、Strings、MO2 ZIP、制作ソースZIPのバイト一致を確認済み。記録を含む最終ZIPにも同じ検査を実施した。

## 実機では未確認

- SkyrimとMO2による実際のESP/PEXロード。
- Cabbage ENBでのLifeDetectedの表示、壁越しの見え方、2秒での消失。
- 約8mの半径、移動中の対象、Native Detect Lifeの条件評価と距離判定の組合せ。
- 再使用60秒、連打、保存/ロード後の残時間、待機・睡眠・メニュー・セル移動。
- LoreRim/Requiemの最終勝者、生成パッチによる新規レコードの変更、独自Actorのキーワード。
- MOD無効化後のセーブの状態。

この機械にゲーム本体、Skyrim.esmの実内容、LoreRim/Requiemのプラグイン、ENBはありません。したがって、LoreRim/Requiemの既存生命探知レコードをそのまま複製したものではありません。代わりに標準のDetect Life archetypeと既存のLifeDetectedへの参照で新規MGEFを定義しました。危険な既存レコードの上書きや、他MODの効果の変更は行っていません。

## 依存・競合の範囲

- 直接のマスター依存：`Skyrim.esm` のみ。
- SKSE関数呼び出し：なし。使用するAPIはバニラの `Game.GetPlayer`、`Actor.GetRace`、`Spell.Cast` と `OnEffectStart`。
- 既存レコードのオーバーライド：0件。2 MGEF + 2 SPELの4件のみ。
- 既存ナイトアイ・種族・Perk・NPC・クエスト・ActorValueの値は変更しない。
- 生命探知の表示は既存LifeDetectedの最終定義に依存する。新規レコードだけでも、表示シェーダー・Actorキーワード・エンジンの仕様まで他MODから独立するわけではない。
- クールダウンは有限時間の魔法効果として保存する設計。外部処理でこの効果を消した場合は制限も消える。常駐クエストやポーリングで再付与する構成ではない。

具体的な実機確認は [IN_GAME_CHECKLIST.md](IN_GAME_CHECKLIST.md) を使ってください。
