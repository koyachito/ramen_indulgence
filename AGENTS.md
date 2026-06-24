# Issue 作業フロー

GitHub Issue に着手するときは、次の手順を守る。

1. 現在のブランチと作業ツリーを確認する。
   - `git branch --show-current`
   - `git status --short`
2. 未コミットの変更がある場合は、新しい Issue の作業を開始しない。
   - 既存の変更を勝手に破棄、上書き、commit、stash しない。
   - 変更の扱いが不明な場合はユーザーに確認する。
3. 前の Issue のブランチから `main` に移動する。
   - `git switch main`
4. 前の Issue が `main` にマージ済みであることを確認し、前の Issue のブランチをローカルと GitHub から削除する。
   - マージ確認: `git merge-base --is-ancestor <前のブランチ名> main`
   - ローカル削除: `git branch -d <前のブランチ名>`
   - GitHub 削除: `git push origin --delete <前のブランチ名>`
   - マージされていないブランチを強制削除しない。
5. GitHub の最新版を取り込む。
   - `git pull --ff-only origin main`
6. Issue 専用の新しいブランチを作成して移動する。
   - ブランチ名は `issue-<番号>-<短い説明>` とする。
   - 例: `git switch -c issue-10-mobile-about-link`
7. Issue の要件を確認し、必要な変更だけを実装する。
8. Issue の完了条件に対応するテストと動作確認を行う。
9. ローカル確認用サーバーを起動し、ユーザーがブラウザで確認できる状態にする。
   - 原則として `./start.sh` を使用する。
   - 起動後に `http://127.0.0.1:8000/` へアクセスできることを確認する。
   - ユーザーへ確認URLを報告する。
10. 差分を確認し、Issue に関係するファイルだけを commit する。
11. 作業ブランチを GitHub に push する。
   - 初回: `git push -u origin <ブランチ名>`
   - 以降: `git push`
12. 実装内容、確認結果、push 先のブランチをユーザーへ報告する。
   - GitHub へ push した場合は、必ず Pull Request 作成用 URL も報告する。
   - URL 形式: `https://github.com/<owner>/<repository>/pull/new/<ブランチ名>`

## Git 操作上の注意

- `main` 上で直接実装しない。
- `git pull` は意図しないマージコミットを避けるため `--ff-only` を使う。
- ユーザーの既存変更や未追跡ファイルを、Issue の変更へ混ぜない。
- `git reset --hard`、`git checkout -- <file>`、無断の `git stash` は行わない。
- push 前にテスト結果と `git diff`、`git status` を確認する。
