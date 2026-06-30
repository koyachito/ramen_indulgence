# セキュリティ・品質レビュー 指摘事項

> **Phase 1 完了 — コードは一切変更していません。**  
> 各IDに承認 / 却下 / 保留 を記入して返送してください。承認されたIDのみ Phase 2 で修正します。

---

## サマリー

| 深刻度 | 件数 |
|--------|------|
| MEDIUM | 1    |
| LOW    | 4    |
| INFO   | 5    |
| **合計** | **10** |

---

## 指摘一覧

---

### F001 — Cookie ベースのレート制限が無効化できる

| 項目 | 内容 |
|------|------|
| **深刻度** | MEDIUM |
| **ファイル** | `app/rate_limit.py:11–17`, `app/main.py:116,168` |

**説明**  
`can_record()` はクッキーが存在しない場合に `True` を返す設計になっています。  
スクリプトからクッキーを送らずに `/result` や `/hidden-judgment` へ繰り返し POST すると、レート制限を完全にスキップして DB にレコードを書き続けられます。また、クッキーが存在していてもその値は平文の UNIX タイムスタンプ（例: `1751263200.12`）であり、クライアントが `0.0` に書き換えれば常に「最後の記録から 30 秒以上経過」と判定されます。

**影響**  
- 統計 DB に大量のフェイクレコードを挿入され、`/stats` の表示が汚染される  
- SQLite の 1 GB Persistent Disk を枯渇させる可能性がある（数十万件規模のスパム）

**修正方針**  
クッキー値を HMAC-SHA256 で署名し、改ざん検知を行う。または IP アドレスベースのサーバーサイドレート制限（`slowapi` 等）を追加する。署名キーは環境変数 `RATE_LIMIT_SECRET` で管理する。

---

### F002 — `.dockerignore` が存在しない

| 項目 | 内容 |
|------|------|
| **深刻度** | LOW |
| **ファイル** | `Dockerfile:8`（`COPY data ./data`） |

**説明**  
`.dockerignore` が存在しないため、ローカルで `docker build` を行う際に `data/ramen.db`（`.gitignore` 対象・53 KB の実 DB ファイル）がイメージに同梱されます。CI（GitHub Actions / Render）ではチェックアウト時に `.gitignore` 対象は存在しないため無害ですが、開発者がローカルビルドしたイメージをレジストリに push した場合、DB のデータが漏洩します。本アプリはゲーム統計のみで個人情報はありませんが、誤操作の余地があります。

**影響**  
ローカルビルドの Docker イメージに開発中の統計データが含まれる。

**修正方針**  
`.dockerignore` を追加して `data/*.db`, `backups/`, `.venv/`, `node_modules/`, `test-results/` などを除外する。

---

### F003 — Strict-Transport-Security (HSTS) ヘッダーが未設定

| 項目 | 内容 |
|------|------|
| **深刻度** | LOW |
| **ファイル** | `app/security_headers.py` |

**説明**  
`SecurityHeadersMiddleware` に `Strict-Transport-Security` ヘッダーが含まれていません。HTTPS への強制と中間者攻撃防止のためのベストプラクティスです。Render は CDN/プロキシレイヤーで HTTPS を強制しますが、アプリ側でも明示的に設定しておくことが望ましい。

**影響**  
HTTP でアクセスされた場合にブラウザが自動で HTTPS へリダイレクトしない（Render CDN 任せになる）。

**修正方針**  
`SECURITY_HEADERS` 辞書に `"Strict-Transport-Security": "max-age=31536000; includeSubDomains"` を追加する。

---

### F004 — CSP に `style-src 'unsafe-inline'` が含まれる

| 項目 | 内容 |
|------|------|
| **深刻度** | LOW |
| **ファイル** | `app/security_headers.py:7`, `app/templates/stats.html` |

**説明**  
`stats.html` でグラフバーの幅を `style="--width: {{ value }}%"` というインラインスタイルで指定しているため、CSP に `'unsafe-inline'` が必要になっています。`'unsafe-inline'` は XSS 攻撃時にインラインスタイルを使った任意コード実行（CSS インジェクション）の余地を残します。なお Jinja2 のオートエスケープ（`autoescape=True`）が有効なため、現状ではテンプレート変数経由の CSS インジェクションは発生しません。

**影響**  
将来的なテンプレート変更時に CSS インジェクションのリスクがある。CSP のスコアが下がる。

**修正方針**  
`stats.html` のインラインスタイルを CSS カスタムプロパティ + データ属性（`data-width="{{ value }}"`) に変更し、CSS 側で `[data-width]` を使用する。これにより `'unsafe-inline'` を CSP から削除できる。

---

### F005 — `start.sh` が `--reload` フラグで起動している

| 項目 | 内容 |
|------|------|
| **深刻度** | LOW |
| **ファイル** | `start.sh:11` |

**説明**  
`start.sh` の `uvicorn` 起動コマンドに `--reload` フラグが含まれています。`--reload` は開発用のファイルウォッチャーを起動し、CPU / ファイルディスクリプタを余分に消費します。Render は `runtime: docker` を使用するため本番では `Dockerfile` の `CMD` が使われますが、`start.sh` がステージング環境や CI で誤って使われた場合に問題になります。

**影響**  
不必要な CPU 使用と、ファイル変更による意図しないリロード。

**修正方針**  
`start.sh` から `--reload` を削除するか、`--reload` は `PORT` などの環境変数で制御するようにする。開発時は別途 `uvicorn ... --reload` を手動実行させる。

---

### F006 — `_date_context`（プライベート関数）が `__all__` に公開されている

| 項目 | 内容 |
|------|------|
| **深刻度** | INFO |
| **ファイル** | `app/diagnosis.py` |

**説明**  
`_date_context` はアンダースコアプレフィックスによりプライベート関数として命名されていますが、`from .result_generator import _date_context` でインポートされ `__all__` に列挙されています。APIの意図と命名が矛盾しています。

**影響**  
コードの可読性・保守性への影響のみ。セキュリティ影響なし。

**修正方針**  
`_date_context` を `__all__` から削除するか、関数名からアンダースコアプレフィックスを取り除く。

---

### F007 — `database_url()` が呼び出しごとに `os.getenv()` を再読み込みする

| 項目 | 内容 |
|------|------|
| **深刻度** | INFO |
| **ファイル** | `app/database.py:42–43` |

**説明**  
`database_url()` は `os.getenv("DATABASE_URL")` を毎回呼び出します。`init_db()` 内だけで 5 回呼ばれており、`_connect()` でも毎回呼ばれます。`os.getenv` のオーバーヘッド自体は軽微ですが、起動後に環境変数が変わらない前提であればモジュールレベルでキャッシュする方が意図が明確です。

**影響**  
微小なパフォーマンスオーバーヘッド。セキュリティ影響なし。

**修正方針**  
モジュール起動時に `_DATABASE_URL: str | None = os.getenv("DATABASE_URL")` として 1 度だけ読み込む。

---

### F008 — `/health` エンドポイントがタイムゾーンなし datetime を返す

| 項目 | 内容 |
|------|------|
| **深刻度** | INFO |
| **ファイル** | `app/main.py:231` |

**説明**  
`datetime.now().isoformat()` は naive datetime（タイムゾーン情報なし）を返します。`app/database.py` では `datetime.now(JAPAN_TIMEZONE)` を使用しており一貫性がありません。ヘルスチェックの返値が監視ツールによっては誤って解釈される可能性があります。

**影響**  
監視ツール連携時の軽微な誤解釈リスク。セキュリティ影響なし。

**修正方針**  
`datetime.now(timezone.utc).isoformat()` に変更して UTC タイムゾーン付きの ISO 8601 文字列を返す。

---

### F009 — `generate_result_text` の `result_type=None` デフォルトが使われていない

| 項目 | 内容 |
|------|------|
| **深刻度** | INFO |
| **ファイル** | `app/result_generator.py:99` |

**説明**  
`generate_result_text(data, scores, result_type=None, rng=None)` の `result_type` は実際には常に呼び出し元 (`app/main.py`) から明示的に渡されており、`None` のデフォルトが使われるパスは存在しません。`None` が渡された場合の動作が暗黙的になっています。

**影響**  
コードの可読性の問題のみ。

**修正方針**  
`result_type: str` として必須引数にするか、`None` 時の挙動を明示的にドキュメント化する。

---

### F010 — POST エンドポイントに CSRF トークンがない

| 項目 | 内容 |
|------|------|
| **深刻度** | INFO |
| **ファイル** | `app/main.py:69,166`, `app/templates/result.html`, `app/templates/hidden_confession.html` |

**説明**  
`/result` および `/hidden-judgment` への POST フォームに CSRF トークンがありません。ただし、本アプリはセッション管理・ログイン機能を持たないため、CSRF 攻撃で攻撃者が得られる利益は「統計カウントの水増し」に限られます（クロスオリジンリクエストはレスポンスを読めないため情報漏洩なし）。レート制限クッキーは `SameSite=Lax` で設定されているため、クロスサイトからのサブリソースリクエストにはクッキーが付きません（ただしトップレベルナビゲーション経由の GET は付く）。  
F001（レート制限バイパス）が修正されれば実質的な影響はさらに限定されます。

**影響**  
クロスサイトから POST を誘導することで統計カウントを水増しできる可能性がある（F001 と組み合わせた場合に顕在化）。

**修正方針**  
F001 のレート制限強化を先行して対応し、その後必要に応じて `itsdangerous` などを使った CSRF トークンを導入する。

---

## 問題なし（良好な実装）

以下は確認したが問題なし：

| 項目 | 状況 |
|------|------|
| SQL インジェクション | 全クエリでパラメータバインディング使用。DDL の `id_column` はハードコードされた定数のみ |
| XSS（テンプレート） | Jinja2 `autoescape=True` が確認済み。`\|safe` フィルター使用箇所なし |
| XSS（JavaScript） | DOM 操作は `textContent` のみ。`innerHTML` 使用なし。`CSS.escape()` 適切に使用 |
| ハードコード秘密情報 | `app/` 以下に SECRET / PASSWORD / API_KEY / TOKEN の記述なし |
| セキュリティヘッダー適用範囲 | `BaseHTTPMiddleware` は `/static/` を含む全リクエストに適用される |
| クッキーのセキュリティ属性 | `HttpOnly=True`, `SameSite=lax`, HTTPS 時 `Secure=True` が設定済み |
| 外部リンク | `target="_blank"` には全て `rel="noopener"` が付与済み |
| CORS | 未設定（デフォルト拒否）。外部 API 呼び出しなし |
| 依存パッケージ | Dependabot により週次で自動 PR。既知の CVE なし（確認済み） |
| 個人情報 | DB に記録されるのは時間帯・選択肢のみ。IP・UA・個人識別情報は記録されない |

---

## 承認欄

各 ID に対してコメントをお願いします。

| ID | 承認 / 却下 / 保留 | コメント |
|----|-------------------|----------|
| F001 | | |
| F002 | | |
| F003 | | |
| F004 | | |
| F005 | | |
| F006 | | |
| F007 | | |
| F008 | | |
| F009 | | |
| F010 | | |
