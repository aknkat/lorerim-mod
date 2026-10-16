# 参照とビルドツール

ESPのレコード構造と定数は、以下の公開された実装に照合しています。ゲームデータ本体・公式スクリプト本体・これらのツールのバイナリをMO2用ZIPへ同梱していません。

- [xEdit / wbDefinitionsTES5.pas](https://github.com/TES5Edit/TES5Edit/blob/9fb016884bec138ea6c7b872cec831537d464c3e/Core/wbDefinitionsTES5.pas)：MGEF/SPEL/CTDA/VMADの構造、Detect Life archetype 19、条件関数の番号。
- [Mutagen](https://github.com/Mutagen-Modding/Mutagen)：ESP生成・独立した再読み込みに使用。NuGetの0.53.1とロックファイルを使う。
- [Mutagen.Bethesda.FormKeys.SkyrimSE](https://github.com/Mutagen-Modding/Mutagen.Bethesda.FormKeys/tree/650e147f854086b47b91ea80a881751466135256/Mutagen.Bethesda.FormKeys.SkyrimSE/Skyrim)：参照するKhajiitRace、KhajiitRaceVampire、ActorTypeUndead、ActorTypeDwarven、NoDetectLife、LifeDetectedEnemy、VoiceのFormID。PlayerRefは標準の参照FormID `00000014` を使用する。
- [Caprica v0.3.0](https://github.com/Orvid/Caprica/releases/tag/v0.3.0)：PapyrusをSkyrimのPEX 3.2 / Game ID 1へコンパイル。
- [Champollion v1.3.2](https://github.com/Orvid/Champollion/releases/tag/v1.3.2)：生成PEXの独立した読み込みとデコンパイル。
- [SKSE64公開リポジトリのvanillaスクリプト宣言](https://github.com/ianpatt/skse64/tree/master/scripts/vanilla)：Game.GetPlayer、Actor.GetRace、Spell.Cast、ActiveMagicEffect.OnEffectStartの**バニラAPIのシグネチャ**を確認するために使用。SKSEの拡張関数は使わない。

コンパイル用の最小API宣言は独自に記載したもので、ゲーム実行用の代替スクリプトではありません。

Caprica.exe SHA256：`389fef19a803c36342fa7f733c96b6e27ef10fcd0b171af10427e29cbe153ec6`

Champollion.exe SHA256：`450d9c74dade66331d573cfad881ef3e55384b5478e019af6d90a82378d1a1ec`

Capricaのオブジェクト長フィールドの補正は、[PexWriter.endObject](https://github.com/Orvid/Caprica/blob/master/Caprica/pex/PexWriter.h)が長さマーカーを直接書き込むことと、実出力の `ee010000`（little-endianで494、big-endianでは不正な長さ）を照合して行う。本文494に長さフィールド自身の4バイトを含め、補正後は `000001f2`（498）、命令本体は不変。長さ規則は [Mutagen PexObject](https://github.com/Mutagen-Modding/Mutagen/blob/414371eedc94a3e0c28f082180e0492df67ab8ca/Mutagen.Bethesda.Core/Pex/DataTypes/PexObject.cs) と照合し、NuGet 0.53.1のリーダーでも確認する。

公開CK Wikiはこの環境からHTTP 403となり参照できませんでした。v0.1.1はユーザー提供のSSEEditレコード出力を参照し、Areaによる範囲指定へ訂正しました。Area 27 feetと距離上限560 unitsの組合せを使い、実効半径は実機最終確認待ちです。

ユーザー提供の `LKS-detection-records.txt`（3494 loaded files）をデータとして参照。標準FF探知MGEF、Aura Whisperの最終定義と関連シェーダー、自作4レコードを比較した。出力全文は公開・同梱せず、必要な値と根拠を [RECORD_COMPARISON_0.1.1.md](RECORD_COMPARISON_0.1.1.md) にまとめた。
