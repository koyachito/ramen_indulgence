1. .mount, .get, .postはosモジュールのメソッド？
	- 違う。app = FastAPI(title="ramen", lifespan=lifespan)で作られたappインスタンス
	- そのappに足して.mount(), .get(), .post()を呼ぶ
	- >　は？これは標準関数なの？
2. appにルートが登録とはどういう意味か
	- Pythonファイルを読み込んだ段階で、FastAPIがURLと処理関数の対応表を作ること
```
GET  /           -> index
GET  /diagnosis  -> diagnosis_form
POST /result     -> result
GET  /result     -> result_get_redirect
GET  /about      -> about
GET  /stats      -> stats
GET  /health     -> health
```

3. ASGIサーバーとは？Uvicornとは？
	- ASGIはPythonのWebサーバーとWebアプリをつなぐための規格
	- Asynchronous Server Gateway Interface:
	- async/awaitによる非同期処理、WebSocketなどの双方向リアルタイム通信を標準サポート
	- UvicornはASGI規格に対応したサーバー
```
uvicorn app.main:app --reload
```
	- 「app/main.pyの中にあるappというFastAPIインスタンスをuvicornで起動する」

4. はじめに処理されるのがapp = FastAPI(...　ということ？
	- import -> 定数PUBLIC_APP_URL作成 -> 関数定義 -> app=FastAPI -> app.mount ...
	- 本体が作られる最初の大きな行はapp = FastAPIであってる

5. サイト管理者にアプリ終了時にその時点のDBを渡したいなあ
	- SQLite、Renderの無料インスタンスだと終了処理が確実に完了しない可能性もある
	- /statsで統計見るとか、
6. StaticFilesとStarletteの解説
7. 32行目以下はJinja2Templatesを使用してhtmlを作成してる？
8. get_stats()["Total"]が未定義なのに動くのはなぜか
9. 「GET / にアクセスが来たら」の意味は？GETってなに？SQL？
10. HTMLレスポンスって何？そもそもHTMLってマークアップ言語ってだけじゃないの？
11. クエリパラメータとは？application/x-www-form-urlencoded または multipart/form-dataとは？JSONとは？フォームフィールドとは？
12. try:
    selected_date = date(2000, current_month, current_day)
except ValueError:
    today = date.today()
    selected_date = date(2000, today.month, today.day)の意味がわからん。文法解説して
13. result{~}: valid_values={~}で制限できるってのはなんで？他のところでそういうふうに定義してる？それとも標準ライブラリでvalid_valuesがある？このコロン何？
14. value not in ~ と書いたとき、このvalueって予約語？辞書内の各値って意味になるの？
15.   if any(value not in valid_values[name] for name, value in submitted.items()): の文法解説して
16. HTMLを返すとは？status_code=303したらGETで...って、GETってなに？モード？
17. @dataclass便利だねー。__init__とself.属性を書かなくていいのか
18. def diagnose(data: DiagnosisInput) -> DiagnosisResult:の->の機能がわからん
19. /resultのhourとかmealがge/leの範囲内になかったらどうなるの？
20. get_stats()の機能がよくわからなかった
21. HTTPとHTMLの違い、解説
22. valid_valuesはたしかにそうかも。diagnosis.pyの辞書をここで読んで、それと一致してるか見せたほうがいいね
23. Pydantic modelとLiteralってなんですか？たしかに不正入力はそもそも許さない設計にしたほうが安全ではある。valid_valuesとsubmittedいちいち追加しないといけないのは冗長だしな。
24. _connect()ってどこにあるの？
