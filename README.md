# ラーメン免罪符

![Tests](https://github.com/koyachito/ramen_indulgence/actions/workflows/test.yml/badge.svg)

「今日ラーメンを食べてもよい理由がほしい」という欲望を、シスターとの事情聴取を通して審議するジョークWebアプリです。

## Demo

https://ramen-indulgence.onrender.com/

無料ホスティングのため、初回アクセス時に30〜60秒ほど起動に時間がかかる場合があります。

## 主な機能

- 1問ずつ進む、シスターのリアクション付き事情聴取
- 食事回数、今日の行動、気分、今後の予定などによるスコア判定
- 赦し・心配・怒り・鬼審議・「今日は寝ろ」の結果分岐
- 回答内容に沿った結果文のランダム生成
- 免罪符PNGの生成・画像共有とGoogle Maps検索URLの生成
- SQLiteまたはPostgreSQLによる匿名診断ログと統計
- 閲覧者の現在時間帯ごとのラーメン種類分布
- スマートフォン対応
- スクロール表示、発行演出、カウントアップなどのモーション
- デプロイ監視用 `/health` エンドポイント

ログイン、位置情報取得、個人を識別する情報の保存は行いません。診断回答と算出スコアは匿名の統計ログとして保存します。

## 技術スタック

- Python / FastAPI / Uvicorn
- Jinja2 / HTML / CSS / JavaScript
- SQLite（ローカル既定）/ PostgreSQL（`DATABASE_URL` 設定時）
- pytest

## ローカル起動

Python 3.11以降を推奨します。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

ブラウザで <http://127.0.0.1:8000> を開きます。

または、プロジェクト直下で次を実行します。

```bash
bash start.sh
```

リモート開発環境を使っている場合、ブラウザの `localhost` はサーバーと別環境です。
エディタの「Ports / ポート」画面で `8000` を転送し、表示された転送URLを開いてください。

## テスト

```bash
pytest
```

## Docker

```bash
docker build -t ramen-menzaifu .
docker run --rm -p 8000:8000 -v ramen-data:/app/data ramen-menzaifu
```
### データ保存について

ローカル環境および `DATABASE_URL` 未設定時は SQLite を使用します。  
Renderなどのホスティング環境では、再デプロイや再起動によりSQLite上の診断ログが失われる場合があります。

`DATABASE_URL` にPostgreSQLの接続URLを設定した場合は、PostgreSQLへ保存する構成に切り替わります。  
現在の公開版では、運用コストを抑えるためPostgreSQL常時運用は必須としていません。

## データベースと結果生成

通常は `data/ramen.db` のSQLiteを使います。Render PostgreSQLなどへ接続する場合は、接続文字列を `DATABASE_URL` に設定してください。起動時に必要なテーブルを作成します。

結果文は回答内容と矛盾しない候補からランダムに生成し、必ず「ラーメン。」で締めます。これは栄養・医療上の判断ではなく、入力を振り返って楽しむジョークです。

診断処理は責務ごとに分割しています。

- `app/choices.py`: 入力値、表示名、質問文、シスターのリアクション
- `app/diagnosis.py`: 診断処理の入口と既存公開API
- `app/scoring.py`: スコア計算と結果種別の判定
- `app/message_catalog.py`: 結果文・共有文の候補
- `app/result_generator.py`: 結果文と表示用データの生成
- `app/sharing.py`: 共有文、X投稿URL、Google Maps URLの生成

### 診断の入力項目

診断画面の選択肢は`app/choices.py`で一元管理しています。HTML、画面上のリアクション、サーバー検証はこの定義から生成され、スコア計算では同じ定数を参照します。

- `meals`: 今日の食事回数（0〜4）
- `ramen_count_today`: 今日食べたラーメン回数（0〜3、3食以上の場合のみ）
- `achievement`: 今日なしとげたこと
- `mood`: 今日の心の状態
- `after_plan`: この後の予定
- `reason_not_to_eat`: ラーメンを食べない理由
- `ramen_type`: 食べたいラーメンの系統
- `forgiveness_style`: 希望する赦され方

## 画面

- `/` トップページ
- `/diagnosis` 免罪審議フォーム
- `/result` 免罪符（POST）
- `/stats` 全体の判決統計
- `/about` アプリとプライバシー方針
- `/health` 稼働確認
