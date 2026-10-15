# 実機確認手順（未実施）

対象は Skyrim SE 1.6.1170、LoreRim v5.0.4.8 Default、Requiem、Cabbage ENBです。以下はテスト手順であり、合格記録ではありません。

## 1. 最終ロードオーダーとSSEEdit

- MO2からSSEEditを起動し、実際のロードオーダーとこのESPを読み込みます。
- このESPを選び「Check for Errors」。未解決FormID、VMADプロパティ、不正なSPEL/MGEFがないことを確認します。
- マスターは `Skyrim.esm` だけ、新規MGEFが2件・SPELが2件、既存のRACE/PERK/NPC/魔法レコードのオーバーライドは0件であることを確認します。
- `LKS_KeenSensesPower` は Lesser Power、Self、Fire and Forget、Base Cost 0、効果のDuration 60。
- `LKS_KeenSensesCooldownEffect` はScript、No Recast、No Death Dispel。No DurationはOFF。VMADのDetectionSpell、KhajiitRace、KhajiitVampireRaceが解決されること。
- `LKS_DetectionPulse` の効果Duration 2、Magnitude 26.25、Area 0。
- `LKS_DetectLivingEffect` はDetect Life、Hit Shader `Skyrim.esm:00000146 (LifeDetected)`、GetDistance条件が `PlayerRef <= 560`。死亡・アンデッド・ドワーフ機械の除外条件があること。
- `LifeDetected`、KhajiitRace、KhajiitRaceVampire、ActorTypeUndead、ActorTypeDwarvenの最終勝者を確認します。生成パッチが新規レコードを変更している場合、その変更を調べてから動作を判断します。この制作環境ではRequiem/LoreRimの勝者を照合していません。

## 2. 探知と約8mの境界

- 生きた人間・動物をそれぞれ用意します。敵と味方が同じ色で見えること。
- ターゲットをコンソールで選択し `getdistance player` で距離を調べます。この表示はゲーム内unitsです。
- 近い生物、約500、550、560、570、600 unitsにいる生物で確認します。条件上の境界は560です。キャラクターの移動・Actorの原点による測定差も記録します。
- 壁・扉越しの探知を確認します。昼・夜、屋内・屋外で同じ範囲になること。
- 約2秒で表示が終了することを確認します。表示シェーダーのフェードや描画遅延も確認します。
- Cabbage ENB有効時に確認します。必要ならENBの効果を一時的に切り替え、標準の生命探知が表示されるかと、この能力の表示を比較します。MODはENB設定を変更しません。

## 3. 除外対象

- 生きた通常NPC・動物：探知される。
- Draugr、Skeleton、Vampire等、ActorTypeUndead付きActor：探知されない。
- Dwarven Spider、Sphere、Centurion等、ActorTypeDwarven付きActor：探知されない。
- 死体：探知されない。探知中に死亡した場合の表示終了も確認する。
- プレイヤー自身：探知されない。
- LoreRimで追加された敵も確認する。独自の機械・アンデッドが標準キーワードを持たない場合、このキーワード判定だけでは除外できない。
- 他の生物についてはSkyrimのDetect Life固有の扱いも確認する。特殊なActor、NoDetectLife設定、変身時のActorについて未検証。

## 4. 再使用とセーブ/ロード

- 発動を時刻0秒とし、1秒・2秒・30秒・59秒に再度発動を試す。探知が再発動せず、残時間が60秒に戻らないこと。
- 60秒経過後に再発動できること。連打しても探知や制御効果が重複しないこと。
- 発動15秒後に保存し、ロードする。残り約45秒の制限を維持すること。
- 発動直後・終了直前の保存とロード、ゲームを完全終了してからの再開でも確認する。
- メニュー中、ゲーム内の待機・睡眠、別セルへの移動、時間倍率を変更するMODによる扱いを確認する。タイマーはエンジンの魔法効果の残時間に従い、独自のリアルタイム時計は使わない。
- 外部MODがこの制御効果を明示的にdispelした場合は制限が解除され得る。通常のLoreRimの操作でそうなるかを確認する。

## 5. 種族・NPC・既存能力・解除

- 通常のカジートとカジート吸血鬼のプレイヤーで発動できること。
- 別種族のプレイヤーに手動で付与しても探知が発動しないこと。
- カジートNPCを含め、NPCへの自動付与がないこと。試験用に主能力をNPCへ付与しても制御効果・探知が発動しないこと。
- 主能力の使用中に種族を変更した場合の挙動を確認する。種族条件は発動時に評価する設計であり、開始済み2秒の探知を途中で取り消すスクリプトはない。
- Night Eyeが元のまま残り、既存の魔法・Perk・種族能力・経験値・マジカ・スタミナに変更がないこと。
- `player.removespell`、効果の終了、再付与を確認する。MODを外す確認は別名のテストセーブで行う。

結果は「合格/不合格/未実施」と、使用したプロファイル・ロードオーダー・FormIDを添えて記録してください。
