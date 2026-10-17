# v0.1.4 diagnostic4：画面を塞がず発動経路を確認する

主能力800の直接Castは光らず、内部探知803の直接Castは光ったとの実機報告がある。diagnostic3の画像では、Quest running / Race allowed / Spell bound / TryActivate acceptedはいずれもTRUEで、保存期限も満了していた。ただしユーザーは発光をよく見ておらず、光らなかった気がするとの回答だった。発光は未確認であり、成功・失敗のどちらとも確定しない。

診断3は探知Castの後に数値画面を出すため、2秒間の発光が画面に隠れる欠点があった。**diagnostic4はダイアログを廃止し、画面を塞がない通知へ置き換える。** 本体の不発を修正した版ではない。発動条件・探知レコード・クールダウンの元の処理は変更しない。

## 導入と実行

1. ゲームを終了し、このZIPをMO2に**別MODとして**導入する。本体v0.1.4も有効にしたまま、左ペインで診断MODを本体より下へ置く。上書きするのは本MOD専用のPEX・PSC各2件だけ。
2. 以前の診断MODは無効化するか、**診断MODだけをReplace**する。本体は置き換えない。診断MODを複数有効にしない。
3. 完全終了・再起動後、問題の検証用セーブをロードする。付け外しや事前の発動確認を挟まず、通常画面で65秒待つ。
4. 近くの生きたNPCを見た状態で、選択済みの「鋭敏な感覚」を **Y＋RTで1回だけ**発動する。コンソールは使わない。通知とNPCの赤い発光を確認する。
5. 結果は「発光あり／なし」と、確認できた最後の通知だけでよい。通知は `LKS: INPUT`、続いて `LKS: ACCEPTED - cast requested` または `LKS: BLOCKED`。途中の異常は `LKS: ERROR ...` と表示する。INPUTが短くて見えなくても、最後の通知が出ればその内容を記録する。
6. 何も出ない／INPUTだけの場合も、その結果を記録する。追加の連打・付け外し・コマンドでの確認は挟まない。診断後はセーブせず終了する。

## 表示の意味

- `INPUT`：入力効果のOnEffectStartに入った。
- `ACCEPTED - cast requested`：元のTryActivateがTrueを返した。探知SPELのCast呼び出しは通過したが、描画成功を証明する戻り値ではない。
- `BLOCKED`：元のTryActivateがFalseを返した。クールダウン・種族・参照など、拒否理由は通知単体では区別しない。
- `ERROR ...`：PlayerRef、Controller参照、Quest開始、スクリプトのキャストのいずれかで中断した。

診断3の画面を見落とした確認を、そのままやり直す必要はない。診断4で結果を取る場合も1回の発動だけにする。今回の発光が見えれば探知描画まで動いたと分かるが、通常版のロード後不発の原因や修正成功まで証明するものではない。

## 保存状態と依存

**診断は現在と同じ制御を1回呼び、受理された場合は探知と通常のクールダウンを開始する。** 読み取りだけの診断ではない。本体のESP・レコード・コントローラーの元の全関数・保存変数とプロパティは変更しない。入力スクリプトのOnEffectStartを通知と診断呼び出し付きに差し替える。

新しい保存変数・タイマー・Wait・OnPlayerLoadGame・Alias・装備変更はない。Debug.Notification / Debug.TraceはバニラPapyrusで、追加のSKSE・DLLは必要ない。通知の処理時間の影響と、本体の保存状態への依存は残る。診断が終わったらゲーム終了後に**診断MODだけを無効化**すると、元の本体PEXへ戻る。本体の削除・Resetは不要。

詳細な数値はDebug.Traceにも出す。既存のPapyrusログが有効な環境では `LKS DIAG4` が目印になるが、今回の確認のためにINIを変更する必要はない。ログが無効でも画面の通知と探知は実行する。

## 制作・検査

`tools/build_diagnostic.py` は公開済みv0.1.4 ZIPのSHA256を固定し、そのPSCから診断用2スクリプトをstrictコンパイルする。保存レイアウト、コントローラーの元の全関数、入力の変更対象外の関数が同一であることを解析する。

実際のPEXで、コントローラー4ケースと、入力からの準備完了・待機中・別種族・未設定SPEL・未設定Controller・Quest開始失敗・別対象の7ケースを模擬実行する。通知内容とTrace、モーダル表示がないこと、余分なCast・更新登録がないことを確認する。Mutagenによる両PEXの読み込み、ZIPのCRC・SHA256・同梱パスを検査する。実機の入力・時計・描画を模擬実行の合格で保証するものではない。

通常ビルドと同じツール・Wine環境で実行する：

```text
python3 tools/build_diagnostic.py --dotnet /workspace/scratch/dotnet/dotnet --caprica /workspace/scratch/caprica-bin/Caprica.exe --wine /workspace/scratch/wine-root/usr/lib/wine/wine64
```

ソースZIPには本体PSC・診断生成コード・検査用ホストを含む。再ビルドにはリポジトリの `dist/KhajiitKeenSenses-0.1.4-MO2.zip` も必要。公開済みZIPは上書きしない。Skyrimの `cqf` 利用確認のないdiagnostic1/2の手順は撤回済み。
