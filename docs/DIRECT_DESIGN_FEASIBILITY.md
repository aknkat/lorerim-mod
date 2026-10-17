# 直接探知方式の設計検証

2026-10-17。対象はSkyrim SE 1.6.1170 / LoreRim 5.0.4.8 Default。

**結論：直接探知＋専用SKSE DLLで、3条件を両立させる具体的な候補は設計できた。待機ロジックは単独実行で検査できたが、エンジンへの接続方法は未確定であり、採用確定・実機合格ではない。** ESP・Papyrusだけで同じ条件を確実に満たす代案は、今回の資料では確認できなかった。

## 新しい構成

```text
通常の能力入力
  → エンジンの発動処理
  → LKS専用の発動前ガード
  → 主能力のDetect Life効果を直接適用（2秒）
```

探知を別のSPELへPapyrusのCastで渡さない。主能力はコスト0のLesser Powerのまま、探知効果を直接持たせる。候補のESPは新規SPELと新規Detect Life MGEFの2レコードで、QUST・VMAD・PEXを持たない。

DLLはこの能力の発動制限と残時間だけを担当する。キー登録、操作の生成、装備・付け外し、種族・Perkの変更、他の魔法の解除、共有シャウト待機時間の変更は行わない。プレイヤーの通常・吸血鬼Khajiitだけを許可し、対象外のNPC・種族から本能力が使われる場合は拒否する。他の魔法は元の処理へそのまま渡す。

使用中のmodlistにはAddress Library（4030行）とSKSE64（4032行）があるため、一般的な依存MODを新しく探して追加する案ではない。ただし、**本MODに専用DLLが1本必要になる**。従来の「バニラPapyrusのみ」という実装から依存条件が変わる。

## 直接探知の根拠と限界

ユーザーは内部探知FECF5803への直接Castで発光を確認した。公開済みv0.1.4 ZIPを再読込し、803には探知MGEF802が直接付き、Magnitude 0 / Area 27 / Duration 2 / Self / Fire and Forgetで、検出MGEFにVMADがないことも確認した。ZIPのSHA256は `36473781515cb99d1f8bf47a05cff933ed2a4b37c1dd8360fb3b07e39c9a9fad` のまま。

この探知データと除外条件を出発点にできる。ただし803はType Spellで、コンソール試験のSourceはleft。新しい主能力はType Lesser Powerで通常の能力入力を使うため、**直接Castの成功だけで新方式の発動成功を証明したことにはならない。** 約8mの境界、吸血鬼Khajiit、除外対象などの未確認事項も残る。

## 比較して採用候補から外した案

| 案 | 判断の根拠 |
|---|---|
| 探知と60秒効果を並べ、No Recastだけで制限 | 60秒効果があることは、探知の再適用を止める仕組みにならない。既存v0.1.2でもNo Recast単独の制限は実機で不成立 |
| 待機効果の有無を自己参照条件にする | 自分が適用されると条件が変わる。ActiveEffectには条件再評価の処理があり、既存版でも自己参照を撤回済み。Cast時だけの条件だと仮定して再利用しない |
| シャウトの回復時間を60秒へ設定 | 他のシャウトと共有する状態へ作用するため、干渉を小さくする要件に合わない |
| 待機中に能力を削除し、時間後に付け直す | 能力選択・お気に入り・他MODの装備処理との接点が増える。ロード後の付け外しを避けたい目的にも合わない |
| ゲーム内日時だけで60秒を測る | 時間倍率、待機・睡眠などと実時間の60秒を混同するため、そのままでは仕様を満たさない |
| 発動後のイベントだけで再使用を拒否 | イベント前に探知が適用されれば、待機中の発動を防げない |
| 通常のCheckCastだけへガードを追加 | 公開APIにSetSkipCheckCastとCastSpellImmediateがある。通常チェックを必ず通るという仮定は採用できない |

SPELのcastDurationも専用の再使用時間ではない。CommonLibの公開宣言ではGetFixedCastDurationはConcentrationの場合だけこの値を返す [S1]。Lesser PowerのFF用60秒制限として流用しない。

## 待機状態の保存方法

二つの候補を比較した。

1. **60秒の専用ActiveEffectを印にする方法。** NativeのActiveEffectにはduration・elapsedSecondsとSaveGame/LoadGameがある [S2]。ユーザー提供のxEdit出力にも、Script archetypeだがVMADを持たないVoiceAuraWhisperDescriptionがあり、「Script archetypeなら必ずPapyrusスクリプトを追加する」という制約はない。ただし、その印を他の処理が解除したり持続時間を短くしたりすれば60秒前に待機が終わる。これらが実環境で起こらないことは未確認なので、厳密な待機の第一候補にはしない。
2. **DLLが独立した残時間を持つ方法。** 効果解除や魔法の持続時間補正とは独立させ、ゲーム進行中の非スケール実時間を減算する。保存するのは残時間だけ。プロセス開始時刻・絶対日時・PapyrusのBoolや実行中スタックに依存しない。こちらを実装候補とする。

2の保存ペイロードは64bit整数1個、8バイト。形式バージョンはSKSEのレコードヘッダーで管理する。SKSE SerializationInterfaceには固有ID、保存・読込・Revertのコールバックがある [S3]。ゲーム側との接続は未実装。

- 発動を受理した時だけ60秒へ設定する。通常の可否照会、待機中の入力、他の魔法では変更しない。
- 残り45秒で保存したら、完全終了・再起動後も45秒を復元する。終了中・ロード中・ゲームが停止するメニュー中は減らさない。
- 残り0秒の保存は、ロード直後から使用可能にする。ロードで勝手に発動させない。
- 新規ゲーム・保存データ切替時には一度リセットし、そのセーブの残時間を読む。他のセーブの状態を引き継がない。
- データが初めからない新規導入は0秒。不正な形式・範囲のデータは60秒へ再初期化し、永久ロックにしない。消失したco-saveから以前の正確な残時間を復元することはできない。

**保存情報がなくなる案ではない。** Papyrusの保存状態に代わり、ESSと対になるSKSE co-saveに固有データを持つ。バックアップや移行では両方が必要になる。Nativeコードと保存コールバックの実装にも検証が必要で、「スクリプトをなくせばセーブが安全」という判定はしない。

## 発動ガードと時間入力の接続条件

ここが未確定であり、単独検査の合格では埋まらない。

- **発動前に止める最終段階を特定する。** 通常のパワー入力、即時Cast、他MODのホットキー経路を含め、効果を適用する前にガードを通す必要がある。ActorMagicCaster/ MagicCasterには複数の段階がある [S4]。FindTargetsにはloadCast引数もあるが [S5]、通常・即時Castのすべてがそこを通ることは公開ラッパーだけでは確認できない。特定のフック位置へ断定していない。
- **物理的な発動1回につきガード1回。** 外側と内側で二重に制限すると、自分の最初の発動を止める。逆に別経路が迂回すれば連打可能になる。ロード時の効果復元・能力選択画面での可否照会を、新しい発動として数えない。
- **時計を実際のエンジンへ接続する。** BSTimerにはrealTimeDelta、UIにはGameIsPausedがある [S6][S7]。この値を単に読むだけで十分とは扱わず、1.6.1170で更新頻度、停止メニュー、読み込み直後、スローモーションとの関係を確認する。Nativeのフレーム更新への接続が増えるので、常駐処理ゼロとも言わない。
- **他のMODの処理を保つ。** 他のSpellは条件判定後すぐ元の処理へ同じ引数で渡す。元の処理を呼ぶことだけで競合が消えるわけではなく、同じ位置を使うDLLとの共存は未検証。

接続条件を確認できなければ、この候補を導入用MODへ昇格させない。公開APIの存在を、全経路の保証として扱わない。

## 実行した単独検査

[実験用C++コア](../experiments/direct-native-gate/cooldown_core.hpp) はSkyrim APIを一切宣言・模倣しない。制限判定・整数時間・保存バイト列だけを実装する。[検査](../experiments/direct-native-gate/verify.cpp) は同じコアをコンパイルして実行した。

```bash
c++ -std=c++20 -O2 -Wall -Wextra -Werror -pedantic -pthread \
  experiments/direct-native-gate/verify.cpp -o /tmp/lks-direct-native-gate-verify
/tmp/lks-direct-native-gate-verify
```

GCC 14.2.0、警告をエラーとしてコンパイルし、**5群と20万回の操作列を通過**。

- 60秒間に6万回再入力しても満了が延長されず、60秒境界で再使用できる。
- 一時停止12時間を除外し、残り45秒を新しいオブジェクトへ保存・復元して期限を迎える。使用可能な保存はすぐ使用可能。
- 他の魔法・NPC・別種族の操作、10万回の可否照会で残時間を変えない。不正な保存値は永久ロックにしない。
- 32スレッドの同時要求で受理は1回。エンジンや他MODのコードを呼んでいる間、コアのロックを保持する構成にはしない。
- 残時間を減算する実装を、絶対期限を持つ別の計算モデルと20万回比較。保存の巻き戻し、異なるプロセス時刻、一時停止、再入力、保存データ切替を含めて一致。

これは**新しいDLLのビルド・エンジン上の時計・フックの成否・ロード復帰・描画を検査したものではない**。Windows DLL・新ESP・MO2用ZIPはまだ作成していない。既存配布物は変更していない。

## 採用判断

| 条件 | 設計上の対応 | 現時点の判定 |
|---|---|---|
| 60秒制限 | 発動前ガードと独立した残時間。再入力で更新しない | コアは検査済み。実時間入力と全発動経路は未確認 |
| ロード後復帰 | 残時間だけをSKSEに保存し、更新イベント・装備し直しに依存しない | 保存形式と状態計算は検査済み。実ゲームのコールバック接続は未確認 |
| 他MODへの干渉を小さくする | 新規2レコード、既存レコード上書き0、入力・共有シャウト・装備を変更しない | レコード構成の候補。Nativeフックの競合は新たに検証が必要 |

従来の不発経路と復帰不能になる保存フラグを使わずに構成できる見込みはある。ただし、Nativeフックという別の接点が増えるため「従来版より安全」「LoreRimで動く」とはまだ判定しない。使用中の他MODが入力や詠唱そのものを変える場合の問題も、自動的に解消されるわけではない。

既存版のESP名・Quest・保存済みスクリプトを使い回す更新ではなく、別の固有ESPとして分離する想定。旧版からの移行は旧保存状態の扱いを含めて別に設計する必要があり、この単独コアの合格には含めない。

## 公開資料

CommonLibSSE-NGの固定コミット `b93280e832f263dbef44e44cbe2936622a02f91a` を参照した。リバースエンジニアリングされた宣言・ラッパーであり、ゲーム本体の全実装ではない。Creation Kit Wiki本文はこの環境から403拒否され、再取得できなかった。

- [S1: SpellItemのSPITとGetFixedCastDuration](https://github.com/CharmedBaryon/CommonLibSSE-NG/blob/b93280e832f263dbef44e44cbe2936622a02f91a/include/RE/S/SpellItem.h#L45-L72)
- [S2: ActiveEffectの保存・復元と時間フィールド](https://github.com/CharmedBaryon/CommonLibSSE-NG/blob/b93280e832f263dbef44e44cbe2936622a02f91a/include/RE/A/ActiveEffect.h)
- [S3: SKSE SerializationInterface](https://github.com/CharmedBaryon/CommonLibSSE-NG/blob/b93280e832f263dbef44e44cbe2936622a02f91a/include/SKSE/Interfaces.h#L81-L101)
- [S4: MagicCasterのCastSpellImmediate・CheckCast・SetSkipCheckCast](https://github.com/CharmedBaryon/CommonLibSSE-NG/blob/b93280e832f263dbef44e44cbe2936622a02f91a/include/RE/M/MagicCaster.h)
- [S5: FindTargetsの公開ラッパー](https://github.com/CharmedBaryon/CommonLibSSE-NG/blob/b93280e832f263dbef44e44cbe2936622a02f91a/src/RE/M/MagicCaster.cpp#L16-L21)
- [S6: BSTimerのrealTimeDelta](https://github.com/CharmedBaryon/CommonLibSSE-NG/blob/b93280e832f263dbef44e44cbe2936622a02f91a/include/RE/B/BSTimer.h#L33-L40)
- [S7: UI::GameIsPaused](https://github.com/CharmedBaryon/CommonLibSSE-NG/blob/b93280e832f263dbef44e44cbe2936622a02f91a/include/RE/U/UI.h#L78-L84)
