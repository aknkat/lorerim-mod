# LoreRim ロード画面用パッチ

## 最新：指定画像への変更 0.1.1 WQHD

[0.1.1 WQHD MO2導入用ZIPをダウンロード](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/loading-screen-mod/dist/LoreRim_TESL_Skyrim_Coverage_Patch-0.1.1-WQHD-MO2.zip)

差し替え先は「雪山を望む猫人の旅人 (1).png」。元画像1672×941の全体を収めたまま2560×1440へ拡大し、DXT5 DDSに変換しました。WQHDは出力サイズであり、元画像以上の細部を保証しません。

0.1.0からは画像DDSだけを変更しています（説明・チェックサム・画像変換記録を除く）。NIF 110個は前版とバイト単位で同一です。共通DDSパスを使うため、元のEchoes差し替え側にも新画像が適用されます。メインメニュー設定、ESP、スクリプト、DLL、INIは変更しません。

0.1.0を導入済みなら、その追加パッチMODだけを本ZIPでReplaceするか、旧パッチを無効化して新版を別MODとして導入してください。元のEchoes差し替え・TESL本体・Fully IsolatedへMerge/Replaceしないでください。新版がDDSと110個のNIFの競合勝者になるよう配置します。

DDS寸法・DXT5データ長・再復号・圧縮誤差・ZIP CRC・全メンバーSHA256・NIF不変性を検査済み。**Skyrim実機未検証、全ロード画面経路の修正や実機の全画面描画は未確認です。** 0.1.0は履歴として保持しています。


既存の他MODとは分けた、ロード画面MOD専用フォルダです。

## TESL画像差し替え範囲の補完 0.1.0

[MO2導入用ZIPをダウンロード](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/loading-screen-mod/dist/LoreRim_TESL_Skyrim_Coverage_Patch-0.1.0-MO2.zip)

**実機未検証の部分修正版です。全ロード画面の完全統一や、元画像の出典の確定を意味しません。**

受領したEchoes差し替えZIPはEchoes本体の300モデルを覆っていますが、TESL本体の110モデルは含んでいませんでした。このパッチはTESLの110パスへ既存差し替えの表示用NIFを配置し、同じSkyrim画像DDSを同梱します。DDSだけの差し替えではなく、NIFの形状・材質設定も置き換えます。元テンプレートと画像のバイト列は変更していません。

MO2へ新規の別MODとして導入し、TESL本体・既存Echoes差し替え・Fully Isolatedより高い優先度にしてください。既存MODへMerge/Replaceしないでください。ESP順序の変更は不要です。元MODのディスク上のファイルは変更しません。

ESP・スクリプト・DLL・INI・メインメニュー用ファイルは含みません。共通画像DDSは既存Echoes差し替えと同名・同一内容です。メインメニュー側MODに残るロード画面ファイルと、MO2の実際の競合勝者は未確認です。

検査済み：TESLのLSCR→STAT→NIF参照110件の網羅、ZIP CRC、全メンバーSHA256、元NIF/DDSとのバイト一致。16:9の最終表示は実機で確認が必要です。問題があれば追加したパッチのみ無効化してください。

ZIP内部のREADMEに導入・確認事項とSHA256SUMSを同梱しています。
