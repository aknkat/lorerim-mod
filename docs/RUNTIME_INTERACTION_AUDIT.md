# 使用中MO2プロファイルの照合：2026-10-17

**結論：一覧の整合性とLKSの優先順位に問題は見つからなかった。ロード後の不発の原因、特定MODとの実行時競合は未確定。** 診断版を追加したり、他MODを無効化したりする根拠はまだない。

## 資料と検査範囲

ユーザー提供の `modlist.txt`、`plugins.txt`、`loadorder.txt` を読み取り専用で照合した。原本は公開リポジトリへ転載しない。添付内の説明やセパレーター名は構成データとして扱う。

| ファイル | バイト数 | SHA256 |
|---|---:|---|
| modlist.txt | 150034 | `f4d941ea48fe29eb0444ba3122161e61cda46a869df654663738558c8aa2d9c7` |
| plugins.txt | 120497 | `6fae2fd19c7fee3640f392af6bd57bfe55bb71fecaff017ec4d31d77ea64bdc6` |
| loadorder.txt | 122559 | `11c867345407f3095b576eef111a05975b86f6bd577e49ef6554787ab3ed27af` |

- `plugins.txt` の有効プラグインは3413件。大文字小文字を区別しない名前の重複は0件。
- `loadorder.txt` は3493件。有効プラグイン3413件はすべて含まれ、その相対順序も一致した。
- `modlist.txt` のセパレーターを除く項目は、`+` 3897件、`-` 49件、`*` 4件。これをDLLやスクリプトの実ロード数とは扱わない。
- 一覧にはDLLの実ロード結果、バージョン、実ファイルの内容、INIの値、保存されたMCM設定は含まれていない。

## LKSとパッチの位置

| 資料の行 | 内容 | 判断 |
|---|---|---|
| modlist 2 | `+KhajiitKeenSenses-0.1.4-diagnostic5-MO2` | 診断5は有効。本体より高い優先順位に置かれている |
| modlist 3 | `+Khajiit Keen Senses` | 本体も有効。診断5が意図した2スクリプトを上書きする順序 |
| plugins 3415 / loadorder 3494 | `KhajiitKeenSenses.esp` | 両一覧の最後。有効な後続ESPはない |
| plugins 1720 / 3350 / 3394 | Requiem for the Indifferent / Synthesis - Requiem Patcher / Synthesis - Spell Absorption | いずれもLKSより前 |

MO2のmodlistは高い優先順位が先頭側に並ぶ。この一覧上の順序は正しいが、仮想Data内のPEXの内容や、一覧外のOverwrite・手動配置ファイルまで検査した意味ではない。実機では診断5のINPUTとACCEPTEDが表示されたことも別に確認している。

LKSより後のESPが新規レコードを上書きしているという説明は、この一覧では支持されない。ただし前方のプラグインが定義するPerk、参照先レコード、DLLや配布処理による実行時変更は、この順序だけでは否定できない。既存レコードの上書き0件も、すべての相互作用がないという証拠ではない。

## 有効な関連MODと公開実装

公開ソースの固定コミットを調べた。**インストール済みの版・設定と一致することは未確認。** ソースが見つかったMODだけを原因候補にすることも、見つからなかったMODを無関係とすることもしない。

| 分野 | 一覧で有効な主なMOD | 確認できた範囲と限界 |
|---|---|---|
| 入力 | Complete Controller Setup（modlist 25）、Gamepad Plus Plus（26）、Auto Input Switch（27） | Controller SetupとGamepad++は両方有効。公開Gamepad++のキー処理は組み合わせからキーを選び、押下・0.1秒待機・解放を行う。実際の割り当てとController Setupによる変更は未取得 [G1] |
| インタラクション | SkyInteract（321）、Remote Interactions（937）、Dynamic Activation Key（1293–1295）、Immersive Interactions（752） | 同時に有効。ただし `No nearby items to interact with` の発生元と、LKSのCastを妨げる因果関係は未特定。通知が出ることだけで競合とはしない |
| 詠唱・魔法 | STB Quick Hotkey Cast（3858）、Dual Casting Fix（3903）、Spell Absorption Rework（1342）、Scrambled Bugs（3927）など | 名前と有効状態を確認。適用される設定・Perk・フックを全件検査した資料ではない。インストール済みファイルとの照合がないため原因・無関係のどちらにも確定しない |
| Papyrus | Papyrus Tweaks NG（4019）、powerofthree's Tweaks（4020）、DLL Tweaks（424） | Papyrus TweaksのNative高速化は呼び出しのフレーム同期を変える。ただし公開ソースの標準値は無効、標準除外にはCastが含まれる [P1][P2]。DLL Tweaksの内容は一覧から分からない |
| ENB | Cabbage ENB - Lore Cut（72）、ENB Light Detection Fix（3983） | 調べたENB Light Detection Fixは粒子光の明るさをAIの隠密判定へ加える処理。生命探知を有効化する設定やSpell.Castのフックは確認できなかった [E1]。導入済み版の全相互作用を否定する意味ではない |

powerofthree's Tweaksの公開ソースでは、ScriptSpeedupが対象にするのはUtility.RandomInt/RandomFloatであり、Castを直接高速化する処理ではなかった [T1]。また、調べたロード時の魔法再適用処理はプレイヤーを除外している [T2]。これも導入済み版と設定の照合がないため、MOD全体の無関係を証明するものではない。

## 次に必要な資料を1ファイルへ限定

MO2右側の **Dataタブ → SKSE → Plugins → PapyrusTweaks.ini** に表示される、実際に優先されるファイルを読む。Papyrus Tweaks NGのMODフォルダーにある初期設定とは限らない。DLL Tweaksは一覧上で優先されるが、このファイルを提供しているかは未確認。提供元の表示も記録する。

公開ソースでは次の設定を読む [P2]。

```ini
[Experimental]
bSpeedUpNativeCalls=...
sScriptClassExclusions=...
sScriptMethodPrefixesToExclude=...
```

古い版では `bRunScriptsOnMainThreadOnly`、`sMainThreadClassesToExclude`、`sMainThreadMethodsToExclude` などの旧名があるため、値を抜粋せずファイル全体で版差も確認する。標準値と異なるからといって設定を直ちに変更しない。

高速化が有効でCastの除外も外れていれば、今回の呼び出し経路の差に関係し得る具体的な設定として調べる。無効またはCastが除外されていれば、その結果に応じてこの直接的な説明の優先度を下げる。どちらの結果も単独で原因確定にはならない。グローバル設定を変えて他MODへ影響を広げる修正は、この確認では行わない。

これはゲームを起動しないファイル確認であり、新たなセーブ・ロード試験ではない。追加の診断ZIPや試験コマンドは作成していない。

## 解決の見通し

入力イベント到達、待機判定の受理、DetectionSpellがFECF5803であること、同じ内部魔法のコンソール経由の表示は実機で確認済み。PapyrusのCastが戻ったことは効果適用成功の証明ではない。入力・詠唱状態、呼び出し元やタイミング、他MODのフック、本MODの実装を含めた差は残っている。

今回の3ファイルから短期修正を約束できる原因は得られていない。上記INI確認にも根拠がなければ、別の仮説を次々に実機で試す進め方には戻さない。現行版を完成・互換性検証済みとは扱わず、追加対応の範囲を再評価する。

## 公開ソースの固定参照

- [P1: Papyrus Tweaksの標準値・Cast除外](https://github.com/Nightfallstorm/PapyrusTweaks/blob/8e0288fd0c002d7e8704d22766bb1980572ea1da/src/configuration/Settings.h#L44-L55)
- [P2: Papyrus Tweaksの設定名・同期変更の説明](https://github.com/Nightfallstorm/PapyrusTweaks/blob/8e0288fd0c002d7e8704d22766bb1980572ea1da/src/configuration/Settings.cpp#L111-L118)
- [P3: 高速化のクラス・関数名による除外判定](https://github.com/Nightfallstorm/PapyrusTweaks/blob/8e0288fd0c002d7e8704d22766bb1980572ea1da/src/hooks/performance/NativeSpeedUp.cpp#L39-L81)
- [G1: Gamepad++のキー押下・解放](https://github.com/pijaczkar8/GamepadPlusPlus/blob/9ecd9b020feab740e1bedf78e950a46a18e7bb85/src%20-%20papyrus/gpp_keyhandler.psc#L246-L271)
- [E1: ENB Light Detection Fixのフック](https://github.com/clayne/ENBLightDetectionFix/blob/5473f99b6b1893ec8d81bafafcb8a633763ff5c0/src/ENBLightAffectsStealth.h#L61-L108)
- [T1: powerofthree's TweaksのScriptSpeedup](https://github.com/powerof3/po3-Tweaks/blob/47e8b72118b2e666af3c03fc3baaec8f73972f94/src/Experimental/ScriptSpeedup.cpp#L4-L24)
- [T2: powerofthree's Tweaksのロード時の魔法再適用](https://github.com/powerof3/po3-Tweaks/blob/47e8b72118b2e666af3c03fc3baaec8f73972f94/src/Fixes/ReapplySpellsOnLoad.cpp#L12-L19)
