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

## Architecture

サーバー側で入力検証・スコア計算・結果生成・統計記録を行い、Jinja2でHTMLを返す構成です。ブラウザ側のJavaScriptは質問フロー、表示演出、Canvas画像生成など、画面内で完結する処理を担当します。

```text
Browser
  ├─ Jinja2 templates
  └─ ES Modules (question flow / animation / Canvas)
          │
          ▼
FastAPI routes (app/main.py)
  ├─ choice definitions and validation (app/choices.py)
  ├─ scoring and result selection (app/scoring.py)
  ├─ result text generation (app/result_generator.py)
  ├─ share URL generation (app/sharing.py)
  └─ anonymous statistics (app/database.py)
          │
          ▼
SQLite or PostgreSQL
```

主な設計方針は次のとおりです。

- 診断の選択肢、表示名、質問文、リアクション、検証値を`app/choices.py`へ集約する
- スコア計算とランダムな結果文生成を分離し、判定結果が文言選択に影響されないようにする
- `app/diagnosis.py`は診断処理の入口と既存公開APIに限定する
- フロントエンドは`app/static/script.js`を入口とするES Modulesへ責務別に分割する
- データベース層でSQLiteとPostgreSQLの接続差を吸収する
- 外部挙動を保護するpytestを、GitHub ActionsでPRと`main`へのpush時に実行する

## Development process

1. 小さなMVPとしてVer0.1を実装し、Renderへ公開
2. 友人9人に実際に操作してもらい、感想を`feedback.md`へ整理
3. フィードバックを質問フロー、判定、文言、共有、統計などの課題へ分解
4. Issueごとにブランチを分け、受け入れ条件を確認しながら実装
5. pytest、Pythonコンパイル、JavaScript構文、差分を確認
6. PRで変更を確認してから`main`へマージ

初期仕様からVer1.0までの変更理由は[`docs/spec_evolution_v0.1_to_v1.0.md`](docs/spec_evolution_v0.1_to_v1.0.md)に記録しています。

## AI-assisted development

ChatGPTとCodexを、思考の外部化、実装補助、レビューに利用しています。完成品を一括生成させるのではなく、既存コード、Issue、テスト、利用者フィードバックを前提に、変更を小さく分けて進めました。

AIが支援した範囲：

- 仕様案や代替案の整理
- FastAPI、Jinja2、JavaScript、DB実装の変更
- リファクタリング案の作成と複数ファイルへの反映
- テスト追加、構文検査、差分確認
- READMEや設計資料の整理

開発者自身が担当した範囲：

- アプリの企画と世界観
- MVPと各バージョンのスコープ決定
- デプロイと友人9人への試用依頼
- フィードバックの収集、分類、優先順位付け
- AIが提示した案の採用、修正、撤回
- 最終的なUX、文言、判定条件の決定

具体的な利用方法と反省点は[`docs/ai_development_retrospective.md`](docs/ai_development_retrospective.md)に記載しています。

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

ローカル環境および`DATABASE_URL`未設定時はSQLiteを使用します。

現在の公開版はRender Starter Web Service（$7/月）でSQLiteを使用し、`/app/data`へPersistent Diskをマウントして診断ログを永続化する方針です。Dockerfileの`RAMEN_DB_PATH`と[`render.yaml`](render.yaml)のマウント設定を`/app/data/ramen.db`へ統一しています。

`render.yaml`は新規Blueprintや設定確認に利用できます。既存のRenderサービスがDashboardから作成されている場合、ファイルを追加しただけでは設定は変更されないため、Dashboardでもディスクが`/app/data`へ接続されていることを告知前に確認します。

有料Web ServiceでもPersistent Diskを接続しなければファイルシステムは一時的であり、再デプロイや再起動時にSQLiteのデータが失われます。

Persistent Diskは1サービスインスタンス専用で、接続中は水平スケールとゼロダウンタイムデプロイを利用できません。現在の小規模・単一インスタンス構成では、この制約を許容します。

`DATABASE_URL`にPostgreSQLの接続URLを設定した場合はPostgreSQLへ切り替えられますが、現時点では移行しません。複数インスタンス化、書き込み量の増加、より高度なバックアップ・復旧が必要になった段階で再検討します。

判断理由と移行条件は[`docs/database_policy.md`](docs/database_policy.md)に記録しています。

## データベースと結果生成

通常は `data/ramen.db` のSQLiteを使います。Render PostgreSQLなどへ接続する場合は、接続文字列を `DATABASE_URL` に設定してください。起動時に必要なテーブルを作成します。

結果文は回答内容と矛盾しない候補からランダムに生成し、必ず「ラーメン。」で締めます。これは栄養・医療上の判断ではなく、入力を振り返って楽しむジョークです。

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

## Known limitations

- ログイン機能はなく、個人ごとの診断履歴や端末間同期には対応していません。
- SQLiteの永続化はRender DashboardでPersistent Diskを`/app/data`へ接続する外部設定に依存します。未接続やマウント先の誤りがあると、再デプロイ・再起動時に統計が失われます。
- Persistent Disk利用中は単一インスタンスに限定され、デプロイ時に数秒の停止が発生します。
- PostgreSQL接続コードはありますが、複数インスタンス化や高度なDB運用が必要になるまで移行しません。
- 統計画面の時間帯判定は、現在サーバーまたは閲覧環境の時刻に依存し、日本時間へ固定されていません。
- 自動テストはPython処理と生成HTMLの確認が中心で、実ブラウザを使ったE2Eテストや複数スマートフォン実機での継続検証は未導入です。
- 免罪符画像はブラウザのCanvasで生成するため、フォントや描画結果に端末差が出る場合があります。
- XのWeb Intentではローカル生成画像を自動添付できないため、画像保存と投稿操作を分けています。
- 無料ホスティングでは、スリープ後の初回アクセスに30〜60秒程度かかる場合があります。

## Future work

- Persistent Disk上のSQLiteについて、バックアップと復旧手順を実地確認する
- 複数インスタンス化やDB負荷増加が必要になった段階でPostgreSQLへ移行する
- 統計の時間帯判定を日本時間基準に統一する
- Playwrightなどによる診断完走・画像保存のブラウザE2Eテストを追加する
- スマートフォン実機でナビゲーション、診断フロー、結果画面を継続確認する
- 結果画面と免罪符画像のデザイン、アクセシビリティを改善する
- 離脱した質問、画像保存率、再診断率などを個人を識別しない形で検証する
- 重要な仕様変更と撤回理由をIssueやADRへ残す

## 画面

- `/` トップページ
- `/diagnosis` 免罪審議フォーム
- `/result` 免罪符（POST）
- `/stats` 全体の判決統計
- `/about` アプリとプライバシー方針
- `/health` 稼働確認
