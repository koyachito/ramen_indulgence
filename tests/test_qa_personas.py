"""
7ペルソナQAテスト
P1 新人    : 説明読まず直感操作・空送信・連打
P2 ベテラン : キーボード高速・境界値入力
P3 悪意    : 不正値・権限外・二重送信・インジェクション
P4 データ整合: 画面でなくDBを直接確認
P5 移行    : 旧スキーマ・欠損・異形式
P6 回帰    : 周辺機能が壊れていないか
P7 仕様懐疑 : 実装でなく仕様書と突合
"""
import asyncio
import logging
import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

os.environ["RAMEN_DB_PATH"] = "/tmp/ramen-qa-test.db"

import httpx
import pytest

from app.database import init_db, get_stats
from app.main import app
from app.security_headers import SECURITY_HEADERS, CSP

VALID_DATA = {
    "current_hour": "20",
    "current_month": "6",
    "current_day": "22",
    "meals": "1",
    "ramen_count_today": "0",
    "achievement": "worked",
    "mood": "tired",
    "after_plan": "work_more",
    "reason_not_to_eat": "none",
    "ramen_type": "miso",
    "forgiveness_style": "praise",
}


async def req(method, path, **kwargs):
    init_db()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        return await c.request(method, path, **kwargs)


# ─────────────────────────────────────────────
# P1 新人：説明読まず直感操作・空送信・連打
# ─────────────────────────────────────────────

def test_p1_get_result_redirects_to_top():
    """GETで/resultを直接叩いたらトップへ飛ぶ"""
    r = asyncio.run(req("GET", "/result"))
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_p1_empty_post_to_result_returns_422():
    """何も入力せずPOSTしたら422（FastAPI検証）"""
    r = asyncio.run(req("POST", "/result", data={}))
    assert r.status_code == 422


def test_p1_missing_required_fields_returns_422():
    """必須フィールドが欠けていたら422"""
    partial = {"current_hour": "12", "meals": "1"}
    r = asyncio.run(req("POST", "/result", data=partial))
    assert r.status_code == 422


def test_p1_rapid_reroll_does_not_inflate_stats():
    """連続でreroll=trueを10回送っても統計が増えない"""
    async def scenario():
        init_db()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
            # 1回目で記録
            await c.post("/result", data=VALID_DATA)
            before = get_stats()["total"]
            for _ in range(10):
                await c.post("/result", data={**VALID_DATA, "reroll": "true"})
            after = get_stats()["total"]
            return before, after
    before, after = asyncio.run(scenario())
    assert before == after, f"reroll10回でtotalが{after - before}増えた"


# ─────────────────────────────────────────────
# P2 ベテラン：境界値・大量入力
# ─────────────────────────────────────────────

def test_p2_boundary_hour_0_and_23_are_valid():
    for hour in ["0", "23"]:
        r = asyncio.run(req("POST", "/result", data={**VALID_DATA, "current_hour": hour}))
        assert r.status_code == 200, f"hour={hour} should be 200"


def test_p2_boundary_hour_out_of_range_rejected():
    for hour in ["-1", "24", "99"]:
        r = asyncio.run(req("POST", "/result", data={**VALID_DATA, "current_hour": hour}))
        assert r.status_code == 422, f"hour={hour} should be 422, got {r.status_code}"


def test_p2_boundary_meals_0_and_4_are_valid():
    for meals in ["0", "4"]:
        r = asyncio.run(req("POST", "/result", data={**VALID_DATA, "meals": meals}))
        assert r.status_code == 200, f"meals={meals} should be 200"


def test_p2_boundary_meals_out_of_range_rejected():
    for meals in ["-1", "5", "100"]:
        r = asyncio.run(req("POST", "/result", data={**VALID_DATA, "meals": meals}))
        assert r.status_code == 422, f"meals={meals} should be 422, got {r.status_code}"


def test_p2_boundary_month_and_day():
    valid = [("1", "1"), ("12", "31")]
    invalid = [("0", "1"), ("13", "1"), ("1", "0"), ("1", "32")]
    for month, day in valid:
        r = asyncio.run(req("POST", "/result", data={**VALID_DATA, "current_month": month, "current_day": day}))
        assert r.status_code == 200
    for month, day in invalid:
        r = asyncio.run(req("POST", "/result", data={**VALID_DATA, "current_month": month, "current_day": day}))
        assert r.status_code == 422, f"month={month},day={day} should be 422"


def test_p2_stats_hour_filter_boundary():
    for hour in ["0", "23"]:
        r = asyncio.run(req("GET", f"/stats?hour={hour}"))
        assert r.status_code == 200
    for hour in ["-1", "24"]:
        r = asyncio.run(req("GET", f"/stats?hour={hour}"))
        assert r.status_code == 422


# ─────────────────────────────────────────────
# P3 悪意：不正値・インジェクション・権限外
# ─────────────────────────────────────────────

def test_p3_invalid_choice_value_redirects_to_diagnosis():
    """定義外のchoice値はDiagnosisにリダイレクト（ユーザー画面は出ない）"""
    for field in ["achievement", "mood", "after_plan", "reason_not_to_eat", "ramen_type", "forgiveness_style"]:
        r = asyncio.run(req("POST", "/result", data={**VALID_DATA, field: "INJECT_VALUE"}))
        assert r.status_code == 303, f"{field}=INJECT_VALUE should be 303"
        assert r.headers["location"] == "/diagnosis"


def test_p3_sql_injection_in_choice_field_does_not_error():
    """SQLインジェクション文字列はchoice検証でリダイレクトされ500にならない"""
    payload = "'; DROP TABLE diagnosis_logs; --"
    r = asyncio.run(req("POST", "/result", data={**VALID_DATA, "mood": payload}))
    assert r.status_code == 303
    # DBが壊れていないか確認
    init_db()
    stats = get_stats()
    assert "total" in stats


def test_p3_html_injection_in_choice_field_does_not_render():
    """<script>タグはchoice検証でブロックされ画面に出ない"""
    payload = '<script>alert(1)</script>'
    r = asyncio.run(req("POST", "/result", data={**VALID_DATA, "ramen_type": payload}))
    assert r.status_code == 303
    assert "<script>alert" not in r.text


def test_p3_non_integer_meals_rejected():
    """mealsに文字列を入れたら422"""
    r = asyncio.run(req("POST", "/result", data={**VALID_DATA, "meals": "abc"}))
    assert r.status_code == 422


def test_p3_hidden_judgment_get_not_allowed():
    """/hidden-judgmentはGETで到達できない（405）"""
    r = asyncio.run(req("GET", "/hidden-judgment"))
    assert r.status_code == 405


def test_p3_exception_detail_not_in_response_body():
    """DB失敗時のexception詳細がユーザー画面に出ないこと"""
    with patch("app.main.record_result", side_effect=Exception("SUPER_SECRET_DB_ERROR")):
        r = asyncio.run(req("POST", "/result", data=VALID_DATA))
    assert r.status_code == 200
    assert "SUPER_SECRET_DB_ERROR" not in r.text
    assert "Traceback" not in r.text
    assert "Exception" not in r.text


# ─────────────────────────────────────────────
# P4 データ整合：画面ではなくDBを直接確認
# ─────────────────────────────────────────────

def _db_row_count(table: str) -> int:
    db = Path(os.environ["RAMEN_DB_PATH"])
    with closing(sqlite3.connect(db)) as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_p4_valid_post_increments_db_row():
    """有効なPOSTでdiagnosis_logsが実際に1行増える"""
    init_db()
    before = _db_row_count("diagnosis_logs")
    asyncio.run(req("POST", "/result", data=VALID_DATA))
    after = _db_row_count("diagnosis_logs")
    assert after == before + 1, f"DB行数が増えていない: {before} → {after}"


def test_p4_reroll_does_not_increment_db_row():
    """reroll=trueはDBに書き込まれない"""
    init_db()
    before = _db_row_count("diagnosis_logs")
    asyncio.run(req("POST", "/result", data={**VALID_DATA, "reroll": "true"}))
    after = _db_row_count("diagnosis_logs")
    assert after == before, "rerollでDBが増えた"


def test_p4_rate_limit_does_not_increment_db():
    """同一クライアントの連続POSTは2回目以降DBに書かれない"""
    async def scenario():
        init_db()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
            await c.post("/result", data=VALID_DATA)
            before = _db_row_count("diagnosis_logs")
            await c.post("/result", data=VALID_DATA)
            after = _db_row_count("diagnosis_logs")
            return before, after
    before, after = asyncio.run(scenario())
    assert before == after, f"レート制限内でDBが{after - before}行増えた"


def test_p4_db_failure_leaves_db_unchanged():
    """record_result失敗時にDBは変化しない"""
    init_db()
    before = _db_row_count("diagnosis_logs")
    with patch("app.main.record_result", side_effect=Exception("disk full")):
        asyncio.run(req("POST", "/result", data=VALID_DATA))
    after = _db_row_count("diagnosis_logs")
    assert before == after, "DB失敗なのに行が増えた"


def test_p4_get_stats_total_matches_db_count():
    """get_stats()のtotalはDB両テーブルの合計と一致する"""
    init_db()
    db = Path(os.environ["RAMEN_DB_PATH"])
    with closing(sqlite3.connect(db)) as conn:
        logs = conn.execute("SELECT COUNT(*) FROM diagnosis_logs").fetchone()[0]
        judgments = conn.execute("SELECT COUNT(*) FROM standalone_judgments").fetchone()[0]
    stats = get_stats()
    assert stats["total"] == logs + judgments, (
        f"stats.total={stats['total']} ≠ DB合計={logs + judgments}"
    )


# ─────────────────────────────────────────────
# P5 移行：旧スキーマ・欠損カラム・文字コード
# ─────────────────────────────────────────────

def test_p5_old_schema_missing_column_handled_gracefully():
    """DBに旧スキーマ（oni_flagカラム欠落）があってもユーザー画面は返る"""
    old_db = "/tmp/ramen-qa-old-schema.db"
    os.environ["RAMEN_DB_PATH"] = old_db
    try:
        # 旧スキーマでテーブル作成（oni_flag欠落）
        with closing(sqlite3.connect(old_db)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS diagnosis_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    current_hour INTEGER NOT NULL,
                    time_bucket TEXT NOT NULL,
                    ramen_type TEXT NOT NULL,
                    meals INTEGER NOT NULL,
                    ramen_count_today INTEGER NOT NULL,
                    achievement TEXT NOT NULL,
                    mood TEXT NOT NULL,
                    reason_not_to_eat TEXT NOT NULL,
                    forgiveness_style TEXT NOT NULL,
                    after_plan TEXT NOT NULL,
                    merit_score INTEGER NOT NULL,
                    danger_score INTEGER NOT NULL,
                    confession_score INTEGER NOT NULL,
                    result_type TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS standalone_judgments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    result_type TEXT NOT NULL
                )
            """)
            conn.commit()

        # init_dbは既存テーブルを変更しない
        r = asyncio.run(req("POST", "/result", data=VALID_DATA))
        # DB書き込みは失敗するが（oni_flagカラムなし）、画面は返るはず
        assert r.status_code == 200, f"旧スキーマ時に画面が返らない: {r.status_code}"
        assert "ラーメン" in r.text
    finally:
        os.environ["RAMEN_DB_PATH"] = "/tmp/ramen-qa-test.db"
        if Path(old_db).exists():
            Path(old_db).unlink()


def test_p5_unicode_ramen_type_in_db_does_not_break_stats():
    """DBに日本語・絵文字が入っていてもget_statsは壊れない"""
    init_db()
    db = Path(os.environ["RAMEN_DB_PATH"])
    with closing(sqlite3.connect(db)) as conn:
        conn.execute(
            "INSERT INTO standalone_judgments (created_at, result_type) VALUES (?, ?)",
            ("2024-01-01T00:00:00", "🍜赦し絵文字テスト"),
        )
        conn.commit()
    stats = get_stats()
    assert stats["total"] >= 1


def test_p5_init_db_is_idempotent():
    """init_dbを複数回呼んでもエラーにならずテーブルが重複しない"""
    for _ in range(3):
        init_db()
    stats = get_stats()
    assert "total" in stats


# ─────────────────────────────────────────────
# P6 回帰：周辺機能が壊れていないか
# ─────────────────────────────────────────────

def test_p6_static_files_still_accessible():
    """静的ファイルが引き続き取得できる"""
    r = asyncio.run(req("GET", "/static/style.css"))
    assert r.status_code == 200
    assert "text/css" in r.headers.get("content-type", "")


def test_p6_embedded_json_script_in_diagnosis_not_broken():
    """<script type="application/json">がCSPで壊れていないこと（HTMLに存在する）"""
    r = asyncio.run(req("GET", "/diagnosis"))
    assert r.status_code == 200
    assert '<script id="diagnosis-question-config" type="application/json">' in r.text


def test_p6_stats_page_still_works_with_hour_filter():
    """統計ページの時間帯フィルターが引き続き動く"""
    for hour in range(0, 24, 6):
        r = asyncio.run(req("GET", f"/stats?hour={hour}"))
        assert r.status_code == 200


def test_p6_health_endpoint_still_returns_ok():
    r = asyncio.run(req("GET", "/health"))
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_p6_hidden_confession_still_accessible():
    r = asyncio.run(req("GET", "/hidden-confession"))
    assert r.status_code == 200
    assert "data-auto-submit" in r.text


def test_p6_result_page_has_all_share_actions():
    """結果画面の共有導線が壊れていない"""
    r = asyncio.run(req("POST", "/result", data=VALID_DATA))
    assert "近くのラーメンを探す" in r.text
    assert "赦しの画像を保存" in r.text
    assert "赦しの結果をツイート" in r.text


def test_p6_security_headers_not_breaking_about_page():
    r = asyncio.run(req("GET", "/about"))
    assert r.status_code == 200
    assert "koyachito" in r.text
    # ヘッダーが付いていることも確認
    assert "x-frame-options" in r.headers


# ─────────────────────────────────────────────
# P7 仕様懐疑：実装でなく仕様と突合
# ─────────────────────────────────────────────

def test_p7_csp_has_all_required_directives_per_spec():
    """issue#44 仕様書に列挙されたCSPディレクティブが全部あるか"""
    required = [
        "default-src 'self'",
        "script-src 'self'",
        "img-src 'self' data:",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "frame-ancestors 'none'",
        "form-action 'self'",
    ]
    for directive in required:
        assert directive in CSP, f"CSPにディレクティブがない: {directive}"


def test_p7_all_specified_endpoints_have_security_headers():
    """issue#44 仕様に書かれた全エンドポイントにヘッダーが付く"""
    endpoints = ["/", "/diagnosis", "/stats", "/about", "/health"]
    post_endpoints = [("/result", VALID_DATA)]

    for path in endpoints:
        r = asyncio.run(req("GET", path))
        for header in SECURITY_HEADERS:
            assert header.lower() in r.headers, f"{path} に {header} がない"

    for path, data in post_endpoints:
        r = asyncio.run(req("POST", path, data=data))
        for header in SECURITY_HEADERS:
            assert header.lower() in r.headers, f"POST {path} に {header} がない"


def test_p7_record_result_failure_is_logged(caplog):
    """issue#38 仕様: 失敗時はログに残る"""
    with caplog.at_level(logging.ERROR, logger="app.main"):
        with patch("app.main.record_result", side_effect=Exception("test-log-check")):
            asyncio.run(req("POST", "/result", data=VALID_DATA))
    assert any("record_result failed" in m for m in caplog.messages), (
        "record_result失敗がログに出ていない"
    )


def test_p7_get_stats_failure_is_logged(caplog):
    """issue#38 仕様: get_stats失敗もログに残る"""
    with caplog.at_level(logging.ERROR, logger="app.main"):
        with patch("app.main.get_stats", side_effect=Exception("stats-log-check")):
            asyncio.run(req("POST", "/result", data=VALID_DATA))
    assert any("get_stats failed" in m for m in caplog.messages)


def test_p7_record_judgment_failure_is_logged(caplog):
    """issue#38 仕様: record_judgment失敗もログに残る"""
    with caplog.at_level(logging.ERROR, logger="app.main"):
        with patch("app.main.record_judgment", side_effect=Exception("judgment-log-check")):
            asyncio.run(req("POST", "/hidden-judgment"))
    assert any("record_judgment failed" in m for m in caplog.messages)


def test_p7_x_frame_options_is_deny_not_sameorigin():
    """issue#44 仕様: X-Frame-Options は DENY（SAMEORIGINではない）"""
    r = asyncio.run(req("GET", "/"))
    assert r.headers.get("x-frame-options") == "DENY"


def test_p7_permissions_policy_disables_specified_apis():
    """issue#44 仕様: Permissions-Policy で geolocation,camera,microphone が無効"""
    r = asyncio.run(req("GET", "/"))
    pp = r.headers.get("permissions-policy", "")
    assert "geolocation=()" in pp
    assert "camera=()" in pp
    assert "microphone=()" in pp


def test_p7_result_stats_total_shown_even_when_zero():
    """issue#38 仕様: get_stats失敗時は total=0 のフォールバック表示"""
    with patch("app.main.get_stats", side_effect=Exception("db down")):
        r = asyncio.run(req("POST", "/result", data=VALID_DATA))
    assert r.status_code == 200
    # 0件でも画面は返る（件数表示部分でクラッシュしない）
    assert "ラーメン" in r.text
