# LoreRim ロード画面用パッチ

既存の他MODとは分けた、ロード画面MOD専用フォルダです。

## TESL画像差し替え範囲の補完 0.1.0

[MO2導入用ZIPをダウンロード](https://github.com/aknkat/lorerim-mod/raw/refs/heads/main/loading-screen-mod/dist/LoreRim_TESL_Skyrim_Coverage_Patch-0.1.0-MO2.zip)

**実機未検証の部分修正版です。全ロード画面の完全統一や、元画像の出典の確定を意味しません。**

受領したEchoes差し替えZIPはEchoes本体の300モデルを覆っていますが、TESL本体の110モデルは含んでいませんでした。このパッチはTESLの110パスへ既存差し替えの表示用NIFを配置し、同じSkyrim画像DDSを同梱します。DDSだけの差し替えではなく、NIFの形状・材質設定も置き換えます。元テンプレートと画像のバイト列は変更していません。

MO2へ新規の別MODとして導入し、TESL本体・既存Echoes差し替え・Fully Isolatedより高い優先度にしてください。既存MODへMerge/Replaceしないでください。ESP順序の変更は不要です。元MODのディスク上のファイルは変更しません。

ESP・スクリプト・DLL・INI・メインメニュー用ファイルは含みません。共通画像DDSは既存Echoes差し替えと同名・同一内容です。メインメニュー側MODに残るロード画面ファイルと、MO2の実際の競合勝者は未確認です。

検査済み：TESLのLSCR→STAT→NIF参照110件の網羅、ZIP CRC、全メンバーSHA256、元NIF/DDSとのバイト一致。16:9の最終表示は実機で確認が必要です。問題があれば追加したパッチのみ無効化してください。

ZIP内部のREADMEに導入・確認事項とSHA256SUMSを同梱しています。
