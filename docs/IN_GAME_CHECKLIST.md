# v0.1.3の実機確認

v0.1.1の近距離の赤い表示は確認済み。v0.1.2では押すたびに発動したため、v0.1.3は専用QUSTの共有フラグと単発更新で制限する構成へ変更した。v0.1.3のゲーム内動作は未確認。

ゲームを終了し、MO2で旧版をReplaceして導入する。能力は追加済みなら追加し直さず、そのまま使う。ESP名と既存800～803のFormIDを維持し、専用QUSTのみ804へ追加した。

確認は同じ生きたNPCの近くで、メニュー・コンソールを閉じた通常画面で次の1回にまとめる。

1. **0秒：Y＋RTで発動**し、赤い表示を確認する。
2. **30秒：Y＋RTを1回**押す。探知が再発動しないこと。
3. **初回から65秒：Y＋RTを1回**押す。再び表示されること。

Y長押しだけによる「no items to interact with」は別操作。連打時の音の発生元も未特定。音や通知だけで待ち時間を判断しない。有効な効果の残り時間表示は、この環境では出ていないため確認の前提にしない。

## 必要になった場合の切り分け

ファイル側は制作環境で検査する。ユーザー側でRaceの最終勝者、MCMやキー設定を一から調べ直す必要はない。上の確認が失敗した場合にだけ、結果に応じて切り分ける。

主能力は800、入力MGEFは801、探知MGEFは802、内部魔法は803、専用QUSTは804。送付されたロードオーダーのIndexはFE:CFD。実際の値は現在のMO2表示を優先する。

FE:CFDのままなら内部探知だけのコマンドは次。通常の能力で表示できている場合は不要。

```text
player.cast FECFD803 00000014 left
```

コンソールを閉じて確認する。これは入力スクリプトと60秒制限を経由しない。標準のオーラ・ウィスパーは広範囲の別能力なので、8mや2秒の検査には使わない。

## 詳細検査（必要時のみ）

- 距離：対象を選んで `getdistance player`。近距離、500/550/560/570/600 unitsの境界。Areaは27 feet、追加条件の上限は560 units。Actorの原点と移動による差を記録する。
- 表示：敵味方共通、屋内外・昼夜・壁や扉越し、自身の発光の有無。
- 対象：通常NPC・動物は表示。死体・Draugr・Skeleton・Vampire・Dwarven機械は除外。標準キーワードのない独自Actorは別途確認。NoDetectLifeを尊重する設計。
- 制限：待機中の再入力で表示や期限が更新されず、60秒後に使用できること。Papyrus負荷によるイベント遅延と区別する。
- 保存：発動15秒後に保存し、ロード後は約45秒の制限が残ること。ロードだけで探知が再発動しないこと。準備完了時の保存も確認する。共有フラグとNativeの単発更新登録を使い、入力MGEFの寿命には依存しない。
- 使用者：通常と吸血鬼のKhajiitプレイヤー。別種族やNPCへ手動付与しても使用できないこと。自動付与はない。
- 非干渉：既存Night Eye、Perk、種族能力、スキル経験値、マジカ・スタミナ。
- 解除：主能力を外し、最後の発動から通常画面で60秒以上待つ。専用QUSTだけを停止して別名保存後に無効化する。導入前セーブを保持する。手順はREADMEを参照。

## SSEEditの検査値

追加で再確認する場合は本ESPの「Check for Errors」と5件の固有レコードを対象にする。

- マスターSkyrim.esmのみ、上書き0件、MGEF 2件・SPEL 2件・QUST 1件。
- 主能力：Lesser Power、Self、Fire and Forget、Base Cost 0。入力効果のDuration **1秒**。
- 入力MGEF（旧EditorID `LKS_KeenSensesCooldownEffect`）：Script。**No Recast・No Death Dispelは無効**、Hide in UI有効、No Duration無効。VMADは旧3参照に加え、`CooldownController` が専用QUSTを参照する計4件。自己参照HasMagicEffect条件はない。
- 専用QUST：`LKS_KeenSensesControllerQuest`。Start Game Enabledなし、Alias・ステージ・目標なし。VMADスクリプトは `LKS_KeenSensesController`、参照はDetectionSpellと2種のKhajiitRaceの3件。
- 内部魔法：Magnitude 0、Area 27、Duration 2、Area Effect Ignores LOS有効。
- 探知MGEF：Detect Life、Actor Value None、No Area/No Duration無効、FX Persist有効、Hit Shaderは `LifeDetectedEnemy [EFSH:000DC209]`。GetDistance PlayerRef <= 560と除外条件。探知側のNoRecastは従来どおり有効で、60秒制限の管理には使用しない。

今後、生成パッチがこの5件自体を変更した場合はその差分を調べる。将来の生成パッチの動作まで今回検証したという意味ではない。
