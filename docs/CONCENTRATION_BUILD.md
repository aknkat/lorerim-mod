# 集中呪文版0.2.6の制作・検査

Python 3.10以上の標準ライブラリだけで生成・基本検査できます。旧版用の.NET・Caprica・Wineは使いません。ビルドは独立した新規レコードを書きます。専用EFSHはユーザー提供のxEditテキストにある標準シェーダーの設定から復元し、別IDへ複製・調整します。ゲームや第三者ESPのレコード自体は上書きせず、画像・モデル・第三者ツールを同梱しません。

```bash
python3 tools/build_concentration.py --package-only
python3 -m unittest discover -s tests -p test_concentration.py -v
python3 tools/build_concentration.py
python3 tools/verify_concentration.py dist/KhajiitKeenSensesConcentration-0.2.6-MO2.zip
```

作業ディレクトリはこのソースZIPを解凍したルートです。生成先は `build/concentration-0.2.6/` と `dist/`。既存の旧版ZIPと旧PluginBuilder／Papyrusソースは変更しません。同じ版の配布物が存在し、内容が異なる場合は上書きを拒否します。リリース済み成果物を変更する場合は新しい版にします。

0.2.4は時間・範囲・対象条件の変更を含むため、関連テスト19件と以下の第三者読み戻しを実行し、すべて合格しました。ゲームの条件再評価や詠唱を実行するテストではありません。

0.2.6のリリースは色差分と梱包時の構造チェックのみ確認し、テスト一式・第三者読み戻しは再実行していません。

## 独立読み戻し

基本検査はビルダーをimportしない `verify_concentration.py` と既存の `formats.py` によるサイズ・値・参照・条件・文字列・アーカイブの検査です。条件の真理値表と境界検査は符号化した論理の検査であり、ゲーム内の条件コンテキストの実証ではありません。

第三者読み戻しはNode.jsと `@fcrick/tes-data 0.0.1` を検査用の作業ディレクトリにインストールして実行します。パッケージのinstallスクリプトは実行しません。ゲームへの依存追加ではありません。

```bash
npm --prefix /tmp/lksc-reader install --ignore-scripts --save-exact @fcrick/tes-data@0.0.1
node tools/verify_concentration_third_party.cjs /tmp/lksc-reader/node_modules/@fcrick/tes-data build/concentration-0.2.6/KhajiitKeenSensesConcentration.esp
```

検査ではTES4と3つのGRUPを辿り、全レコード・サブレコードを第三者リーダーで読みます。EFSH／MGEF DATA・SPIT・CTDA・EFITを同じライブラリで再出力して元のバイト列と一致することも確かめます。この読み戻しもSkyrimの実行を代替しません。

## 設計上の決定

- 1 SPEL + 1 MGEF + 1 EFSH。マスターはSkyrim.esmのみ。0.1.xの旧特殊能力版とは分離。集中版0.2.0のESP名・SPEL/MGEFのIDは維持。
- SpellType Spell、CastType Concentration、Delivery Self、EitherHand。EFIT Duration 0は集中中の標準設定であり、ゼロ秒の単発効果を意味しません。
- SPEL ManualCostCalcとBase Cost 50、MGEF Base Costも50。これは補正前の毎秒コストです。
- 変性分類（ActorValue 18）を維持し、SkillUsageMultiplier 0とHalf-cost Perk NULLを設定。通常の手持ち生命探知の形を優先します。別途上げた変性スキルや一般的なコスト補正から完全に独立させる処理はありません。
- Area 17 feet（約362.7ゲーム単位）で距離条件350以下を覆います。最終上限は約5m。Magnitudeでは範囲を指定しません。PowerAffectsMagnitude／Durationを設定せず、両手強化の変更も要求しません。
- 探知対象条件はSubject。使用者条件はSPELの効果エントリーでTarget（術者）を指定。プレイヤーAND（通常Khajiit OR 吸血鬼Khajiit）。自己参照のHasMagicEffect条件は使いません。
- 原仕様の死体・アンデッド・機械除外と標準NoDetectLifeを維持し、ActorTypeDaedra（Skyrim.esm:00013797）の除外を追加。対象の種族・敵味方による条件は付けません。
- MGEFの対象フィルター7件をANDで結び、その後に `(IsInInterior == 1 OR GetCurrentTime >= 19 OR GetCurrentTime < 6)` のOR群をANDで追加。3件ともRun On Reference = PlayerRef（00000014）を明示。屋内判定は探知対象の状態を使いません。
- 可用性条件はMGEF側に置き、エンジン標準の条件評価に任せます。ゲーム内での再評価タイミングは未確認で、朝6時の即時描画停止・詠唱停止・消費停止を保証しません。独自のInterruptCastや時計更新は実装しません。
- 標準LifeDetectedEnemyの400バイトの設定は `tools/data/life_detected_enemy.json` に保持。100個のフィールド名・オフセット・値を記録し、Skyrimの元EFSHのData Size 536も、400バイトDATAと全サブレコード長で再計算して照合しました。
- 専用EFSH `LKSC_DetectionAmberShader`（ローカル802）では、DATAの188／192／196にRGB(223,168,149)、384のFlagsを0x10001から0x1へ変更。Particle Grayscale Colorを解除し、NAM9も空にして直接RGBを使用。その他の粒子・透明度・合成・Z Testの設定は変更しません。0.2.6では0.2.5のRGB3キーだけを#DFA895へ変更します。
- MGEFのHit Shaderを専用EFSHへ、Casting ArtをNULLへ変更。Casting Light・Hit Art・ImageSpaceModifier等もNULL。音・腕のアニメーション・通常の詠唱処理は維持。
- 公開済み0.2.3のフィールドを記録した `tests/fixtures/v023-concentration.json` と照合し、SPELはBase CostとEFIT Area、MGEFはBase Cost・Spellmaking Area・CTDA以外が同じであること、EFSHがRGB3キー以外同一であることを検査します。境界・対象フィルター・OR群は生成済みCTDAを独立した評価器へ読み戻して確認します。
- 独自VMAD・Papyrus・QUST・DLL・アップデート登録・タイムスタンプ・共有シャウト待機の変更なし。

## スキーマと参照根拠

- [xEdit TES5スキーマ](https://github.com/TES5Edit/TES5Edit/blob/9fb016884bec138ea6c7b872cec831537d464c3e/Core/wbDefinitionsTES5.pas)：SPEL、MGEF、CTDA、フラグ・ActorValue・Archetype・CastTypeの値。
- [CommonLibSSE-NG SpellItem](https://github.com/CharmedBaryon/CommonLibSSE-NG/blob/b93280e832f263dbef44e44cbe2936622a02f91a/include/RE/S/SpellItem.h)：標準SPITとコスト・詠唱種別。
- ユーザー提供のxEdit出力：標準Detect LifeおよびRequiem - Magic Redoneの勝者のConcentration／Self、EitherHand、Area、手の表示・音・標準参照先。原本やそのレコードペイロードはソースZIPに含めません。
- [第三者ESPリーダー](https://github.com/fcrick/tes-data)：npm 0.0.1、公開パッケージのintegrityに従って取得。MODには同梱しません。

Skyrimを実行できない制作環境のため、実機の結果を合格扱いしません。未検証項目と導入・解除・旧版入りセーブの扱いは [CONCENTRATION.md](CONCENTRATION.md) を参照してください。
