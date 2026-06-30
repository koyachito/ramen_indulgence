# 運用ランブック

公開後の確認・障害対応手順。高度な監視・自動アラートは現時点では導入しない。

## 公開前チェック

- [ ] Render DashboardでService Planが意図したもの（Starter以上）であること
- [ ] Persistent Diskが `/app/data` にマウントされていること
- [ ] 環境変数 `RAMEN_DB_PATH=/app/data/ramen.db` が設定されていること
- [ ] `/health` が `{"status": "ok"}` を返すこと
- [ ] `/` が表示されること
- [ ] 診断を1件通してPOSTし、`/stats` のカウントが増えること

## 告知直後の確認（公開直後10分以内）

1. `/health` を叩いて `200 OK` を確認する
2. 自分で診断を1件完走する
3. `/stats` でカウントが増えていること
4. Render Logsに `ERROR` や `Exception` が出ていないこと

## 定期確認項目

### Render Dashboardで見るもの

- **Service Status**: Running であること
- **Billing**: 月次コスト・使用量が想定内であること
- **Persistent Disk**: マウント状態・使用容量

### ログ（Render Logs）

- `uvicorn.error` に `Exception` が出ていないか
- 統計書き込み失敗（`record_result failed` / `record_judgment failed`）がないか
- `get_stats failed` が出ていないか（出た場合は `/stats` が `0件` 表示になる）

## 障害別の確認先

### 統計が0件・消えた場合

1. Render DashboardでPersistent Diskのマウント状態を確認する
2. `RAMEN_DB_PATH` 環境変数が `/app/data/ramen.db` に設定されているか確認する
3. Render Shellで `ls -la /app/data/` を実行してファイルの存在を確認する
4. バックアップがあれば `scripts/verify_sqlite_backup.py` で整合性を確認する

### 診断結果が表示されない場合

1. Render Logsでエラーを確認する
2. `/health` が応答するか確認する（応答しない場合はサービス停止）
3. DB書き込みエラーの場合でも結果画面は表示されるはず（try/exceptで保護済み）

### 静的ファイルが反映されない場合

1. Renderで手動デプロイを実行する
2. ブラウザのキャッシュをクリアする
3. `?v=` バージョン文字列が更新されているか確認する

### 初回アクセスが遅い場合

無料プランではスリープ後の初回アクセスに30〜60秒かかる。有料Starterプランでも起動に数秒かかることがある。これはホスティング仕様であり、アプリ側の問題ではない。

## バックアップ手順

Render Shellから実行:

```bash
python scripts/backup_sqlite.py --source /app/data/ramen.db --backup-dir /app/data/backups
python scripts/verify_sqlite_backup.py /app/data/backups/ramen-YYYYMMDD-HHMMSS.db
```

バックアップファイルは `/app/data/backups/` に保存される（Persistent Disk上）。

## SQLite → PostgreSQL移行条件

複数インスタンス化、書き込み量の増加、高度なバックアップ・復旧が必要になった段階で検討。詳細は [`docs/database_policy.md`](database_policy.md) を参照。
