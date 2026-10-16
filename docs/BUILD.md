# ビルド方法

実行環境に必要なのはPython 3.12以降、.NET SDK 8、Caprica v0.3.0です。これらは開発用で、MODの実行時依存ではありません。SDKソースを同梱したSkyrimゲーム本体はビルドに必要ありません。

## Windows

1. .NET SDK 8とPythonをインストールします。
2. [Caprica v0.3.0](https://github.com/Orvid/Caprica/releases/tag/v0.3.0) の公式アーカイブから `Caprica.exe` を展開します。
3. リポジトリのルートで実行します。

```powershell
python tools/build.py --caprica C:\Tools\Caprica\Caprica.exe
```

Windowsでのこのラッパーの実行は未検証です。生成・コンパイル・検査はこの制作環境のLinuxとWineで実行しています。

## このクラウド環境

既存の `/workspace/lorerim-mod` を使います。各クラウドタスクは隔離済みのため、指示がない限りGit worktreeを追加しません。ゲームを起動するサービスはありません。

```bash
cd /workspace/lorerim-mod
export DOTNET_CLI_HOME=/workspace/scratch/dotnet-home
export NUGET_PACKAGES=/workspace/scratch/nuget
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export WINEPREFIX=/workspace/scratch/wine-prefix
export WINESERVER=/workspace/scratch/wine-root/usr/lib/wine/wineserver64
export WINELOADER=/workspace/scratch/wine-root/usr/lib/wine/wine64
export WINEDLLPATH=/workspace/scratch/wine-root/usr/lib/x86_64-linux-gnu/wine
export LD_LIBRARY_PATH=/workspace/scratch/wine-root/usr/lib/x86_64-linux-gnu
export WINEDEBUG=-all
python3 tools/build.py \
  --dotnet /workspace/scratch/dotnet/dotnet \
  --caprica /workspace/scratch/caprica-bin/Caprica.exe \
  --wine /workspace/scratch/wine-root/usr/lib/wine/wine64
```

.NETの名前付きMutexとWineのローカルIPCは、制限されたサンドボックス内では拒否される場合があります。この環境では許可された実行経路でビルドします。

新しいマシンで `/workspace/scratch` のツールがない場合は、.NET SDKと公式Capricaを再導入してください。このパスの存在や、実行中のWineプロセスが復元されることを前提にしません。Wineはビルド時だけ必要で、ゲーム利用者への追加依存ではありません。

## 処理内容

- `dotnet restore --locked-mode` で `packages.lock.json` を維持します。
- Mutagen.Bethesda.Skyrim **0.53.1** でESPを生成し、生成後に再読み込みして新規5レコード、マスター、参照を検査します。
- Capricaを **`--game=skyrim --strict --all-warnings-as-errors`** で実行します。ソースディレクトリを作業ディレクトリにし、Skyrimに存在しない名前空間を付けません。Debug情報と独自言語拡張を使いません。
- 入力用とクエスト管理用の2スクリプトをコンパイルします。
- `tools/papyrus-api` は呼び出すバニラAPIだけのコンパイル用宣言です。これらのPSC/PEXをMODに導入しません。通常のCreation Kitのベースソースでも、必要なAPIとFlagsがあれば `--api-dir` で差し替えられます。
- Caprica v0.3.0のSkyrim出力には、オブジェクト長の4バイトだけがlittle-endianになる不具合があります。各ファイルの実際の本文長と一致することを確かめ、長さフィールド自身4バイトを含む値をSkyrimのbig-endianへ補正します。補正候補の全オブジェクト・命令・分岐を厳格に読み取れた場合だけ出力を採用します。
- 補正後のPEXをMutagenの独立したSkyrim PEXリーダーでも全体読み込みし、本文長だけを記録した旧形式を拒否します。
- PEXヘッダーのコンパイル時刻・ユーザー名・マシン名・ソースパスを固定します。上記の構造フィールドと非実行メタデータ以外、バイトコードは変更しません。
- 独立したPythonリーダーとユニットテストで出力ファイルを検査します。コンパイル済みPEXを模擬APIで実行し、入力条件、共有期限、再入力時の非更新、Native呼び出し中の再入、更新登録を失うロード、旧版のTrueフラグ・遅延イベント、時計の巻き戻りを検査します。演算は32bit Floatへ丸めます。公開済みv0.1.1の探知とv0.1.3の5レコード・入力PEXもハッシュで照合します。時計の進行と復元は模擬であり、ゲームエンジンの代替検証ではありません。
- 文書・マニフェスト・SHA256を `KhajiitKeenSenses/` 以下へまとめます。履歴用のprobe1/取得ツールの説明はMO2用ZIPに含めません。
- `package/` の生成内容だけを更新し、固定順序・固定ZIP時刻で `dist/KhajiitKeenSenses-0.1.4-MO2.zip` を作成します。
- ZIPのCRC、全ファイルのSHA256、MO2のDataルート構造、SDKスクリプトの混入がないことを検査します。
- 制作ソースだけの別ZIP `dist/KhajiitKeenSenses-0.1.4-source.zip` も作成し、CRCとSHA256を検査します。ビルド用API宣言はこちらにだけ含みます。

コード・レコードを変更した場合はESPとPEXを再ビルドします。ゲームで使うのは `dist/` のZIPです。生成された `package/` を手作業で変更しても、次回ビルドで保持されません。

## 個別検査

```bash
python3 -m unittest discover -s tests -v
python3 tools/verify_archive.py dist/KhajiitKeenSenses-0.1.4-MO2.zip
```

PEXは独立した [Champollion v1.3.2](https://github.com/Orvid/Champollion/releases/tag/v1.3.2) でもデコンパイルし、元のイベントの意味と照合します。正式なゲーム検査はMO2経由のSSEEditとゲーム内で行います。
