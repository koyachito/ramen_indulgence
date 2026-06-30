# ラーメン免罪符 開発全プロセス記録 — 人間とAIの分担（時系列）

このドキュメントは、「ラーメン免罪符」の開発全体を時系列で追い、**どの作業を人間（koyachito）が担い、どの作業をどのAIが担ったか**を省略せず記録するものである。

データソースは以下を突き合わせた。

- GitHub リポジトリ `koyachito/ramen_indulgence` の全コミット履歴
- 全 Pull Request（#1〜#57）
- 全 Issue（#2〜#44）
- リポジトリ内ドキュメント（`feedback.md` / `AGENTS.md` / `findings.md` / `docs/` 各種）

> 表記ルール
> - 確認できない箇所は **（推測）** と明記する。
> - 日時は原則 JST（日本標準時）。GitHub上のマージコミットは作者タイムゾーンが -0600 で記録されているものがあるが、内容の前後関係はコミット時刻で判断した。

> **大前提：人間はコードを一行も書いていない。**
> アプリのコード・テスト・設定・ドキュメントの**実テキストはすべてAI（ChatGPT / Codex / Claude Code）が生成**した。
> コミットの作者名はすべて `koyachito`（および Dependabot）だが、これは人間が commit/push 操作を行っただけで、**コードの執筆者ではない**。
> 人間が担ったのは具体的には次である。
> - **世界観と赦しの文言を決める**（シスターとの懺悔・免罪という設定、核となる「赦しの言葉」）
> - **どうすれば面白くなるかの方向づけ**と**仕様の最終決定**（採用・撤回）
> - **画面の微調整指示**（コピーの大きさ・配置・リアクション秒数など、AIへの具体指示）
> - **個人情報をどこまで取るかの決定**（ログイン・位置情報・個人識別を保存しない方針）
> - **友人の声をAIと壁打ちしつつ最終的に判断する**こと（フィードバックの収集・取捨選択）
> - デプロイ操作、ユーザーテストの実施、push前の品質確認、Git/PR操作
>
> 要するに人間は「**書く人**」ではなく「**決める人・方向づける人・確かめる人**」だった。

> **Issueも人間は書いていない。**
> GitHub Issue の**本文・「やること」「確認」チェックリスト（受け入れ条件）は ChatGPT が作成（＝切ってもらった）**。Claude Code が実装した Issue #36〜#44 も含め、Issue の設計は ChatGPT。
> さらに、**各 Issue が完了条件を満たしているかの照合チェックも ChatGPT** が行った。
> 人間は ChatGPT が作った Issue を GitHub に起票し、優先順位を決め、最終的に PR をマージしただけである。

---

## 0. 使ったAIと役割（サマリ）

| フェーズ | 期間 | 使ったAI | AIの主な役割 |
|----------|------|----------|--------------|
| 企画・仕様壁打ち | 〜2026-06-21 | **ChatGPT** | アイデアの言語化・複数案の比較（採用判断は人間） |
| Issue設計・完了条件チェック | 全期間（〜06-30） | **ChatGPT** | 全Issueの本文・受け入れ条件の作成、各Issueの達成確認 |
| Ver0.1 実装 | 2026-06-21〜06-22 | **Codex** | MVPのコードを全て生成 |
| Ver1.0 体験再設計・リファクタ | 2026-06-22〜06-25 | **Codex** | 既存コードへの変更・テスト更新・ドキュメント生成 |
| 残りIssue一括実装・QA | 2026-06-30 | **Claude Code** | ブランチ/PR管理・E2E・7ペルソナQAの実装と実行 |
| セキュリティレビュー | 2026-06-30 | **Claude Code** | 調査→承認→修正の2段階フロー |
| ドキュメント整備 | 2026-06-30 | **Claude Code** | 振り返り・学び・本資料の執筆 |

各AIは「丸投げ先」ではなく、役割の異なる補助者として使われた。**コードはすべてAIが書いたが、何を作るか・どの案を採用するか・どこで止めるかの最終判断は一貫して人間が持った。**

### 1Issueあたりのライフサイクル（だれが何をしたか）

`#2`〜`#44` のすべてのIssueは、おおむね次の分担で回した。

1. **【ChatGPT】** Issue本文と「やること」「確認（受け入れ条件）」のチェックリストを作成（＝Issueを切る）。
2. **【人間】** ChatGPTが作ったIssueをGitHubに起票し、優先順位を決める。
3. **【Codex（〜06-25）／Claude Code（06-30）】** ブランチを切ってコードを実装し、テストを追加・実行。
4. **【ChatGPT】** 各Issueの「確認」条件を満たしているかを照合チェック。
5. **【人間】** ブラウザ／スマホで実動作を確認し、PRをマージ。

→ つまり **Issueの設計・受け入れ判定は ChatGPT、コード実装は Codex / Claude Code、最終承認とマージ操作・実機確認が人間**、という三者分業だった。

---

## フェーズ 0 — 企画と仕様壁打ち（ChatGPT）｜〜2026-06-21

※ このフェーズはコミット以前の作業であり、`docs/ai_development_retrospective.md` と `docs/ai_collaboration_learnings.md` の記述、および `docs/archive/initial_spec.md` 等の資料を根拠とする。具体的なやり取り日時はリポジトリに残っていないため、一部は（推測）。

- **【人間】** 「今日ラーメンを食べてよい理由が欲しい」という着想から、*シスターとの懺悔と免罪判決* というアプリ企画を決定した。
- **【人間】** ネタアプリとセルフケアの中間という体験コンセプト、MVPで実装する範囲を決めた。
- **【人間】** **アプリの世界観（シスターとの懺悔・免罪という設定）と、赦しの文言は人間が決めた。** ChatGPTはリアクション文や結果文の候補を出したが、世界観の核と最終的な「赦しの言葉」は人間が作った／選んだ。
- **【ChatGPT】** 以下を壁打ち相手として言語化・複数案出しした（採否は人間）。
  - 質問項目の候補
  - 「今日成し遂げたこと」の肯定的／おふざけ選択肢
  - シスターのリアクション文の候補（※最終的な赦しの文言・世界観は人間が決定）
  - 結果文の構造
  - 同じ入力でも変化を出す方法、ランダム要素の是非
  - X共有導線の現実的な構成、隠し結果の見せ方
  - ポートフォリオとして何を説明できるか
- **【人間】** ChatGPTが出した複数案を比較し、MVPに入れる仕様だけを取捨選択した。
- **（推測）【人間】** `docs/archive/initial_spec.md`（「ラーメン免罪符：現時点の仕様まとめ」）は、**文体・体裁から人間が手で書いた初期仕様メモ**と見られる。Markdown見出しを使わない素の箇条書きで、「ガチ健康管理アプリではなく」「42Tokyo／オタク・ネット文化圏にも刺さる」など砕けた自己フレーミングが残る。ChatGPTとの壁打ち内容を人間が自分の言葉でまとめたもの（推測）。

---

## フェーズ 1 — Ver0.1（MVP）の実装と公開（Codex）｜2026-06-21〜06-22

### 実装（コードはすべてCodex）
- **【Codex】** Ver0.1 のコードを全て生成。FastAPI + Jinja2 + JavaScript + CSS + SQLite で、診断入力・サーバー側スコア計算・結果表示・Canvas画像生成・X共有導線・Google Maps検索URL・匿名統計までを実装した。
- 関連コミット（2026-06-21、commit 操作は人間、**実コードはCodex**）:
  - `ad52865 first` — 初期実装
  - `edace2a button` / `b8ec6f4 hidden` / `4d41e88 redirect` — UI調整
  - `63211a9` / `596b710` — README（デモリンク・ホスティング記載）
- **【人間】** `PR #1 "version1.0"` を作成しマージ（`b5c0079`, 2026-06-21）。
- 2026-06-22: `1d08521 ver1` → `230e4ef fix: pin Python version for Render deploy` → `b54f6a5 arrange docs`。
  - **【Codex】** Render デプロイのための Python バージョン固定（デプロイ失敗を受けた修正＝推測）。**【人間】** がデプロイを実行しエラーを観測して指示。

### 公開とユーザーテスト（人間）
- **【人間】** Ver0.1 を Render へデプロイ（https://ramen-indulgence.onrender.com/ ）。**完成を待たずにMVPを公開した**のがこのプロジェクトの核心的判断。
- **【人間】** 友人に実際に触ってもらい、フィードバックを収集した（**最終的に11人**がチェック。当初は9人、後に追加で増えた）。
- **【人間】** 受け取った感想を `feedback.md`（2026-06-22 06:52）へ整理・構造化した（コードではなく仕様メモ）。
  - 結果画面／質問画面／全般に分類し、指針と具体指示を分け、Phase 1/2/3 の優先度を付けた。
  - **`feedback.md` の上部（「指針」など冒頭部分）は人間が自分の手で書いた。** これはこのプロジェクトで人間が手書きした数少ないテキストである。
  - **このフィードバックの収集・分類は人間の作業**（口頭の感想 → AIへ渡せる仕様資料への変換）。

---

## フェーズ 2 — Ver1.0 体験再設計 & リファクタリング（Codex）｜2026-06-22〜06-25

このフェーズから **GitHub Issue 駆動**の開発に移行。**Issue本文はChatGPTが作成**、人間がGitHubに起票・優先順位付け・ブランチ/PR操作・マージ・テスト実行を手動で行い、**コードはすべてCodexが生成**、**完了条件のチェックはChatGPT**が担当した（`docs/ai_collaboration_learnings.md` の比較表＋本人の証言より）。

### CI 整備
- **【ChatGPT】** Issue **#2** "Add GitHub Actions CI for pytest" の本文・条件を作成。**【人間】** がGitHubに起票（06-21）。
- **【Codex】** `84eef36 Add Github Actions CI for pytest` / `45b20ba Add CI badge`。
- **【人間】** `PR #16` マージ（2026-06-22 23:29）。

### テスト健全化・リファクタ（Issue #3〜#9 / PR #17〜#24、2026-06-24）
- **#3 → PR#17** `test: verify reroll does not increment total`（リロールで総数が増えないことを検証）
- **#4 → PR#18** `refactor: split diagnosis responsibilities`（診断ロジックのモジュール分割）
- **#5 → PR#19(close)→#20(merge)** `test: make result randomness reproducible`（乱数のテスト可能化）
- **#6 → PR#21** `refactor: centralize diagnosis choices`（選択肢定義の集約）
- **#7 → PR#22** `refactor: split frontend script responsibilities`（フロントJSの責務分割）
- **#8 → PR#23** `docs: explain architecture and limitations`（アーキテクチャと制約の文書化）
- **#9 → PR#24** `ops: configure persistent SQLite storage` + DBポリシー文書化
- いずれも **Issue本文は【ChatGPT】**、**コードは【Codex】**、**完了条件チェックは【ChatGPT】**、**【人間】** がGitHub起票・PRマージ・`1ccabe6 docs: add repository workflow agreement`（ワークフロー合意）の指示。

### フィードバック反映（Issue #10〜#15・#33〜#35 / PR #25〜#47、2026-06-24〜06-25）
- **#10 → PR#25** モバイルで About リンクを表示
- **#11 → PR#26** About ページに作者リンク追加
- **#12 → PR#27** シスターのコメント表示時間を延長
- **#13 → PR#28** 統計の時間帯バケットを日本時間に
- **#14 → PR#29/#30/#31** トップにコンセプトコピー追加・拡大・大画面調整（3回の反復）
- **#15 → PR#32** 判定スタンプを画像アセット化
- **#33 → PR#45** 文言を「審判トーン」から「懺悔と赦しトーン」へ刷新（`2d526b6` ほか、リアクション秒数を何度も微調整 `145aaa3`〜`1073192`）
- **#34 → PR#46** 結果送信へ軽量レート制限を追加
- **#35 → PR#47** SQLite バックアップ／リストア検証ツール追加（`16c77e5`）
- **Issue本文は【ChatGPT】**、**コードは【Codex】**、**完了条件チェックは【ChatGPT】**、**【人間】** がGitHub起票・優先順位付け・PRマージ・ブラウザ動作確認。

### 画面の微調整指示（人間が手書き）
- **（推測）【人間】** `docs/archive/additionalmodify.md` は、**人間がAIへ出した画面・文言の微調整指示メモ**と見られる。「通常結果時のスタンプの位置が下になってしまっている。シスターの斜め右上に来るよう修正」のような口語の命令形で、表示順や結果ラベルの対応（"完全なる赦し"／"ささやかな懺悔" など）を具体的に指定している。**赦しの文言の最終決定が人間であること**を裏づける資料でもある。
- **（推測）【人間】** `feedback.md` の下部の細かな修正指示や、リアクション秒数を何度も詰めたコミット群（`145aaa3`〜`1073192`）も、こうした人間の微調整指示が起点（推測）。

### このフェーズで人間が下した「撤回・再設計」判断（コードは書かないが方針を決めた部分）
- **「次へ」ボタンの廃止**: リアクション後に押す案を実際に操作すると冗長 → 選択→リアクション→自動遷移に変更。
- **Cookieによる「今日は寝ろ」を撤回**: 別の回答でも睡眠判定が残り因果が不明瞭 → 特定回答の完全一致条件に変更。
- **隠し結果の分離**: 「このアプリについて」の隠し導線を「今日は寝ろ」から「ラーメンばんざい！」に変更。
- **X共有の自動化をやめた**: Web Intentの画像自動添付の制約・端末差が大きい → 「画像保存」と「X投稿」を別ボタンに。
- これらは「**実装できること**」と「**採用すべきこと**」を人間が分けた例（実装そのものはCodexが行った）。

---

## フェーズ 3 — 残りIssueの一括実装・QA（Claude Code）｜2026-06-30

ここから開発支援AIが **Claude Code** に交代。**ブランチ作成・PR作成・テスト実行・エラー自己修正までAIが実行**するようになり、人間は方針決定・承認・ブラウザ実機確認を担当（`docs/ai_collaboration_learnings.md` 第5章の比較表）。

- **【ChatGPT】** 残課題 Issue **#36, #38, #39, #40, #41, #42, #43, #44**（運用・品質・セキュリティ系）の本文・受け入れ条件を作成。**【人間】** が06-24にGitHubへ起票。
- **【人間】** これら8件のIssueの一括着手を Claude Code に指示。
- **【Claude Code】** 1ブランチで8件をコード実装（`3056631 feat: implement all remaining issues`）。
  - #36 Playwright E2E を CI に追加
  - #38 統計書き込みのエラーハンドリング（`/result`・`/hidden-judgment` が落ちないように）
  - #39 Dependabot と依存レビューワークフロー
  - #40 主要ページのアクセシビリティ・スモークチェック
  - #41 リリースチェックリストのカバレッジ文書化
  - #42 依存・アセットのライセンスチェック
  - #43 リリース運用・監視チェックリスト
  - #44 セキュリティヘッダーと基本CSPの追加
- **【Claude Code】** **7ペルソナQAテスト 39件**を実装（`6621d79`）。コードレビューとは別に「壊しにいく視点」を明文化。
  - P1 Newbie / P2 Veteran / P3 Malicious / P4 Data Integrity / P5 Migration / P6 Regression / P7 Spec Skeptic
- **【Claude Code】** Playwright設定・E2Eセレクタを実HTML構造に合わせて修正（`bdf2ec3`）、CIで venv 作成（`7475e35`）、`.gitignore` 整備（`8365fc9`）。
- **テスト結果（PR #49 本文）**: pytest **100 passed**（既存61＋新規39）、Playwright E2E **11 passed**。
- **【ChatGPT】** 各Issue（#36〜#44）の「確認」条件を満たしているか照合チェック。
- **【人間】** `PR #48` を一度クローズ → **`PR #49` を改めてマージ**（2026-06-30 14:14）。**push前に pytest + E2E + 7ペルソナ + ブラウザ実動作 + スマホサイズ確認を要求**するのが人間側の合意ルール（`AGENTS.md`）。
- **【自動】** Dependabot が依存更新 PR **#50〜#56** を自動生成（actions/checkout, setup-node, uvicorn, python-multipart, psycopg, anyio, pytest）。2026-06-30時点で未マージ。

---

## フェーズ 4 — セキュリティ／品質レビュー（Claude Code・2段階フロー）｜2026-06-30

**「調査と修正を分ける」**という人間の明示指示に基づく2段階フロー。

### Phase 1: 調査のみ（承認待ち）
- **【人間】** 「Phase 1（調査のみ・`findings.md`作成・承認待ち）→ Phase 2（承認済みのみ修正）」を指示。
- **【Claude Code】** コードを調査し、指摘 **F001〜F010** を `findings.md` に一覧化。**修正はせず承認欄付きで提示**して停止。
- **【人間】** `findings.md` を確認し、修正対象を承認。

### Phase 2: 承認済みのみ修正（`PR #57`、`7aeb8dd`）
- **【Claude Code】** 承認された全10件をコード修正:

  | ID | 深刻度 | 対応内容 |
  |----|--------|----------|
  | F001 | MEDIUM | Cookieレート制限を HMAC-SHA256 署名で改ざん防止（`RATE_LIMIT_SECRET`で鍵管理） |
  | F002 | LOW | `.dockerignore` 追加（ローカルDBのイメージ混入防止） |
  | F003 | LOW | `Strict-Transport-Security` ヘッダー追加 |
  | F004 | LOW | CSPから `unsafe-inline` 削除、`stats.html` のインラインstyleを `data-width`属性＋`stats_bars.js` に置換 |
  | F005 | LOW | `start.sh` から `--reload` フラグ削除 |
  | F006 | INFO | `_date_context` を `diagnosis.__all__` から除去し直接 import |
  | F007 | INFO | `database_url()` をモジュールレベルでキャッシュ |
  | F008 | INFO | `/health` の `datetime.now()` を UTC に統一 |
  | F009 | INFO | `generate_result_text` の `result_type` を必須引数化 |
  | F010 | INFO | double-submit cookie パターンでCSRF保護を追加（`app/csrf.py`） |

- **テスト結果（PR #57 本文）**: pytest **101 passed**、7ペルソナQA **39 passed**、Playwright E2E **22 passed**（Chromium + Pixel 5 mobile）。
- **【Claude Code】** iPhone 14 (WebKit) のモバイルE2Eプロジェクトを復元（`c4832bc`、WebKit実行には追加ライブラリが必要との注記）。
- **【人間】** `PR #57` をマージ（2026-06-30 14:52）。
- 関連 Issue #36〜#44 を 2026-06-30 05:56 にまとめてクローズ。

---

## フェーズ 5 — ドキュメント整備（Claude Code）｜2026-06-30

- **【Claude Code】** About ページのリンク調整（コードは AI）:
  - `d877a5d`/`34c332a chore: remove GitHub repository link from about page`
  - `7e943f0 chore: add X (Twitter) link to about page creator section`
- **【Claude Code】** 振り返りドキュメントを執筆:
  - `294bfc1 docs: add AI collaboration learnings document`（`docs/ai_collaboration_learnings.md`）
  - `fd39a25 docs: add honest reflections on AI-assisted development`
- **【人間】** 「AIのコードをAIにチェックさせる問題」「Pythonを自分で読めるようにする必要」など、率直な反省点の論点を提示し、ドキュメントに反映させた（文章執筆はAI）。
- **【Claude Code】** 本資料（`docs/development_process_human_vs_ai.md`）を、上記の全履歴を突き合わせて執筆。

---

## まとめ — 役割の境界

### コードを書いたのは100%AI
- **ChatGPT**: アイデアの言語化・複数案の生成・比較材料の提示に加え、**全Issueの本文と受け入れ条件の作成、各Issueの完了条件チェック**を担当（コード生成は主目的でない）。
- **Codex**: 既存コードを前提とした実装変更、テスト更新、ドキュメント生成（Ver0.1〜Ver1.0）。コンテキストは人間が手動で渡し、git/PR/テスト実行も人間が行った。
- **Claude Code**: リポジトリ直接参照、ブランチ/PR管理、E2E・7ペルソナQA、セキュリティ調査と修正、エラー自己修正。多ステップを計画して実行。

### 人間が手放さなかった範囲（コードもIssue本文も書いていない）
- 何を作るか（企画・体験コンセプト）
- **アプリの世界観と赦しの文言**（核となる設定と「赦しの言葉」を人間が決定）
- **どうすれば面白くなるかの方向づけ**（おもしろさの判断・演出の方針）
- **仕様の最終決定**（どの案を採用・撤回するか：Cookie判定撤回、共有の単純化、隠し結果の再設計など）
- **画面の微調整指示**（コピーの大きさ・配置・リアクション秒数・余白など、AIに具体的に出した指示）
- **個人情報をどこまで取るかの決定**（ログイン・位置情報・個人識別を保存しないプライバシー方針）
- **友人フィードバックをAIと壁打ちしつつ最終的に判断**（収集・分類・優先順位付け → 採否決定）
- MVPをいつ公開するか、誰に試してもらうか（友人、最終的に11人）
- どこで止めるか（セキュリティレビューの承認・却下）
- push前の品質ゲート（テスト・ブラウザ・スマホ実機確認）の要求
- Git/GitHub 操作（Issue起票・commit/push/PRマージ。ただしコードもIssue本文も執筆していない）

> **人間が「自分の手で書いたテキスト」はごく一部。** 例外は **`feedback.md` の上部（指針）** で、ここは人間が手書きした。それ以外——コードはCodex/Claude Code、Issue本文と受け入れ条件はChatGPT、振り返りドキュメントはClaude Codeが執筆した。人間の寄与は **判断・選択・方向づけ・操作・実機確認** に集約される。

### 開発スタイルの特徴
**「MVPを早く公開 → 実ユーザーのフィードバック → 一気に拡張」** という流れは、AIによって実装コストが下がったからこそ現実的になった選択（評価は推測を含むが、`docs/ai_collaboration_learnings.md` 6.6 と整合）。一方で「実装できるから入れる」とスコープが膨らむリスクは人間が抑える必要がある、というのが本プロジェクトの主要な学びである。

> **正直な留保（`docs/ai_collaboration_learnings.md` 6.7 より）**: コードの生成もレビューも修正もAIが行ったため、「人間は何をしているのか」という問いは残る。ただし *何を作るか・何を優先するか・どこで止めるか・どんな体験にするか* は人間が判断した。次の課題として、AIの出力を自分で評価できるよう **人間側がPython（型ヒント・非同期・ミドルウェア・`hmac`/`secrets`等）を読めるようになること** が挙げられている。

---

## 付録：ドキュメント別 推定執筆者（文体からの推測を含む）

リポジトリ内の各ドキュメントを、文体・体裁・内容から「だれが書いたか」を推定した一覧。**確証がない判定は（推測）**。

| ドキュメント | 推定執筆者 | 判定根拠 |
|--------------|-----------|----------|
| `feedback.md`（上部の「指針」） | **人間（確定）** | 本人の証言。口語・箇条書きメモ |
| `feedback.md`（下部の細部指示） | 人間（推測） | 口語の修正指示が続く文体 |
| `docs/archive/initial_spec.md` | 人間（推測） | Markdown見出しなしの素メモ、砕けた自己フレーミング |
| `docs/archive/additionalmodify.md` | 人間（推測） | 口語の命令形によるAIへの微調整指示 |
| `docs/archive/reason_candidates.md`（366日分の日付理由） | ChatGPT（推測） | 大量かつ機知に富む一行ジョーク。人間が選別・敬体統一した可能性 |
| `docs/archive/ver1_order_notes.md` | AI＝Codex/ChatGPT（推測） | 整った見出し・「〜する。」の仕様記述体 |
| `docs/spec_evolution_v0.1_to_v1.0.md` | Codex（推測） | 構造化された設計変更資料。`docs/ai_development_retrospective.md` と同系統 |
| `docs/ai_development_retrospective.md` | Codex（推測） | 末尾に「Codexから見た総合評価」あり |
| `docs/ai_collaboration_learnings.md` | Claude Code | コミット `294bfc1`、内容が06-30作業 |
| `docs/release_checklist.md` / `operation_runbook.md` / `database_policy.md` / `license_check.md` | Claude Code/Codex（推測） | Issue実装に伴う運用文書 |
| `AGENTS.md` | 人間＋AI（推測） | ワークフロー合意。人間の方針をAIが文章化した可能性 |
| `README.md` | Codex/Claude Code（推測） | 整った製品説明文 |
| `findings.md` | Claude Code | セキュリティレビュー（フェーズ4）の成果物 |
| 本資料 `development_process_human_vs_ai.md` | Claude Code | 人間の指示・訂正を受けて執筆 |

> ポイント: **人間が「自分の言葉で手書きした」と推定できるのは `feedback.md` 上部・`initial_spec.md`・`additionalmodify.md` の3点**。いずれも「仕様の方向づけ」と「画面・文言の微調整指示」であり、*決める・方向づける* という人間の役割と一致する。

---

## 参照
- `docs/ai_development_retrospective.md` — Codex時代の詳細な振り返り
- `docs/ai_collaboration_learnings.md` — ChatGPT→Codex→Claude Code の学び
- `docs/spec_evolution_v0.1_to_v1.0.md` — Ver0.1→Ver1.0 の仕様変化記録
- `feedback.md` — 友人（最終的に11人）からのフィードバック原本
- `findings.md` — セキュリティレビュー指摘（F001〜F010）
- `AGENTS.md` — Issue作業フロー・push前チェックリスト
