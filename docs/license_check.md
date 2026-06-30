# ライセンス確認

公開時点（2026-06-30）での確認結果。依存関係更新時に再確認すること。

## Pythonパッケージ（`requirements.txt`）

| パッケージ | バージョン | ライセンス | 備考 |
|-----------|-----------|-----------|------|
| fastapi | 0.115.12 | MIT | |
| uvicorn[standard] | 0.34.3 | BSD-3-Clause | |
| jinja2 | 3.1.6 | BSD-3-Clause | |
| python-multipart | 0.0.20 | Apache-2.0 | |
| anyio | 4.8.0 | MIT | |
| psycopg[binary] | 3.2.9 | LGPL-3.0 | PostgreSQL切り替え用。商用利用可 |

## Pythonパッケージ（`requirements-dev.txt`）

| パッケージ | バージョン | ライセンス | 備考 |
|-----------|-----------|-----------|------|
| pytest | 8.4.0 | MIT | テスト実行のみ、配布物に含まれない |
| httpx | 0.28.1 | BSD-3-Clause | テスト実行のみ、配布物に含まれない |
| Pillow | 11.2.1 | HPND（MIT互換） | テスト実行のみ、配布物に含まれない |

## JavaScript / E2Eテスト（`package.json`）

| パッケージ | ライセンス | 備考 |
|-----------|-----------|------|
| @playwright/test | Apache-2.0 | テスト実行のみ、配布物に含まれない |
| @axe-core/playwright | MPL-2.0 | テスト実行のみ、配布物に含まれない |

## GitHub Actions

| Action | ライセンス | 備考 |
|--------|-----------|------|
| actions/checkout@v6 | MIT | |
| actions/setup-python@v6 | MIT | |
| actions/setup-node@v4 | MIT | |

## 画像アセット（`app/static/images/`）

すべての画像はアプリ制作者（koyachito）がオリジナルで作成したもの。第三者素材を使用していない。

| ファイル | 作成元 |
|---------|--------|
| angry_eating.png, angry.png, banzai.png, eating.png | koyachito（オリジナル） |
| idea.png, menai.png, menyoku.png, ogreleft.png | koyachito（オリジナル） |
| ogre.png, prayer.png, suimin.png, thinking.png | koyachito（オリジナル） |
| thumbup.png, worry.png | koyachito（オリジナル） |

## フォント

外部フォントの読み込みなし。ブラウザ既定のシステムフォントを使用。

## まとめ

全依存パッケージはMIT / BSD / Apache-2.0 / LGPL-3.0 / HPND / MPL-2.0ライセンスであり、公開Webアプリとしての利用に問題なし。テスト専用パッケージは配布物に含まれないため、本番利用上の制約は特にない。
