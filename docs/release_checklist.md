# リリースチェックリスト対応状況

公開前に確認した項目と、対応済み・未対応の整理。

## 入力検証

| 項目 | 状態 |
|------|------|
| フォームの選択肢をサーバー側で検証 | ✅ 対応済み（`app/choices.py` の `VALID_CHOICE_VALUES` で一元管理） |
| 数値フィールドの範囲チェック | ✅ 対応済み（FastAPIのパラメータバリデーション） |
| 不正値はリダイレクト | ✅ 対応済み（`/diagnosis` へ303リダイレクト） |

## 個人情報

| 項目 | 状態 |
|------|------|
| ログインなし | ✅ 設計上対応済み |
| 個人を特定する情報を保存しない | ✅ 匿名の診断回答とスコアのみ保存 |
| 位置情報取得なし | ✅ 対応済み（Google Mapsリンクはユーザーが自分で開く） |

## DB保存とバックアップ

| 項目 | 状態 |
|------|------|
| SQLite統計ログ | ✅ 対応済み |
| DB書き込みエラーでも結果画面を返す | ✅ 対応済み（try/exceptで保護、ログに記録） |
| バックアップスクリプト | ✅ 対応済み（`scripts/backup_sqlite.py`） |
| バックアップ検証スクリプト | ✅ 対応済み（`scripts/verify_sqlite_backup.py`） |
| 自動バックアップ | ❌ 未対応（手動またはRender Shellでの実行） |

## レート制限・連投対策

| 項目 | 状態 |
|------|------|
| 連続診断での統計重複カウント抑制 | ✅ 対応済み（Cookieベースのレート制限、`app/rate_limit.py`） |
| Cookie設定（HttpOnly / SameSite） | ✅ 対応済み |

## セキュリティヘッダー

| 項目 | 状態 |
|------|------|
| `X-Content-Type-Options: nosniff` | ✅ 対応済み |
| `X-Frame-Options: DENY` | ✅ 対応済み |
| `Referrer-Policy: strict-origin-when-cross-origin` | ✅ 対応済み |
| `Permissions-Policy` （geolocation/camera/microphone無効） | ✅ 対応済み |
| `Content-Security-Policy` | ✅ 対応済み（`app/security_headers.py`） |

## テスト

| 項目 | 状態 |
|------|------|
| pytestによるサーバー処理・テンプレート確認 | ✅ 対応済み |
| セキュリティヘッダーのpytest確認 | ✅ 対応済み |
| DB書き込み失敗時の結果画面表示テスト | ✅ 対応済み |
| Playwright E2Eテスト（実ブラウザ） | ✅ 対応済み（`tests/e2e/diagnosis.spec.js`） |
| スマホ幅の主要導線テスト | ✅ 対応済み（PlaywrightのiPhone 14プロジェクト） |
| GitHub ActionsでのCI実行 | ✅ 対応済み |

## 依存関係管理

| 項目 | 状態 |
|------|------|
| Dependabotによる自動更新PR | ✅ 対応済み（`.github/dependabot.yml`） |
| Python依存関係の監視 | ✅ 対応済み（週次） |
| GitHub Actionsの監視 | ✅ 対応済み（週次） |

## アクセシビリティ

| 項目 | 状態 |
|------|------|
| 主要画面のaxe-core自動チェック（WCAG 2.0 A/AA） | ✅ 対応済み（Playwrightテストに組み込み） |
| 対象画面: `/`、`/diagnosis`、`/about` | ✅ 対応済み |
| 重大な違反がないこと | ✅ CI通過で継続確認 |

## 未対応・将来対応

- 自動バックアップのスケジュール実行（現在は手動のみ）
- 実機スマートフォンでの継続確認
- 免罪符画像のフォント・描画の端末差解消
- PostgreSQLへの移行（複数インスタンス化が必要になった段階）
- より細かいアクセシビリティ対応（現在は重大な違反なしを確認する水準）
