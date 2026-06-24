# Database policy

最終確認日: 2026年6月24日

## 現在の方針

公開版はRender Starter Web Service（$7/月）で動かし、SQLiteを継続します。診断ログを永続化するため、Render Persistent Diskを`/app/data`へマウントします。

この構成を選ぶ理由は次のとおりです。

- 現在のアプリは単一インスタンスで動作する小規模なポートフォリオアプリ
- 保存対象は匿名の診断ログと集計だけ
- SQLiteで必要な機能と性能を満たしている
- Persistent Diskは$0.25/GB/月で、別途有料PostgreSQLを運用するより小さく始められる
- 既存コードとローカル開発環境を変更せず、データ保存先だけを永続化できる

## Renderの設定

Render DashboardでWeb ServiceへPersistent Diskを追加します。

- Instance type: Starter
- Disk mount path: `/app/data`
- Disk size: 必要な最小容量
- SQLite path: `/app/data/ramen.db`

Dockerfileの`WORKDIR`は`/app`で、`RAMEN_DB_PATH`を`/app/data/ramen.db`に設定しています。そのため、`/app/data`へディスクをマウントすればDashboardで追加の環境変数を設定する必要はありません。

ローカル環境では引き続き`data/ramen.db`を使用します。別の保存先を使う場合は`RAMEN_DB_PATH`を設定できます。

リポジトリでは設定の不一致を防ぐため、次を追加しています。

- `Dockerfile`: `RAMEN_DB_PATH=/app/data/ramen.db`
- `render.yaml`: Starterプラン、`/app/data`への1GB Persistent Disk、`/health`のヘルスチェック

既存のRenderサービスがDashboardから作成されている場合、`render.yaml`を追加しただけでは既存設定は自動変更されません。Dashboardで同じマウント設定を適用するか、サービスをBlueprint管理へ移行する必要があります。

## Persistent Diskがない場合のリスク

有料Web Serviceでも、Persistent Diskを接続しなければファイルシステムは一時的です。SQLiteへ追加された診断ログは、再デプロイまたはサービス再起動時に失われます。

Persistent Diskは、マウントしたパス以下の変更だけを保持します。`/app/data`以外へSQLiteファイルを書き込んだ場合、そのファイルは永続化されません。

## Persistent Disk利用時の制約

- ディスクは1つのサービスインスタンスからのみ利用できる
- ディスク接続中は複数インスタンスへ水平スケールできない
- デプロイ時に旧インスタンスを停止してから新インスタンスを起動するため、数秒の停止が発生する
- 日次スナップショットはあるが、SQLiteの復旧手順は別途確認が必要

現在の規模では単一インスタンスと短時間のデプロイ停止を許容します。

## PostgreSQLへ移行する条件

PostgreSQLへの接続実装は`DATABASE_URL`で切り替えられる状態を維持しますが、現時点では移行しません。

次のいずれかが必要になった段階で、Render Postgresへの移行を再検討します。

- 複数インスタンスでサービスを実行する
- 書き込み量や同時接続数がSQLiteの運用範囲を超える
- DBをWeb Serviceから独立して管理したい
- より明確なバックアップ、復旧、監視が必要になる
- 診断統計以外の消失を許容できないデータを保存する

移行時には接続設定だけでなく、SQLiteからのデータ移行、バックアップ、リストア、スキーマ変更、障害時対応を合わせて整備します。

## 告知前の確認

- Render Web ServiceがStarterになっている
- Persistent Diskが`/app/data`へマウントされている
- 再デプロイ前後で統計件数が維持される
- Render Dashboardでディスク使用量とスナップショットを確認できる

## 参照した公式資料

- [Render: Persistent Disks](https://render.com/docs/disks)
- [Render: Pricing](https://render.com/pricing)
- [Render: Create and Connect to Render Postgres](https://render.com/docs/postgresql-creating-connecting)
