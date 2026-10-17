# 鋭敏な感覚（集中）：LoreRim全体を踏まえた強度再評価

2026-10-17。対象は公開済み0.2.3（約6m、基礎25マジカ／秒、集中詠唱）。**非魔法特化のカジートについて、序盤から終盤までの用途を評価する。** ナイトアイは正常に働く状態を比較基準とし、現在のENB下で使えない状態を価値0の基準にはしない。

## 結論と提案

「全体平均でナイトアイと同程度〜やや控えめ」という従来の評価は支持できない。日中の利用だけでなく、短い詠唱で位置情報を持ち帰れること、使わないマジカを索敵へ転用できること、既存の隠密強化との相乗効果を過小評価していた。一方で、暗所の足場・罠・物品を見やすくする機能はなく、アンデッド・機械主体の場所では用途が小さい。能力の種類も、場面ごとの優劣も異なる。

**元の「昼夜使用可」を維持し、OP回避と実装の単純さを優先する提案は、半径約5m・基礎50マジカ／秒・デイドラの明示除外。** 短い距離上限を主制約にして、消費は補助制約とする。ナイトアイとの等価を実証した数値ではない。

今回は調査・調整案の作成のみ。ESP、配布ZIP、ゲーム内設定は変更していない。

## 調査範囲と根拠の強さ

- 提供されたmodlist全4086行をセクション単位で集計し、一覧全体を横断して関連項目を抽出した。セパレーターを除き、有効3897、無効49、その他の管理項目4。有効プラグインは3413。
- これは旧特殊能力・診断5が載った時点の一覧であり、その後の全変更を反映した現在のMO2一覧ではない。今回の集中版自体は0.2.3の実ファイル・生成コードを参照した。
- 種族、隠密、魔法、成長、敵・クエスト、戦闘、サバイバル、世界・照明・音、UI、装備・入力・DLL、生成パッチを検討対象にした。外見・家具・テクスチャ等も一覧には含まれるが、名前を確認したことを個々の実装の精査とは扱わない。
- 強い根拠は、提供されたxEdit出力、INI、公開済みESPの設定。種族・Perk等の補助資料はGigaPlannerの**5.0.4.2**データで、ユーザー環境**5.0.4.8**の全最終勝者ではない。プランナーの説明文と自動抽出された効果も完全一致とは限らず、数式の入力として混同しない。
- 全MODの実ファイル、全DLLの導入版、MCM、一般Perkの実効条件、敵の遭遇割合、使用頻度は未取得。全件の互換性確認やゲーム内実測を完了した意味ではない。今回、追加のオンライン検索はGitHub APIへの403で補完できなかった。

## 見落としを含む評価表

| 観点 | 関係する構成・確認した点 | 強度への影響と判断 |
|---|---|---|
| 昼夜と天候 | Cabbage ENB、NAT III、Lux / Lux Orbis / Via、Dynamic Weather and Time Based Detection | 暗闇以外でも生物の位置を得られる。暗い夜・天候による視認困難を補える場面がある。AIの隠密検知と生命探知は別処理で、双方に同じ制約があるとは扱わない。各設定の倍率は未取得 |
| 壁・曲がり角・上下階 | 同一の読み込まれた空間にいる対象を、視線が通らなくても探知する設定 | 接敵前の位置・人数・動きの確認が大きな利点。近距離でも遮蔽物の向こうを知る意味がある。ただし通常のロード扉越しに未読込の別セルを調べる能力ではない |
| 非魔法型の資源 | Races Redone、Birthsigns Redone、Biggie Traits、Wintersun、Wayfarer、Finesse、Destiny | 戦闘に使わないマジカなら消費の機会費用が小さい。魔法型でなくても属性・再生・汎用ボーナスで負担が減る。非魔法特化という条件だけで「終盤も重い」と決めない |
| 短時間詠唱 | 現行は開始時の固定消費・最低継続時間・独自クールダウンなし | 表示に必要な短い時間だけ唱え、手を武器へ戻しても得た情報は残る。維持できる最大秒数だけで強度を評価しない |
| カジート・隠密の相乗効果 | Races Redone、Stealth Redone、Shadow / Thief、Shadow Opportunist、Nocturnal's Favor | 接近・隠密強化と位置把握を組み合わせると先制や回避を選びやすい。役割が異なるので、静かな足取りと同じ効果の重複ではないが、相乗効果がある。名称だけで個別MODの全挙動を断定しない |
| 隠密中の詠唱コスト | 本MODはCasting Sound Level = Silent、Casting Light = NULL、手元のCasting ArtもNULL | プレイヤーに音が聞こえることはAIへの発見音の証明ではない。手を使うだけで大きな発覚リスクを負う、と弱体化を過大評価しない。実行時に他MODが加える効果は別途未確認 |
| 戦闘の危険と死亡の扱い | Requiem、Engaging Combat、Legendary Enemies、NPCs Take Cover、Project Gap Close、Dynamic Stat Scaler、Respawn | 危険な敵との不用意な接触を避ける情報は有用。難しい構成なら索敵能力を強くしても釣り合う、とは言えない。戦闘中は武器・盾・弓との装備切替が不利益になるが、戦闘前にはその負担が小さい |
| 対象となる生物 | 敵追加、Mihail系生物、VIGILANT、Undeath、各遺跡・ダンジョン拡張 | 山賊・フォースウォーン・ファルメル・動物等には用途がある。ドラウグル・吸血鬼・ドワーフ機械主体の場所では減る。追加Actorの実際のキーワード次第で例外が出るため、クエスト名から全員の分類を断定しない |
| デイドラの取りこぼし | 実xEdit出力のMagic Redone生命探知はActorTypeDaedraも除外。本MODにはその明示条件がない | NoDetectLife等で別途弾かれないデイドラを拾う余地がある。「生物のみ」を標準生命探知と同じ対象区分として説明するのは不十分。追加除外は元の確定仕様に対する新しい調整提案 |
| 成長・習得 | Experience、Static Skill Leveling Rewritten、Starting Skills、Improved Spell Learning | 使用経験値0は学習稼ぎを避ける設定だが、この成長構成で大きな弱体化として数えない。本MODは手動取得で習得過程を経ず、開始直後から索敵を持てる点も数える |
| 消費軽減・汎用Perk | MinSkill 0、Half-cost Perk NULL。補助資料にUnskilled Spellcasting、汎用コスト軽減等 | 半減Perkを指定しないことと、すべての軽減を受けないことは別。Unskilled Spellcasting等が本MODに実際に適用されるかは実Perk条件を未照合なので候補に留める。経験値0も消費固定にはならない |
| UI・視点・既存の情報 | Detection Meter、TrueHUD、Compass Navigation Overhaul、SmoothCam、音響拡張 | 既存表示や音で分かる情報との重複はあり得る。ただし未発見の対象の正確な位置や壁の向こうまで分かる設定とは限らない。設定不明のため「既に全部見える」と減点しない |
| 他の探知手段 | 既存Detect Life、囁きのオーラ、探知装備等 | 入手後の追加価値は下がる場合がある。新能力は習得前から使え、独自に使えてシャウト回復を使わないため、その入手制限を無料で借用しない |
| 対象外の探索 | 生物探知だけで地形・罠・鍵・アイテム・死体は見やすくならない | 正常なナイトアイの探索面の価値は残る。「何も光らない」ことは安全の保証にならない。これらは今回の能力の明確な限界 |
| 色・ENB・音 | 専用EFSH、ENB Lights For Effect Shaders、ENB Light Detection Fix、Unique Shaders Sound FX | 色味は見やすさの調整とし、読みにくさをバランスの主制約にしない。専用EFSHでも一般の描画処理から完全には独立しない。探知の発光が必ず照明やAI隠密へ影響する、という実証もない |
| 装備・ロードの不具合 | Gamepad++、STB Quick Hotkey Cast、Wheeler、Left Hand Equipment Overhaul、Magic Organizer等 | 通常呪文の装備・詠唱に接点は残る。ロード後の装備解除は原因未特定。操作上の不具合を意図的な弱体化として数えず、新たなタイマーや自動装備で埋め合わせない |
| 既存ナイトアイを残す仕様 | 本MODは種族・元能力を上書きしない | 将来ENB設定等でナイトアイも働くようになれば、両方を使える追加能力として再評価が必要。現在壊れている能力の補償という前提と区別する |

## 非魔法型でも消費が一定の制約にならない理由

補助資料のカジートは初期Magicka 100。通常のレベルアップでマジカを選ばなければ、レベルだけで必ず大量に増えるという根拠はない。ただし、それは全体を通じて100固定という意味でもない。

非魔法型でも回復・照明・支援魔法へマジカを使うなら資源が競合する。全員に余剰マジカがあるとは仮定せず、「非魔法型だから消費が必ず重い」という以前の推論を修正する。

- 5.0.4.2の資料には、Ladyの属性・再生、WayfarerのSurvival Instincts、FinesseのOutlaw / Sound Mind、DestinyのFocus / Magicka Surge / Spellsword、複数のTrait・信仰に回復や属性への接点がある。Spellswordは説明上「武器攻撃ごとに15マジカ回復」であり、魔法特化以外でもマジカを戻す経路の例となる。ユーザーがこれらを取得しているとは仮定しない。
- 逆にAtronachの自然再生不可、Traitや吸血鬼・サバイバルによる資源低下、重装の詠唱ペナルティで使いづらくなる構成もある。全ビルド共通の回復秒数は出せない。
- 提供INIではDLLTweaksの `bConcentrationCasting = true`。公開実装は集中呪文のコストと最大・現在側の資源を比較する。この環境で消費を上げると、単に継続時間が短くなるだけでなく、開始不能になる場合がある。`最大マジカ ÷ 基礎消費` を実際の使用可能秒数とは扱わない。
- 最大マジカ・実消費・実再生・装備・取得Perkが同じなら、レベルだけを変えて価値が変わると計算しない。進行段階により相手・装備・他の手段が変わることを別に考える。

単純な比較用に、詠唱中の消費を `基礎消費 × 有効な消費倍率 × 実際の詠唱秒数` と置く。下表は**数式上の例**で、表示が0.5秒で成立することや、消費・開始判定を実測した数値ではない。

| 消費倍率の例 | 現行25/秒：0.5秒 | 提案50/秒：0.5秒 | 現行25/秒：1秒 | 提案50/秒：1秒 |
|---|---:|---:|---:|---:|
| 1.0 | 12.5 | 25 | 25 | 50 |
| 0.5 | 6.25 | 12.5 | 12.5 | 25 |
| 2.0 | 25 | 50 | 50 | 100 |

高い毎秒消費でも短い索敵は残る。このため、消費増だけで日中・壁越し探知の価値をすべて相殺したと考えない。自然回復等がある場合も、専用の「60秒待ち」とは別である。

## 既存の生命探知との位置付け

提供されたxEdit出力で、Requiem - Magic RedoneのDetect Lifeは基礎50、集中詠唱、Area 100 feet（屋内）／200 feet（屋外）、熟練者のHalf-cost Perk参照。対象効果にはデイドラ除外がある。MinSkill 50等はランク設定であり、すべての状況でスキル50未満なら使用不能という意味にはしない。

提案の5mはこれより大幅に短く、通常生命探知の広域索敵を置き換えない。一方で、種族向けの手動取得により、通常の習得過程を経ずに近距離探知を持てる。基礎コストを既存魔法と同じ50にしても、実コストや総合価値が同一になるとは限らない。

## 調整案の比較

| 案 | 内容 | ねらいと限界 |
|---|---|---|
| **推奨：昼夜使用可を維持** | **約5m、基礎50/秒、デイドラを追加除外**。集中詠唱・敵味方同色・経験値0を維持 | 育成で消費が軽くなっても距離上限が残る。近距離の生物確認として使える。昼間や壁越しの先制情報は残るため、ナイトアイ等価を保証する案ではない |
| より慎重 | 約4m、基礎50/秒、同じ対象除外 | 近くへ寄る必要をさらに強める。範囲だけで調整できるが、使える場面が狭くなる。5m案でも強すぎる用途が残る場合の次候補 |
| 利用場面をナイトアイへ寄せる | 5m・50/秒に加え、屋内常時／屋外は18時～6時のみ探知 | 屋外昼間の追加価値を削る。元の「昼夜使用可」を変更する別仕様。明るさそのものとは一致せず、特殊なセル・屋外扱いの地下等も考慮が必要。屋内昼間の壁越し探知は残る |
| 消費だけ増やす | 6mのまま75～100/秒等 | 短い索敵・回復・軽減による抜け道が残る割に、重装や資源低下構成の開始不能を増やす。第一案にはしない |

5m・50/秒を選ぶ根拠は「厳密にナイトアイ1.0相当」という換算ではない。固定の索敵範囲を縮め、提供された通常生命探知の基礎コスト50を参照し、対象もその生物区分へ寄せる、という保守的な調整判断である。6mから5mへの平面の円面積比は約69%だが、敵数や有用性が31%下がるという意味ではない。廊下・壁・対象の配置で変わる。

「全体平均の価値」を単一の数値にするには、昼夜・探索場所・敵種・装備・詠唱頻度等の重みが必要。MOD数を遭遇割合に置き換えたり、主観的な点数を足して倍率と称したりしない。平均以上に、隠密で先制情報を得られる場面で過剰になりにくいことを調整の基準にする。

## 実装範囲と避ける変更

推奨案なら既存の集中版を保ち、次だけを変更できる。

1. 本MODのSPELのBase CostとMGEFのBase Costをともに50へ。
2. EFIT AreaとMGEF Spellmaking Areaを17 feetへ、距離条件をPlayerRefから350ゲーム単位以下へ。Areaで条件の範囲を覆い、最終上限は距離条件で約5mとする。
3. 既存の探知対象条件へ `HasKeyword ActorTypeDaedra == 0` を追加。Skyrim.esmの `00013797` を参照する。NoDetectLife・死体・アンデッド・機械の除外は維持。
4. 説明文・マニフェストを同じ値へ更新。#E0C8B8、手元の光なし、呪文・エフェクト・シェーダーのFormIDは維持。

既存種族・Perk・NPC・標準魔法の上書き、他MODのINI/MCM変更、新規スクリプト・クエスト・SKSE DLLは不要。この方針は直接の競合を増やしにくいが、一般の魔法補正や入力処理との相互作用がなくなるわけではない。

威力・持続・通常の消費補正が変化しても、本MODの距離条件そのものを変更されなければ350という上限は残る。消費と違い、育成によって自動的に遠距離索敵へ発展するのを抑えられる点を重視する。

時刻・屋内条件を選ぶ場合も、xEditの標準条件にGetCurrentTime（18）とIsInInterior（300）が存在する。新しいタイマーを要する方式ではない。ただし条件文が書けることと、この探知の術者コンテキストで期待どおり働くことは別である。

以下は主案にしない：壁越し表示の解除やLOS条件の追加（探知の挙動が変わり確認が必要）、GetLightLevelだけによる暗さ判定（標準条件711は存在するがCabbageの画面上の暗さと同じとは限らない）、非戦闘限定だけの制限（先制索敵の強みが残る）、毎回固定の最低消費や60秒待ちの再導入（現在の単純な集中方式から設計が変わる）、色や視認不良を使った弱体化。

将来推奨案を制作する場合も、旧診断を再開したり全MODを順番に無効化したりする必要はない。変更差分の確認に加え、短い詠唱での実消費・近距離境界・デイドラ除外という変更点を確認すればよい。現在報告されているロード後の装備解除は、強度調整とは別の未解決項目として扱う。

## 参照資料

- 提供modlist SHA256: `f4d941ea48fe29eb0444ba3122161e61cda46a869df654663738558c8aa2d9c7`。plugins/loadorderのハッシュ・以前の実行時調査は [RUNTIME_INTERACTION_AUDIT.md](RUNTIME_INTERACTION_AUDIT.md)。原本は転載していない。
- 提供xEdit出力 `LKS-detection-records.txt` SHA256: `1714d09212226b3ed72ddaecd0c44375d0cebeb4eed86894a3fc5afc95fc7328`。Magic RedoneのSPEL 000211EEとMGEF 0001EA74等を参照。原本は転載していない。
- [現在の実装](../tools/build_concentration.py)、[集中版仕様](CONCENTRATION.md)。
- [GigaPlannerの対象版](https://github.com/watchis/Lorerim-GigaPlannerPlus/blob/7ff3a0c1ca53ab898e986260935ed2fbd7aba6c9/data/game/manifest.json)、[種族](https://github.com/watchis/Lorerim-GigaPlannerPlus/blob/7ff3a0c1ca53ab898e986260935ed2fbd7aba6c9/data/game/races.json)、[星座](https://github.com/watchis/Lorerim-GigaPlannerPlus/blob/7ff3a0c1ca53ab898e986260935ed2fbd7aba6c9/data/game/birthsigns.json)、[Traits](https://github.com/watchis/Lorerim-GigaPlannerPlus/blob/7ff3a0c1ca53ab898e986260935ed2fbd7aba6c9/data/game/traits.json)。いずれも5.0.4.2の補助資料。
- [隠密Perk](https://github.com/watchis/Lorerim-GigaPlannerPlus/blob/7ff3a0c1ca53ab898e986260935ed2fbd7aba6c9/data/game/perks/sneak.json)、[Wayfarer](https://github.com/watchis/Lorerim-GigaPlannerPlus/blob/7ff3a0c1ca53ab898e986260935ed2fbd7aba6c9/data/game/perks/wayfarer.json)、[Finesse](https://github.com/watchis/Lorerim-GigaPlannerPlus/blob/7ff3a0c1ca53ab898e986260935ed2fbd7aba6c9/data/game/perks/finesse.json)、[Destiny](https://github.com/watchis/Lorerim-GigaPlannerPlus/blob/7ff3a0c1ca53ab898e986260935ed2fbd7aba6c9/data/game/perks/destiny.json)、[変性](https://github.com/watchis/Lorerim-GigaPlannerPlus/blob/7ff3a0c1ca53ab898e986260935ed2fbd7aba6c9/data/game/perks/alteration.json)、[信仰](https://github.com/watchis/Lorerim-GigaPlannerPlus/blob/7ff3a0c1ca53ab898e986260935ed2fbd7aba6c9/data/game/deities.json)。
- [DLLTweaksの集中呪文判定](https://github.com/digital-apple/DLLTweaks/blob/b9a80a94f06decec61d42f500594360ce248db17/source/Hooks.cpp#L66)、[xEditの標準条件・レコードスキーマ](https://github.com/TES5Edit/TES5Edit/blob/9fb016884bec138ea6c7b872cec831537d464c3e/Core/wbDefinitionsTES5.pas)、[ENB Light Detection FixのAI照明への接続](https://github.com/clayne/ENBLightDetectionFix/blob/5473f99b6b1893ec8d81bafafcb8a633763ff5c0/src/ENBLightAffectsStealth.h#L89)。公開ソースと導入バイナリの全一致を確認したという意味ではない。
