# Repository Working Agreement

このファイルは、このリポジトリで作業するエージェントが必ず守る作業指針です。

## Issue作業の開始手順

新しいIssueへ着手する前に、必ず次の順番で操作します。

1. `git status --short --branch`で作業ツリーを確認する。
2. ユーザーの未コミット・未追跡ファイルを勝手に変更、削除、コミットしない。
3. 前のIssueがGitHub上でマージ済みであることを確認する。
4. `main`へ移動する。
5. `git pull --ff-only origin main`で最新の変更を取得する。
6. マージ済みの前Issue用ローカルブランチを`git branch -d <branch>`で削除する。
7. 更新済みの`main`から、新しいIssue専用ブランチを作成する。

```bash
git switch main
git pull --ff-only origin main
git branch -d issue-<previous-number>-<description>
git switch -c issue-<number>-<description>
```

前のIssueブランチを基点に次のIssueブランチを作ってはいけません。Issue間に明示的な依存関係がある場合でも、依存する変更が`main`へマージされた後に最新の`main`から作成します。

## Issueごとの作業ルール

- 1ブランチでは1つのIssueだけを扱う。
- 実装前にIssue本文と現在の`main`のコード構成を確認する。
- 過去Issueの変更が`main`へ正しく反映されているか確認してから編集する。
- リファクタリング後の構成を無視して、古いファイルへ変更を加えない。
- コミットには対象Issueのファイルだけを含める。
- ユーザーが作成した無関係な差分は、ステージ済みでもコミットから除外する。

## 完了確認

Issue完了前に、少なくとも次を実行します。

```bash
pytest
python -m compileall -q app tests
git diff --check
git status --short --branch
```

- Issueの受け入れ条件をテストまたは具体的な確認結果で検証する。
- 関連する既存テストを含む全テストを実行する。
- Issue対応分をコミットし、コミットIDを報告する。
- push、PR作成、マージはそれぞれ別の状態として明確に報告する。
- PRを作成していない場合や、マージしていない場合は、その事実を明記する。

## マージ後

Issueがマージされたら、次のIssueへ進む前に再び「Issue作業の開始手順」を最初から実行します。
