# 『ビジネスオーナーの視座』公式付録：モート・トラッカー

本書『ビジネスオーナーの視座』（*THE BUSINESS OWNER'S PERSPECTIVE*）の付録Pythonスクリプトおよび検証用データのリポジトリです。

金融庁の EDINET API を活用し、企業の長期財務データ（ROE、DOE等）を取得・可視化して、企業の「経済的な堀（モート）」の形成・拡大軌跡を状態空間上にアニメーション描画します。

---

## リポジトリ構成

```text
business-owners-perspective/
├── appendix_moat_tracker.py   # 可視化スクリプト本体
├── requirements.txt           # 依存パッケージ一覧
├── LICENSE                    # MITライセンス
├── README.md                  # 英語版ドキュメント
├── README_ja.md               # 日本語版ドキュメント
├── data/                      # 【基準データ】精鋭16銘柄の過年度CSVキャッシュ
│   ├── moat_data_6857.csv     # アドバンテスト
│   ├── moat_data_8035.csv     # 東京エレクトロン
│   ├── moat_data_7011.csv     # 三菱重工業
│   └── ...（計16銘柄）
└── output/                    # 【生成物】描画されたHTMLやGIFの保存先

```

* **`data/`**：本書で取り上げた「精鋭16銘柄」の過去最大10年超〜14年程度分のキャッシュデータが同梱されています。EDINET APIキーをお持ちでない場合も、このデータを使用して即座に描画を実行できます。
* **`output/`**：スクリプト実行によって生成された HTML や GIF アニメーションが保存されます。

---

## クイックスタート（APIキー不要）

同梱されているデータを用い、半導体テスト装置で高いモートを誇る **アドバンテスト（6857）** の状態空間軌跡を描画する手順です。

### Step 1. Python環境の準備

Python 3.10以降がインストールされた環境でターミナル（Windowsは「Windows ターミナル」または「PowerShell」）を開き、仮想環境を構築して有効化します。

```bash
# リポジトリのクローンと移動
git clone https://github.com/12ncapital/business-owners-perspective.git
cd business-owners-perspective

# 仮想環境の作成
python3 -m venv .venv

# 仮想環境の有効化（Mac / Linux）
source .venv/bin/activate

# 仮想環境の有効化（Windows PowerShell）
.venv\Scripts\activate

```

### Step 2. 依存パッケージの導入

```bash
pip install -r requirements.txt

```

### Step 3. スクリプトの実行（オフライン動作）

引数にフォーカスしたい証券コード（`6857`）を指定して実行します。

```bash
# アドバンテスト（6857）をフォーカスして描画
python appendix_moat_tracker.py --focus 6857

```

実行が完了すると、`output/` フォルダ配下に以下のファイルが生成されます。

* `output/moat_animation_6857.html`（ブラウザで各プロットの数値を詳細確認できる動的グラフ）
* `output/moat_animation_6857.gif`（モートの拡大軌跡が時系列で再生されるアニメーション動画）

生成された `.html` ファイルを任意のWebブラウザ（Chrome、Safari、Edge等）で開くことで、インタラクティブな分析が可能です。

---

## 応用手順：任意銘柄の取得とデータ更新（APIキーが必要）

同梱の16銘柄以外の企業を分析する場合、または最新の本決算データを反映したい場合は、金融庁 EDINET API から直接データを取得します。

### 1. EDINET APIキーの設定

金融庁の「EDINET API仕様書」ウェブサイトより無料のアカウント登録を行い、APIキーを取得します。取得したキーは環境変数に設定するか、引数で渡します。

```bash
# Mac / Linux
export EDINET_API_KEY="あなたのAPIキー"

# Windows (PowerShell)
$env:EDINET_API_KEY="あなたのAPIキー"

```

### 2. 任意銘柄の解析実行

分析したい証券コード（例：トヨタ `7203`）を指定して実行すると、未取得の財務データを自動的にダウンロードし、可視化します。

```bash
# トヨタ（7203）を取得・解析
python appendix_moat_tracker.py --focus 7203

# 既存のキャッシュデータを破棄して最新の有報から再取得する場合
python appendix_moat_tracker.py --focus 7203 --force-update

# コマンドライン引数で直接キーを渡す場合
python appendix_moat_tracker.py --focus 7203 --api-key "あなたのAPIキー"

```

新しく取得した過年度データは `data/moat_data_xxxx.csv` として自動保存され、次回以降はオフラインで高速に読み込まれます。

---

## コマンドライン引数リファレンス

| オプション | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `--focus` | 文字列 | `7011` | アニメーションの主役として軌跡を強調描画する証券コード（--codes 指定時はその先頭銘柄） |
| `--codes` | 文字列 | 精鋭16銘柄 | 状態空間の比較母集団として背景プロットする銘柄群（カンマ区切り） |
| `--api-key` | 文字列 | なし | EDINET APIキー（環境変数 `EDINET_API_KEY` より優先） |
| `--force-update` | フラグ | オフ | ローカルキャッシュを無視し、EDINETから全年度の開示書類を再取得 |
| `--datadir` | パス | `data` | CSVキャッシュの保存および参照先フォルダ |
| `--outdir` | パス | `output` | 生成されるHTMLやGIFの保存先フォルダ |
| `--no-gif` | フラグ | オフ | GIFアニメーションの生成をスキップ（HTMLのみ高速出力） |
| `--no-html` | フラグ | オフ | HTMLの生成をスキップ（GIFのみ出力） |

---

## 免責事項（Disclaimer）

1. **投資判断について**: 本リポジトリで提供するスクリプト、データ、および分析ロジックは、情報提供およびプログラミングの学習を目的としたものであり、特定の有価証券の売買や投資の勧誘を目的としたものではありません。投資に関する最終的な決定は、ご自身の判断と責任において行っていただけますようお願いいたします。
2. **データの正確性**: 財務データはEDINET APIを通じて機械的に抽出・集計されたものであり、データの正確性、完全性、最新性を保証するものではありません。
3. **仕様変更**: 金融庁EDINET APIの仕様変更や将来の廃止等に伴い、本スクリプトが予告なく正常に動作しなくなる可能性があります。個別サポートや不具合修正の義務は負いかねますのであらかじめご了承ください。

---

## ライセンス

本プロジェクトは [MIT License](LICENSE) の下で公開されています。